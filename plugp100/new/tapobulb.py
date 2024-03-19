import dataclasses
from typing import Optional, Union, Tuple

from plugp100.api.light_effect import LightEffect
from plugp100.api.requests.set_device_info.set_light_color_info_params import (
    LightColorDeviceInfoParams,
)
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.tri import Try, Failure
from plugp100.new.device_type import DeviceType
from plugp100.new.tapodevice import AbstractTapoDevice

from plugp100.api.requests.set_device_info.set_light_info_params import (
    LightDeviceInfoParams,
)
from plugp100.api.requests.set_device_info.set_plug_info_params import SetPlugInfoParams
from plugp100.responses.device_state import LedStripDeviceState, LightDeviceState


@dataclasses.dataclass
class HS:
    hue: int
    saturation: int


class TapoBulb(AbstractTapoDevice):
    def __init__(self, host: str, port: Optional[int], client: TapoClient):
        super().__init__(host, port, client, DeviceType.Bulb)
        self._is_led_strip = None
        self._internal_state: Union[LightDeviceState, LedStripDeviceState, None] = None

    async def update(self):
        await super().update()
        self._is_led_strip = self.components.has("light_strip")
        if self._is_led_strip:
            self._internal_state = (
                LedStripDeviceState.try_from_json(self._last_update.get("state"))
            ).get_or_raise()
        else:
            self._internal_state = (
                LightDeviceState.try_from_json(self._last_update.get("state"))
            ).get_or_raise()

    @property
    def is_on(self) -> bool:
        return self._internal_state.device_on

    @property
    def is_color(self) -> bool:
        return self.components.has("color")

    @property
    def is_color_temperature(self) -> bool:
        return self.components.has("color_temperature")

    @property
    def color_temp_range(self) -> Tuple[int, int]:
        if temp_range := self._internal_state.color_temp_range is not None:
            return temp_range
        else:
            return 2500, 6500

    @property
    def has_effect(self) -> bool:
        return self.components.has("light_strip_lighting_effect")

    @property
    def effect(self) -> Optional[LightEffect]:
        if self.has_effect:
            return self._internal_state.lighting_effect
        else:
            return None

    @property
    def color_temp(self) -> Optional[int]:
        return self._internal_state.color_temp

    @property
    def hs(self) -> Optional[HS]:
        if (
            self._internal_state.hue is not None
            and self._internal_state.saturation is not None
        ):
            return HS(self._internal_state.hue, self._internal_state.saturation)
        return None

    @property
    def brightness(self) -> Optional[int]:
        if self.effect is not None and self.effect.enable:
            return self.effect.brightness
        return self._internal_state.brightness

    async def set_brightness(self, brightness: int) -> Try[bool]:
        return await self.client.set_device_info(
            LightDeviceInfoParams(brightness=brightness)
        )

    async def set_hue_saturation(self, hue: int, saturation: int) -> Try[bool]:
        return await self.client.set_device_info(
            LightColorDeviceInfoParams(hue=hue, saturation=saturation, color_temp=0)
        )

    async def set_color_temperature(self, color_temperature: int) -> Try[bool]:
        return await self.client.set_device_info(
            LightColorDeviceInfoParams(color_temp=color_temperature)
        )

    async def set_light_effect(self, effect: LightEffect) -> Try[bool]:
        if self.has_effect:
            return await self.client.set_lighting_effect(effect)
        else:
            return Failure(Exception("Setting effect not supported"))

    async def set_light_effect_brightness(
        self, effect: LightEffect, brightness: int
    ) -> Try[bool]:
        if self.has_effect:
            effect.brightness = brightness
            effect.bAdjusted = 1
            effect.enable = 1
            return await self.client.set_lighting_effect(effect)
        else:
            return Failure(Exception("Setting brightness of effect not supported"))

    async def turn_on(self):
        return await self.client.set_device_info(SetPlugInfoParams(True))

    async def turn_off(self):
        return await self.client.set_device_info(SetPlugInfoParams(False))
