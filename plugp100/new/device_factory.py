import dataclasses
import logging
from typing import Optional, Type

import aiohttp

from plugp100.common.credentials import AuthCredential
from plugp100.protocol.klap.klap_protocol import KlapProtocol
from plugp100.protocol.passthrough_protocol import PassthroughProtocol
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
    scheme: str = "http"
    verify_ssl: bool = True
    credentials: Optional[AuthCredential] = None
    device_type: Optional[str] = None
    device_model: Optional[str] = None
    encryption_type: Optional[str] = None
    encryption_version: Optional[int] = None

    @property
    def url(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}/app"


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
            verify_ssl=config.verify_ssl,
        )
    elif config.encryption_type.lower() == "aes":
        return PassthroughProtocol(
            auth_credential=config.credentials,
            url=config.url,
            http_session=session,
            verify_ssl=config.verify_ssl,
        )
    else:
        raise Exception("Failed to determine the right tapo protocol")


async def _guess_protocol(
    config: DeviceConnectConfiguration, session: Optional[aiohttp.ClientSession] = None
) -> TapoProtocol:
    protocol = await _try_protocols_at(config, session)
    if protocol is not None:
        return protocol

    # H200 hubs (and other recent Tapo firmwares) only listen on HTTPS:443
    # with a self-signed TPRI-DEVICE certificate. If the default HTTP:80
    # transport failed completely, retry over HTTPS:443 with TLS verification
    # disabled before declaring it an authentication failure.
    if config.scheme == "http" and config.port == 80:
        _LOGGER.debug(
            "HTTP:80 protocols failed for %s, retrying over HTTPS:443", config.host
        )
        https_config = dataclasses.replace(
            config, scheme="https", port=443, verify_ssl=False
        )
        protocol = await _try_protocols_at(https_config, session)
        if protocol is not None:
            return protocol

    _LOGGER.error("None of available protocol is working, maybe invalid credentials")
    raise InvalidAuthentication(config.host, config.device_type)


async def _try_protocols_at(
    config: DeviceConnectConfiguration, session: Optional[aiohttp.ClientSession] = None
) -> Optional[TapoProtocol]:
    protocols = [
        PassthroughProtocol(
            config.credentials, config.url, session, verify_ssl=config.verify_ssl
        ),
        KlapProtocol(
            config.credentials,
            config.url,
            klap_handshake_v1(),
            session,
            verify_ssl=config.verify_ssl,
        ),
        KlapProtocol(
            config.credentials,
            config.url,
            klap_handshake_v2(),
            session,
            verify_ssl=config.verify_ssl,
        ),
    ]
    device_info_request = TapoRequest.get_device_info()
    for i, protocol in enumerate(protocols):
        info = await protocol.send_request(device_info_request)
        if info.is_success():
            _LOGGER.debug(
                "Found working protocol %s at %s", type(protocol), config.url
            )
            for j, p in enumerate(protocols):
                if i != j:
                    await p.close()
            return protocol
        else:
            _LOGGER.debug(
                "Protocol %s at %s not working, trying next...",
                type(protocol),
                config.url,
            )
            await protocol.close()
    return None


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


