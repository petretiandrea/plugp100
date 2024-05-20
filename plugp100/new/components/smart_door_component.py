import logging
from typing import Any

from plugp100.new.components.device_component import DeviceComponent


_LOGGER = logging.getLogger("SmartDoorComponent")

# TODO: get component_negotiation for Tapo Smart Door sensor
# this class is actually too specific for SmartDoor, the component can be called open_closed


class SmartDoorComponent(DeviceComponent):
    def __init__(self):
        self.is_open = False

    async def update(self, current_state: dict[str, Any] | None = None):
        if "is_open" in current_state:
            self.is_open = current_state["is_open"]
        elif "open" in current_state:
            self.is_open = current_state["open"]
        else:
            _LOGGER.warning("Open state not found in current state")
