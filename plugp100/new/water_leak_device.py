from plugp100.common.functional.tri import Try
from plugp100.new.tapohub import TapoHub
from plugp100.requests.tapo_request import TapoRequest
from plugp100.responses.hub_childs.leak_device_state import LeakDeviceState


class WaterLeakSensor:
    def __init__(self, hub: TapoHub, device_id: str):
        self._hub = hub
        self._device_id = device_id

    async def get_device_state(self) -> Try[LeakDeviceState]:
        return (
            await self._hub.control_child(self._device_id, TapoRequest.get_device_info())
        ).flat_map(LeakDeviceState.try_from_json)
