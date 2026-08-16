from typing import Any

from plugp100.components.base import DeviceComponent


class MotionSensorComponent(DeviceComponent):
    def __init__(self):
        self.detected = False

    async def update(self, current_state: dict[str, Any] | None = None):
        self.detected = (current_state or {})["detected"]
