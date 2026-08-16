from typing import Any

from plugp100.components.base import DeviceComponent


class OverheatComponent(DeviceComponent):
    def __init__(self):
        self._overheat = False

    @property
    def overheated(self) -> bool:
        return self._overheat

    async def update(self, current_state: dict[str, Any] | None = None):
        current_state = current_state or {}
        if "overheated" in current_state:
            self._overheat = current_state["overheated"]
        elif "overheat_status" in current_state:
            self._overheat = current_state["overheat_status"] != "normal"
        else:
            self._overheat = False
