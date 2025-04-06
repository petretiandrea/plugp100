from typing import Optional, Any

from plugp100.api.tapo_client import TapoClient
from plugp100.new.components.device_component import DeviceComponent
from plugp100.responses.energy_info import EnergyInfo
from plugp100.responses.power_info import PowerInfo


class EnergyComponent(DeviceComponent):
    def __init__(self, client: TapoClient):
        self._client = client
        self._energy_usage = None
        self._power_info = None

    async def update(self, current_state: dict[str, Any] | None = None):
        energy_usage = await self._client.get_energy_usage()
        power_info = await self._client.get_current_power()
        self._energy_usage = energy_usage.value if energy_usage.is_success() else None
        self._power_info = power_info.value if power_info.is_success() else None

    @property
    def energy_info(self) -> Optional[EnergyInfo]:
        return self._energy_usage

    @property
    def power_info(self) -> Optional[PowerInfo]:
        return self._power_info
