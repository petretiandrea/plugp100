from typing import Any

from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.tri import Try
from plugp100.new.components.device_component import DeviceComponent
from plugp100.responses.hub_childs.t31x_device_state import TemperatureHumidityRecordsRaw


class TemperatureHumidityRecordComponent(DeviceComponent):
    def __init__(self, client: TapoClient, child_id: str | None = None):
        self._client = client
        self._child_id = child_id

    async def update(self, current_state: dict[str, Any] | None = None):
        pass

    async def get_temperature_humidity_records(
        self,
    ) -> Try[TemperatureHumidityRecordsRaw]:
        request = TapoRequest.get_temperature_humidity_records()
        response = await self._client.control_child(self._child_id, request)
        return response.flat_map(TemperatureHumidityRecordsRaw.from_json)
