from typing import Optional

from plugp100.api.tapo_client import TapoClient
from plugp100.components.battery import BatteryComponent
from plugp100.components.report_mode import ReportModeComponent
from plugp100.devices.base import C, TapoDevice
from plugp100.devices.types import DeviceType
from plugp100.models.components import Components


class TapoHubChildDevice(TapoDevice):
    def __init__(
        self,
        host: str,
        port: Optional[int],
        client: TapoClient,
        child_id: str,
        parent_device_id: str,
        device_type: DeviceType = DeviceType.Sensor,
    ):
        super().__init__(host, port, client, device_type, child_id)
        self._parent_device_id = parent_device_id

    @property
    def parent_device_id(self) -> str:
        return self._parent_device_id

    @property
    def battery_low(self) -> bool:
        return self.get_component(BatteryComponent).is_battery_low

    @property
    def report_interval_seconds(self) -> int:
        return self.get_component(ReportModeComponent).report_interval_seconds

    def _get_components_to_activate(self, components: Components) -> list[C]:
        active_components = [ReportModeComponent()]
        if components.has("battery_detect"):
            active_components.append(BatteryComponent())
        return active_components


__all__ = ["TapoHubChildDevice"]
