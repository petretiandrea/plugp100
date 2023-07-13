from plugp100.api.hub.hub_device import HubDevice
from plugp100.common.functional.either import Either
from plugp100.requests.tapo_request import TapoRequest
from plugp100.responses.hub_childs.t31x_device_state import T31DeviceState, TemperatureHumidityRecordsRaw


class T31Device:

    def __init__(self, hub: HubDevice, device_id: str):
        self._hub = hub
        self._device_id = device_id

    async def get_device_state(self) -> Either[T31DeviceState, Exception]:
        request = TapoRequest.get_device_info()
        return await self._hub.control_child(self._device_id, request) | T31DeviceState.from_json

    async def get_temperature_humidity_records(self) -> Either[TemperatureHumidityRecordsRaw, Exception]:
        request = TapoRequest.get_temperature_humidity_records()
        response = await self._hub.control_child(self._device_id, request)
        return response | TemperatureHumidityRecordsRaw.from_json
