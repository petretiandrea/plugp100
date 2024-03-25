from typing import Any

from plugp100.new.components.device_component import DeviceComponent


# TODO: get component_negotiation for Water leak sensor
# this class is actually too specific for Water leak, the component can be called in other way
class WaterLeakComponent(DeviceComponent):
    async def update(self, current_state: dict[str, Any] | None = None):
        self.in_alarm = current_state.get("in_alarm", False)
        self.water_leak_status = current_state["water_leak_status"]

    def __init__(self):
        self.water_leak_status = ""
        self.in_alarm = False
