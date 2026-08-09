import asyncio
import dataclasses
import logging
from contextlib import suppress
from typing import Callable, Optional, Type

import aiohttp

from plugp100.common.credentials import AuthCredential
from plugp100.protocol.klap.klap_protocol import KlapProtocol
from plugp100.protocol.passthrough_protocol import PassthroughProtocol
from plugp100.protocol.tpap_protocol import TpapProtocol
from plugp100.responses.tapo_exception import (
    TapoAuthenticationError,
    TapoError,
    TapoException,
)
from .errors.invalid_authentication import InvalidAuthentication
from .errors.protocol_guess import (
    HostUnreachableError,
    ProtocolDetectionTimeoutError,
    ProtocolFailure,
    UnsupportedProtocolError,
)
from .tapobulb import TapoBulb
from .tapodevice import TapoDevice
from .tapohub import TapoHub
from .tapoplug import TapoPlug
from ..api.requests.tapo_request import TapoRequest
from ..api.tapo_client import TapoClient
from ..protocol.klap import klap_handshake_v1, klap_handshake_v2
from ..protocol.tapo_protocol import TapoProtocol
from ..responses.device_state import DeviceInfo

_LOGGER = logging.getLogger("DeviceFactory")


@dataclasses.dataclass
class DeviceConnectConfiguration:
    host: str
    port: int = 80
    credentials: Optional[AuthCredential] = None
    device_type: Optional[str] = None
    device_model: Optional[str] = None
    encryption_type: Optional[str] = None
    encryption_version: Optional[int] = None
    is_support_https: bool = False
    timeout: Optional[float] = 5.0
    guess_timeout: Optional[float] = 15.0

    @property
    def url(self) -> str:
        scheme = "https" if self.is_support_https else "http"
        return f"{scheme}://{self.host}:{self.port}/app"


async def connect(
    config: DeviceConnectConfiguration, session: Optional[aiohttp.ClientSession] = None
):
    if config.device_type is None:
        protocol = await _get_or_guess_protocol(config, session)
        _LOGGER.debug(
            "Not enough information to detected device type and model, trying to fetching from device..."
        )
        device_info = DeviceInfo(
            **(await protocol.send_request(request=TapoRequest.get_device_info()))
            .get_or_raise()
            .result
        )
        factory = _get_device_class_from_model_type(device_info.type)
    else:
        factory = _get_device_class_from_model_type(config.device_type)
        protocol = await _get_or_guess_protocol(config, session)

    client = TapoClient(config.credentials, config.url, protocol, session)
    return factory(config.host, config.port, client)


async def _get_or_guess_protocol(
    config: DeviceConnectConfiguration, session: Optional[aiohttp.ClientSession] = None
) -> TapoProtocol:
    if config.encryption_type is None:
        return await _guess_protocol(config, session)
    elif config.encryption_type.lower() == "klap":
        handshake_version = (
            klap_handshake_v2() if config.encryption_version == 2 else klap_handshake_v1()
        )
        return KlapProtocol(
            auth_credential=config.credentials,
            url=config.url,
            klap_strategy=handshake_version,
            http_session=session,
        )
    elif config.encryption_type.lower() == "aes":
        return PassthroughProtocol(
            auth_credential=config.credentials, url=config.url, http_session=session
        )
    elif config.encryption_type.lower() == "tpap":
        return TpapProtocol(
            auth_credential=config.credentials, url=config.url, http_session=session
        )
    else:
        raise Exception("Failed to determine the right tapo protocol")


async def _guess_protocol(
    config: DeviceConnectConfiguration, session: Optional[aiohttp.ClientSession] = None
) -> TapoProtocol:
    failures: list[ProtocolFailure] = []
    guess = _try_protocol_candidates(config, session, failures)
    try:
        return (
            await asyncio.wait_for(guess, timeout=config.guess_timeout)
            if config.guess_timeout is not None
            else await guess
        )
    except asyncio.TimeoutError as exc:
        failures.append(("global timeout", exc))
        error = ProtocolDetectionTimeoutError(
            config.host, config.device_type, failures=failures
        )
        _LOGGER.error("Protocol detection exceeded its global timeout: %s", error)
        raise error from exc


async def _try_protocol_candidates(
    config: DeviceConnectConfiguration,
    session: Optional[aiohttp.ClientSession],
    failures: list[ProtocolFailure],
) -> TapoProtocol:
    device_info_request = TapoRequest.get_device_info()
    unavailable_endpoints: set[str] = set()
    for candidate in _build_protocol_candidates(config, session):
        if candidate.endpoint and candidate.endpoint in unavailable_endpoints:
            _LOGGER.debug(
                "Skipping protocol candidate %s because endpoint %s is unavailable",
                candidate.name,
                candidate.endpoint,
            )
            continue
        protocol = None
        success = False
        try:
            protocol = candidate.factory()
            request = protocol.send_request(device_info_request, retry=0)
            info = (
                await asyncio.wait_for(request, timeout=config.timeout)
                if config.timeout is not None
                else await request
            )
            if info.is_success():
                success = True
                _LOGGER.debug("Found working protocol %s", candidate.name)
                return protocol
            error = info.error()
            failures.append((candidate.name, error))
            if candidate.endpoint and _is_endpoint_unavailable(error):
                unavailable_endpoints.add(candidate.endpoint)
            _LOGGER.debug(
                "Protocol candidate %s failed: %s",
                candidate.name,
                error,
            )
        except Exception as ex:
            failures.append((candidate.name, ex))
            if candidate.endpoint and _is_endpoint_unavailable(ex):
                unavailable_endpoints.add(candidate.endpoint)
            _LOGGER.debug("Protocol candidate %s failed: %s", candidate.name, ex)
        finally:
            if protocol is not None and not success:
                with suppress(Exception):
                    await protocol.close()

    error = _protocol_guess_error(config, failures)
    _LOGGER.error("None of the available protocols worked: %s", error)
    raise error


_AUTHENTICATION_ERROR_CODES = {
    TapoError.ERR_AES_DECODE_FAIL.value,
    TapoError.INVALID_CREDENTIAL.value,
    TapoError.ERR_HAND_SHAKE_FAILED.value,
    TapoError.ERR_LOGIN_FAILED.value,
}


def _protocol_guess_error(
    config: DeviceConnectConfiguration, failures: list[ProtocolFailure]
) -> Exception:
    errors = [error for _, error in failures]

    if any(_is_authentication_error(error) for error in errors):
        return InvalidAuthentication(config.host, config.device_type, failures=failures)

    if errors and all(_is_timeout_error(error) for error in errors):
        return ProtocolDetectionTimeoutError(
            config.host, config.device_type, failures=failures
        )

    if errors and all(_is_network_error(error) for error in errors):
        return HostUnreachableError(config.host, config.device_type, failures=failures)

    return UnsupportedProtocolError(config.host, config.device_type, failures=failures)


def _is_authentication_error(error: Exception) -> bool:
    return isinstance(error, TapoAuthenticationError) or (
        isinstance(error, TapoException)
        and error.error_code in _AUTHENTICATION_ERROR_CODES
    )


def _is_timeout_error(error: Exception) -> bool:
    return isinstance(error, (TimeoutError, asyncio.TimeoutError))


def _is_network_error(error: Exception) -> bool:
    return _is_timeout_error(error) or isinstance(
        error, (aiohttp.ClientConnectionError, OSError)
    )


def _is_endpoint_unavailable(error: Exception) -> bool:
    return isinstance(error, (aiohttp.ClientConnectorError, ConnectionRefusedError))


@dataclasses.dataclass(frozen=True)
class _ProtocolCandidate:
    name: str
    factory: Callable[[], TapoProtocol]
    endpoint: str = ""


def _build_protocol_candidates(
    config: DeviceConnectConfiguration,
    session: Optional[aiohttp.ClientSession] = None,
) -> list[_ProtocolCandidate]:
    """Build lazy protocol candidates for direct connection without discovery."""
    http_config = dataclasses.replace(
        config,
        port=config.port if not config.is_support_https else 80,
        is_support_https=False,
    )
    https_config = dataclasses.replace(
        config,
        port=config.port if config.is_support_https else 443,
        is_support_https=True,
    )
    tpap_https_config = dataclasses.replace(
        config,
        port=config.port if config.is_support_https else TpapProtocol.DEFAULT_HTTPS_PORT,
        is_support_https=True,
    )

    def common_candidates(
        endpoint: DeviceConnectConfiguration, label: str
    ) -> list[_ProtocolCandidate]:
        return [
            _ProtocolCandidate(
                f"AES {label}",
                lambda endpoint=endpoint: PassthroughProtocol(
                    endpoint.credentials, endpoint.url, session
                ),
                endpoint.url,
            ),
            _ProtocolCandidate(
                f"KLAP v1 {label}",
                lambda endpoint=endpoint: KlapProtocol(
                    endpoint.credentials,
                    endpoint.url,
                    klap_handshake_v1(),
                    session,
                ),
                endpoint.url,
            ),
            _ProtocolCandidate(
                f"KLAP v2 {label}",
                lambda endpoint=endpoint: KlapProtocol(
                    endpoint.credentials,
                    endpoint.url,
                    klap_handshake_v2(),
                    session,
                ),
                endpoint.url,
            ),
        ]

    http_candidates = [
        _ProtocolCandidate(
            f"TPAP HTTP:{http_config.port}",
            lambda: TpapProtocol(http_config.credentials, http_config.url, session),
            http_config.url,
        )
    ] + common_candidates(http_config, f"HTTP:{http_config.port}")
    https_candidates = [
        _ProtocolCandidate(
            f"TPAP HTTPS:{tpap_https_config.port}",
            lambda: TpapProtocol(
                tpap_https_config.credentials, tpap_https_config.url, session
            ),
            tpap_https_config.url,
        )
    ] + common_candidates(https_config, f"HTTPS:{https_config.port}")

    if config.is_support_https:
        return https_candidates + http_candidates
    return http_candidates + https_candidates


def _get_device_class_from_model_type(device_type: str) -> Type[TapoDevice]:
    device_type = device_type.upper()
    if device_type == "SMART.TAPOPLUG":
        return TapoPlug
    elif device_type == "SMART.TAPOBULB":
        return TapoBulb
    elif device_type == "SMART.TAPOHUB":
        return TapoHub
    elif device_type == "SMART.KASAHUB":
        return TapoHub
    elif device_type == "SMART.IPCAMERA":
        raise Exception(f"Device of type {device_type} not supported!")
    return TapoDevice
