import dataclasses
from typing import Any, Optional, Tuple

from plugp100.api.requests.set_device_info.set_light_color_info_params import (
    LightColorDeviceInfoParams,
)
from plugp100.api.requests.set_device_info.set_light_info_params import (
    LightDeviceInfoParams,
)
from plugp100.api.requests.set_device_info.set_plug_info_params import SetPlugInfoParams
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.tri import Try
from plugp100.new.components.device_component import DeviceComponent
from plugp100.responses.device_state import LightDeviceState


@dataclasses.dataclass
class HS:
    hue: int
    saturation: int


class LightComponent(DeviceComponent):
    def __init__(self, client: TapoClient):
        self._client = client
        self._state: LightDeviceState | None = None

    @property
    def device_on(self) -> bool:
        return self._state.device_on

    @property
    def state(self) -> LightDeviceState:
        return self._state

    @property
    def brightness(self) -> Optional[int]:
        return self._state.brightness

    @property
    def hs(self) -> Optional[HS]:
        if self._state.hue is not None and self._state.saturation is not None:
            return HS(self._state.hue, self._state.saturation)
        return None

    @property
    def color_temp(self) -> Optional[int]:
        return self._state.color_temp

    @property
    def color_temp_range(self) -> Tuple[int, int]:
        if temp_range := self._state.color_temp_range is not None:
            return temp_range
        else:
            return 2500, 6500

    async def turn_on(self):
        return await self._client.set_device_info(SetPlugInfoParams(True))

    async def turn_off(self):
        return await self._client.set_device_info(SetPlugInfoParams(False))

    async def set_brightness(self, brightness: int) -> Try[bool]:
        return await self._client.set_device_info(
            LightDeviceInfoParams(brightness=brightness)
        )

    async def set_hue_saturation(self, hue: int, saturation: int) -> Try[bool]:
        return await self._client.set_device_info(
            LightColorDeviceInfoParams(hue=hue, saturation=saturation, color_temp=0)
        )

    async def set_color_temperature(self, color_temperature: int) -> Try[bool]:
        return await self._client.set_device_info(
            LightColorDeviceInfoParams(color_temp=color_temperature)
        )

    async def update(self, current_state: dict[str, Any] | None = None):
        self._state = LightDeviceState.try_from_json(current_state).get_or_raise()
