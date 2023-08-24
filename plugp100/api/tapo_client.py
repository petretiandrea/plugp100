import logging
from enum import Enum
from time import time
from typing import Optional, Any, cast

import aiohttp

from plugp100.api.light_effect import LightEffect
from plugp100.common.credentials import AuthCredential
from plugp100.common.functional.tri import Try, Success, Failure
from plugp100.common.utils.json_utils import dataclass_encode_json, Json
from plugp100.protocol.klap_protocol import KlapProtocol
from plugp100.protocol.passthrough_protocol import PassthroughProtocol
from plugp100.protocol.tapo_protocol import TapoProtocol
from plugp100.requests.tapo_request import TapoRequest, MultipleRequestParams
from plugp100.responses.child_device_list import ChildDeviceList
from plugp100.responses.energy_info import EnergyInfo
from plugp100.responses.power_info import PowerInfo

logger = logging.getLogger(__name__)


class TapoProtocolType(Enum):
    KLAP = 1
    PASSTHROUGH = 2


class TapoClient:
    def __init__(
        self,
        auth_credential: AuthCredential,
        ip_address: str,
        protocol_type: TapoProtocolType = TapoProtocolType.PASSTHROUGH,
        http_session: Optional[aiohttp.ClientSession] = None,
        auto_recover_expired_session: bool = False,
    ):
        self._protocol: TapoProtocol = (
            KlapProtocol(
                auth_credential=auth_credential,
                host=ip_address,
                http_session=http_session,
            )
            if protocol_type == TapoProtocolType.KLAP
            else PassthroughProtocol(
                auth_credential=auth_credential,
                host=ip_address,
                http_session=http_session,
                auto_recover_expired_session=auto_recover_expired_session,
            )
        )

    async def close(self):
        await self._protocol.close()

    async def execute_raw_request(self, request: "TapoRequest") -> Try[Json]:
        return (await self._protocol.send_request(request)).map(lambda x: x.result)

    async def get_device_info(self) -> Try[Json]:
        """
        The function `get_device_info` sends a request to retrieve device information and returns the result or an
        exception.
        @return: an `Either` object that contains either a `Json` object or an `Exception`.
        """
        get_info_request = TapoRequest.get_device_info()
        return (await self._protocol.send_request(get_info_request)).map(
            lambda x: x.result
        )

    async def get_energy_usage(self) -> Try[EnergyInfo]:
        """
        The function `get_energy_usage` makes a request to get energy usage information and returns either the energy info
        or an exception.
        @return: an `Either` type, which can either contain an `EnergyInfo` object or an `Exception` object.
        """
        get_energy_request = TapoRequest.get_energy_usage()
        response = await self._protocol.send_request(get_energy_request)
        return response.map(lambda x: EnergyInfo(x.result))

    async def get_current_power(self) -> Try[PowerInfo]:
        """
        The function `get_current_power` asynchronously retrieves the current power information and returns it as a
        `PowerInfo` object, or an `Exception` if an error occurs.
        @return: an `Either` object that contains either a `PowerInfo` object or an `Exception`.
        """
        get_current_power = TapoRequest.get_current_power()
        response = await self._protocol.send_request(get_current_power)
        return response.map(lambda x: PowerInfo(x.result))

    async def set_device_info(self, device_info: Any) -> Try[True]:
        """
        The function `set_device_info` encodes the `device_info` object into JSON format and returns either `True` or an
        `Exception`.

        @param device_info: The `device_info` parameter is an object that contains information about a device. It is passed
        to the `set_device_info` method as an argument
        @return: an `Either` type, which can either be `True` or an `Exception`.
        """
        return await self._set_device_info(dataclass_encode_json(device_info))

    async def set_lighting_effect(self, light_effect: LightEffect) -> Try[True]:
        """
        The function `set_lighting_effect` sets a lighting effect for a device and returns either `True` or an exception.

        @param light_effect: The `light_effect` parameter is of type `LightEffect`. It represents the desired lighting
        effect that you want to set for a device
        @type light_effect: LightEffect
        @return: an `Either` object that contains either a `True` value or an `Exception`.
        """
        response = await self._protocol.send_request(
            TapoRequest.set_lighting_effect(light_effect)
        )
        return response.map(lambda _: True)

    async def get_child_device_list(self) -> Try[ChildDeviceList]:
        """
        The function `get_child_device_list` retrieves a list of child devices asynchronously and returns either the list or
        an exception.
        @return: an `Either` object, which can contain either a `ChildDeviceList` or an `Exception`.
        """
        request = TapoRequest.get_child_device_list()
        return (await self._protocol.send_request(request)).map(
            lambda x: ChildDeviceList.try_from_json(**x.result)
        )

    async def get_child_device_component_list(self) -> Try[Json]:
        """
        The function `get_child_device_component_list` retrieves a list of child device components asynchronously and
        returns either the JSON response or an exception.
        @return: an `Either` object, which can contain either a `Json` object or an `Exception`.
        """
        request = TapoRequest.get_child_device_component_list()
        return (await self._protocol.send_request(request)).map(lambda x: x.result)

    async def control_child(self, child_id: str, request: TapoRequest) -> Try[Json]:
        """
        The function `control_child` is an asynchronous method that sends a control request to a child device and returns
        the response or an exception.

        @param child_id: The `child_id` parameter is a string that represents the ID of a child device
        @type child_id: str
        @param request: The `request` parameter is an instance of the `TapoRequest` class. It represents a request to be
        sent to the Tapo device.
        @type request: TapoRequest
        @return: an instance of the `Either` class, which can contain either a `Json` object or an `Exception`.
        """
        multiple_request = TapoRequest.multiple_request(
            MultipleRequestParams([request])
        ).with_request_time_millis(round(time() * 1000))
        request = TapoRequest.control_child(child_id, multiple_request)
        response = await self._protocol.send_request(request)
        if response.is_success():
            try:
                responses = response.get().result["responseData"]["result"]["responses"]
                if len(responses) > 0:
                    return (
                        Success(responses[0]["result"])
                        if "result" in responses[0]
                        else Success(responses[0])
                    )
                else:
                    return Failure(Exception("Empty responses from child"))
            except Exception as e:
                return Failure(e)
        return cast(Failure, response)

    async def _set_device_info(self, device_info: Json) -> Try[True]:
        response = await self._protocol.send_request(
            TapoRequest.set_device_info(device_info)
        )
        return response.map(lambda _: True)
