from plugp100.components.water_leak import WaterLeakComponent
from plugp100.devices.children.base import TapoHubChildDevice


class WaterLeakSensor(TapoHubChildDevice):
    def _get_components_to_activate(self, components):
        return super()._get_components_to_activate(components) + [WaterLeakComponent()]

    @property
    def is_alarm_active(self) -> bool:
        return self.get_component(WaterLeakComponent).in_alarm

    @property
    def water_leak_status(self) -> str:
        return self.get_component(WaterLeakComponent).water_leak_status


__all__ = ["WaterLeakSensor"]
