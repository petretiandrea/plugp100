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
from .errors.invalid_authentication import InvalidAuthentication
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
    device_info_request = TapoRequest.get_device_info()
    for candidate in _build_protocol_candidates(config, session):
        protocol = candidate.factory()
        success = False
        try:
            request = protocol.send_request(device_info_request)
            info = (
                await asyncio.wait_for(request, timeout=config.timeout)
                if config.timeout is not None
                else await request
            )
            if info.is_success():
                success = True
                _LOGGER.debug("Found working protocol %s", candidate.name)
                return protocol
            _LOGGER.debug(
                "Protocol candidate %s failed: %s",
                candidate.name,
                info.error(),
            )
        except Exception as ex:
            _LOGGER.debug("Protocol candidate %s failed: %s", candidate.name, ex)
        finally:
            if not success:
                with suppress(Exception):
                    await protocol.close()

    _LOGGER.error("None of available protocol is working, maybe invalid credentials")
    raise InvalidAuthentication(config.host, config.device_type)


@dataclasses.dataclass(frozen=True)
class _ProtocolCandidate:
    name: str
    factory: Callable[[], TapoProtocol]


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
            ),
            _ProtocolCandidate(
                f"KLAP v1 {label}",
                lambda endpoint=endpoint: KlapProtocol(
                    endpoint.credentials,
                    endpoint.url,
                    klap_handshake_v1(),
                    session,
                ),
            ),
            _ProtocolCandidate(
                f"KLAP v2 {label}",
                lambda endpoint=endpoint: KlapProtocol(
                    endpoint.credentials,
                    endpoint.url,
                    klap_handshake_v2(),
                    session,
                ),
            ),
        ]

    http_candidates = common_candidates(http_config, f"HTTP:{http_config.port}")
    http_candidates.append(
        _ProtocolCandidate(
            f"TPAP HTTP:{http_config.port}",
            lambda: TpapProtocol(http_config.credentials, http_config.url, session),
        )
    )
    https_candidates = common_candidates(https_config, f"HTTPS:{https_config.port}")
    https_candidates.append(
        _ProtocolCandidate(
            f"TPAP HTTPS:{tpap_https_config.port}",
            lambda: TpapProtocol(
                tpap_https_config.credentials, tpap_https_config.url, session
            ),
        )
    )

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
