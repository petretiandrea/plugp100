from typing import Optional

from plugp100.api.tapo_client import TapoClient
from plugp100.new.device_type import DeviceType
from plugp100.new.tapodevice import AbstractTapoDevice
from plugp100.requests.set_device_info.set_plug_info_params import SetPlugInfoParams
from plugp100.responses.energy_info import EnergyInfo
from plugp100.responses.power_info import PowerInfo


class TapoPlug(AbstractTapoDevice):
    def __init__(self, host: str, port: Optional[int], client: TapoClient):
        super().__init__(host, port, client, DeviceType.Plug)

    async def update(self):
        await super().update()

        if self.components.has("energy_monitoring"):
            energy_usage = await self.client.get_energy_usage()
            power_info = await self.client.get_current_power()
            self._additional_data["energy"] = (
                energy_usage.value if energy_usage.is_success() else None
            )
            self._additional_data["power_info"] = (
                power_info.value if power_info.is_success() else None
            )

    async def turn_on(self):
        return await self.client.set_device_info(SetPlugInfoParams(True))

    async def turn_off(self):
        return await self.client.set_device_info(SetPlugInfoParams(False))

    @property
    def is_on(self) -> bool:
        return self._last_update.get("state", {}).get("device_on", False)

    @property
    def energy_info(self) -> Optional[EnergyInfo]:
        return self._additional_data.get("energy", None)

    @property
    def power_info(self) -> Optional[PowerInfo]:
        return self._additional_data.get("power_info", None)
