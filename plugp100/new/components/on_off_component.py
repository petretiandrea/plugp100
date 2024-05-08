from typing import Any

from plugp100.api.requests.set_device_info.set_plug_info_params import SetPlugInfoParams
from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.api.tapo_client import TapoClient
from plugp100.common.utils.json_utils import dataclass_encode_json
from plugp100.new.components.device_component import DeviceComponent


class OnOffComponent(DeviceComponent):
    def __init__(self, client: TapoClient, child_id: str | None = None):
        self._client = client
        self._device_on = False
        self._child_id = child_id

    @property
    def device_on(self) -> bool:
        return self._device_on

    async def turn_on(self):
        if self._child_id:
            request = TapoRequest.set_device_info(
                dataclass_encode_json(SetPlugInfoParams(device_on=True))
            )
            return await self._client.control_child(self._child_id, request)
        return await self._client.set_device_info(SetPlugInfoParams(True))

    async def turn_off(self):
        if self._child_id:
            request = TapoRequest.set_device_info(
                dataclass_encode_json(SetPlugInfoParams(device_on=False))
            )
            return await self._client.control_child(self._child_id, request)
        return await self._client.set_device_info(SetPlugInfoParams(False))

    async def update(self, current_state: dict[str, Any] | None = None):
        self._device_on = current_state.get("device_on", False)
