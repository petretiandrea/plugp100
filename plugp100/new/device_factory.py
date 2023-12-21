import functools
import logging
from typing import Optional, Any, Type

import aiohttp

from plugp100.common.credentials import AuthCredential
from plugp100.protocol.klap_protocol import KlapProtocol
from plugp100.protocol.passthrough_protocol import PassthroughProtocol
from plugp100.requests.tapo_request import TapoRequest
from plugp100.responses.tapo_exception import TapoException
from .tapobulb import TapoBulb
from .tapodevice import TapoDevice
from .tapoplug import TapoPlug
from .tapoplugstrip import TapoPlugStrip
from ..api.tapo_client import TapoClient
from ..responses.device_state import DeviceInfo

_LOGGER = logging.getLogger("DeviceFactory")


async def connect(
    host: str,
    port: Optional[int],
    credentials: AuthCredential,
    session: aiohttp.ClientSession,
) -> TapoDevice:
    client, info = await _get_client_and_info(host, port, credentials, session)
    factory = _get_device_class_from_info(info)
    return factory(host, port, client)


async def _get_client_and_info(
    host: str,
    port: Optional[int],
    credentials: AuthCredential,
    session: aiohttp.ClientSession,
) -> tuple[TapoClient, dict[str, Any]]:
    url = f"http://{host}:{port}/app"
    device_info_request = TapoRequest.get_device_info()
    protocol = PassthroughProtocol(credentials, url, session)
    response = await protocol.send_request(device_info_request)
    client_factory = functools.partial(lambda p, s: TapoClient(credentials, url, p, s))
    if response.is_success():
        return client_factory(protocol, session), response.value.result
    else:
        error = response.error()
        if isinstance(error, TapoException) and error.error_code == 1003:
            _LOGGER.warning("Default protocol not working, fallback to KLAP ;)")
            protocol = KlapProtocol(
                auth_credential=credentials,
                url=url,
                http_session=session,
            )
            response = (await protocol.send_request(device_info_request)).get_or_raise()
            return client_factory(protocol, session), response.result
        else:
            raise error


def _get_device_class_from_info(device_info: dict[str, Any]) -> Type[TapoDevice]:
    info = DeviceInfo(**device_info)
    type = info.type.upper()
    model = info.model.lower()
    if type == "SMART.TAPOPLUG":
        return TapoPlugStrip if "p300" in model else TapoPlug
    elif type == "SMART.TAPOBULB":
        return TapoBulb
    elif type == "SMART.":
        pass
    return TapoDevice
