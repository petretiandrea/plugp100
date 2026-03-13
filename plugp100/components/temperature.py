from typing import Any

from plugp100.components.base import DeviceComponent
from plugp100.models.temperature import TemperatureUnit


class TemperatureComponent(DeviceComponent):
    def __init__(self):
        self.current_temperature = None
        self.current_temperature_error = None
        self.temperature_unit = TemperatureUnit.CELSIUS

    async def update(self, current_state: dict[str, Any] | None = None):
        current_state = current_state or {}
        self.current_temperature = current_state["current_temp"]
        self.current_temperature_error = current_state["current_temp_exception"]
        self.temperature_unit = next(
            (
                member
                for member in TemperatureUnit
                if member.value == current_state.get("temp_unit")
            ),
            TemperatureUnit.CELSIUS,
        )
