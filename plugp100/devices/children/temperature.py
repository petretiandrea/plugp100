from plugp100.common.functional.tri import Try
from plugp100.components.humidity import HumidityComponent
from plugp100.components.temperature import TemperatureComponent
from plugp100.components.temperature_humidity_records import (
    TemperatureHumidityRecordComponent,
)
from plugp100.devices.children.base import TapoHubChildDevice
from plugp100.models.hub_children.temperature import TemperatureHumidityRecordsRaw
from plugp100.models.temperature import TemperatureUnit


class TemperatureHumiditySensor(TapoHubChildDevice):
    def _get_components_to_activate(self, components):
        active_components = []
        if components.has("temperature"):
            active_components.append(TemperatureComponent())
        if components.has("humidity"):
            active_components.append(HumidityComponent())
        if components.has("temp_humidity_record"):
            active_components.append(
                TemperatureHumidityRecordComponent(self.client, self._child_id)
            )
        return super()._get_components_to_activate(components) + active_components

    async def get_temperature_humidity_records(
        self,
    ) -> Try[TemperatureHumidityRecordsRaw]:
        return await self.get_component(
            TemperatureHumidityRecordComponent
        ).get_temperature_humidity_records()

    @property
    def current_humidity(self) -> int:
        return self.get_component(HumidityComponent).current_humidity

    @property
    def current_humidity_error(self) -> int:
        return self.get_component(HumidityComponent).current_humidity_error

    @property
    def current_temperature(self) -> float:
        return self.get_component(TemperatureComponent).current_temperature

    @property
    def current_temperature_error(self) -> float:
        return self.get_component(TemperatureComponent).current_temperature_error

    @property
    def temperature_unit(self) -> TemperatureUnit:
        return self.get_component(TemperatureComponent).temperature_unit


__all__ = ["TemperatureHumiditySensor"]
