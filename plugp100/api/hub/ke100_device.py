from typing import Any
from plugp100.api.hub.hub_device import HubDevice

from plugp100.common.functional.tri import Try
from plugp100.common.utils.json_utils import dataclass_encode_json
from plugp100.requests.set_device_info.set_trv_info_params import TRVDeviceInfoParams
from plugp100.requests.tapo_request import TapoRequest
from plugp100.responses.hub_childs.ke100_device_state import KE100DeviceState


class KE100Device:
    def __init__(self, hub: HubDevice, device_id: str):
        self._hub = hub
        self._device_id = device_id

    async def get_device_state(self) -> Try[KE100DeviceState]:
        return (
            await self._hub.control_child(self._device_id, TapoRequest.get_device_info())
        ).flat_map(KE100DeviceState.from_json)

    async def set_target_temp(self, kwargs: Any) -> Try[bool]:
        return await self.send_trv_control_request(
            TRVDeviceInfoParams(target_temp=kwargs["temperature"])
        )

    async def set_temp_offset(self, value: int) -> Try[bool]:
        return await self.send_trv_control_request(TRVDeviceInfoParams(temp_offset=value))

    async def set_frost_protection_on(self) -> Try[bool]:
        return await self.send_trv_control_request(
            TRVDeviceInfoParams(frost_protection_on=True)
        )

    async def set_frost_protection_off(self) -> Try[bool]:
        return await self.send_trv_control_request(
            TRVDeviceInfoParams(frost_protection_on=False)
        )

    async def set_child_protection_on(self) -> Try[bool]:
        return await self.send_trv_control_request(
            TRVDeviceInfoParams(child_protection=True)
        )

    async def set_child_protection_off(self) -> Try[bool]:
        return await self.send_trv_control_request(
            TRVDeviceInfoParams(child_protection=False)
        )

    async def send_trv_control_request(self, params: TRVDeviceInfoParams) -> Try[bool]:
        request = TapoRequest.set_device_info(dataclass_encode_json(params))
        return (await self._hub.control_child(self._device_id, request)).map(
            lambda _: True
        )
