from typing import Any

from plugp100.new.components.device_component import DeviceComponent


# TODO: get component_negotiation for Tapo Motion Sensor
# this class is actually too specific for T100
class MotionSensorComponent(DeviceComponent):
    def __init__(self):
        self.detected = False

    async def update(self, current_state: dict[str, Any] | None = None):
        self.detected = current_state["detected"]
