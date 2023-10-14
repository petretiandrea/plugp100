from plugp100.api.hub.hub_device import HubDevice

from plugp100.common.functional.tri import Try
from plugp100.common.utils.json_utils import dataclass_encode_json
from plugp100.requests.set_device_info.set_plug_info_params import SetPlugInfoParams
from plugp100.requests.tapo_request import TapoRequest
from plugp100.responses.hub_childs.switch_child_device_state import SwitchChildDeviceState


class SwitchChildDevice:
    def __init__(self, hub: HubDevice, device_id: str):
        self._hub = hub
        self._device_id = device_id

    async def get_device_info(self) -> Try[SwitchChildDeviceState]:
        """
        The function `get_device_info` sends a request to retrieve device information and returns either the device state or
        an exception.
        @  return: an instance of the `Either` class, which can hold either an instance of `S200BDeviceState` or an instance
        of `Exception`.
        """
        return (
            await self._hub.control_child(self._device_id, TapoRequest.get_device_info())
        ).flat_map(SwitchChildDeviceState.try_from_json)

    async def on(self) -> Try[bool]:
        request = TapoRequest.set_device_info(
            dataclass_encode_json(SetPlugInfoParams(device_on=True))
        )
        return (await self._hub.control_child(self._device_id, request)).map(
            lambda _: True
        )

    async def off(self) -> Try[bool]:
        request = TapoRequest.set_device_info(
            dataclass_encode_json(SetPlugInfoParams(device_on=False))
        )
        return (await self._hub.control_child(self._device_id, request)).map(
            lambda _: True
        )
