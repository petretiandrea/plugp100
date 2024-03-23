from typing import Any

from plugp100.new.components.device_component import DeviceComponent


class HumidityComponent(DeviceComponent):
    async def update(self, current_state: dict[str, Any] | None = None):
        self.current_humidity = current_state["current_humidity"]
        self.current_humidity_error = current_state["current_humidity_exception"]

    def __init__(self):
        self.current_humidity = 0
        self.current_humidity_error = None
