from typing import Any

from plugp100.components.base import DeviceComponent


class WaterLeakComponent(DeviceComponent):
    def __init__(self):
        self.water_leak_status = ""
        self.in_alarm = False

    async def update(self, current_state: dict[str, Any] | None = None):
        current_state = current_state or {}
        self.in_alarm = current_state.get("in_alarm", False)
        self.water_leak_status = current_state["water_leak_status"]
