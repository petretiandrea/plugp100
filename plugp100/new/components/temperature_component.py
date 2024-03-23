from typing import Any

from plugp100.new.components.device_component import DeviceComponent
from plugp100.responses.temperature_unit import TemperatureUnit


class TemperatureComponent(DeviceComponent):
    def __init__(self):
        self.current_temperature = None
        self.current_temperature_error = None
        self.temperature_unit = TemperatureUnit.CELSIUS

    async def update(self, current_state: dict[str, Any] | None = None):
        self.current_temperature = current_state["current_temp"]
        self.current_temperature_error = current_state["current_temp_exception"]
        self.temperature_unit = next(
            [
                member
                for member in TemperatureUnit
                if member.value == current_state.get("temp_unit")
            ].__iter__(),
            TemperatureUnit.CELSIUS,
        )
