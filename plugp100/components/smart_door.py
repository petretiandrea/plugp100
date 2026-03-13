import logging
from typing import Any

from plugp100.components.base import DeviceComponent

_LOGGER = logging.getLogger("SmartDoorComponent")


class SmartDoorComponent(DeviceComponent):
    def __init__(self):
        self.is_open = False

    async def update(self, current_state: dict[str, Any] | None = None):
        current_state = current_state or {}
        if "is_open" in current_state:
            self.is_open = current_state["is_open"]
        elif "open" in current_state:
            self.is_open = current_state["open"]
        else:
            _LOGGER.warning("Open state not found in current state")
