from typing import Any

from plugp100.components.base import DeviceComponent


class ReportModeComponent(DeviceComponent):
    def __init__(self):
        self._report_interval = None

    @property
    def report_interval_seconds(self) -> int:
        return self._report_interval

    async def update(self, current_state: dict[str, Any] | None = None):
        current_state = current_state or {}
        if "report_interval" in current_state:
            self._report_interval = current_state["report_interval"]
        elif "report_interval_seconds" in current_state:
            self._report_interval = current_state["report_interval_seconds"]
        else:
            self._report_interval = 0
