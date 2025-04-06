from typing import Any

from plugp100.new.components.device_component import DeviceComponent


class BatteryComponent(DeviceComponent):
    def __init__(self):
        self._battery_low = False
        self._battery_percentage = -1

    @property
    def is_battery_low(self) -> bool:
        return self._battery_low

    @property
    def battery_percentage(self) -> int:
        return self._battery_percentage

    async def update(self, current_state: dict[str, Any] | None = None):
        self._battery_low = (
            current_state["at_low_battery"]
            if "at_low_battery" in current_state
            else False
        )
        self._battery_percentage = current_state.get("battery_percentage", -1)
