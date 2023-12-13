from plugp100.api.hub.hub_device import HubDevice

from plugp100.common.functional.tri import Try
from plugp100.requests.tapo_request import TapoRequest
from plugp100.responses.components import Components
from plugp100.responses.hub_childs.t31x_device_state import (
    T31DeviceState,
    TemperatureHumidityRecordsRaw,
)


class T31Device:
    def __init__(self, hub: HubDevice, device_id: str):
        self._hub = hub
        self._device_id = device_id

    async def get_device_state(self) -> Try[T31DeviceState]:
        return (
            await self._hub.control_child(self._device_id, TapoRequest.get_device_info())
        ).flat_map(T31DeviceState.from_json)

    async def get_temperature_humidity_records(
        self,
    ) -> Try[TemperatureHumidityRecordsRaw]:
        request = TapoRequest.get_temperature_humidity_records()
        response = await self._hub.control_child(self._device_id, request)
        return response.flat_map(TemperatureHumidityRecordsRaw.from_json)

    async def get_component_negotiation(self) -> Try[Components]:
        return (
            await self._hub.control_child(
                self._device_id, TapoRequest.component_negotiation()
            )
        ).map(Components.try_from_json)
