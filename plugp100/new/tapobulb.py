from typing import Optional, Tuple

from plugp100.api.light_effect import LightEffect
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.tri import Try, Failure
from plugp100.new.components.light_component import LightComponent, HS
from plugp100.new.components.light_effect_component import LightEffectComponent
from plugp100.new.device_type import DeviceType
from plugp100.new.tapodevice import TapoDevice, C
from plugp100.responses.components import Components


class TapoBulb(TapoDevice):
    def __init__(self, host: str, port: Optional[int], client: TapoClient):
        super().__init__(host, port, client, DeviceType.Bulb)

    @property
    def is_on(self) -> bool:
        return self.get_component(LightComponent).device_on

    @property
    def is_brightness(self):
        return self.components.has("brightness")

    @property
    def is_color(self) -> bool:
        return self.components.has("color")

    @property
    def is_color_temperature(self) -> bool:
        return self.components.has("color_temperature")

    @property
    def color_temp_range(self) -> Tuple[int, int]:
        return self.get_component(LightComponent).color_temp_range

    @property
    def has_effect(self) -> bool:
        return self.get_component(LightEffectComponent) is not None

    @property
    def effect(self) -> Optional[LightEffect]:
        if self.has_effect:
            return self.get_component(LightEffectComponent).active_effect
        else:
            return None

    @property
    def color_temp(self) -> Optional[int]:
        return self.get_component(LightComponent).color_temp

    @property
    def hs(self) -> Optional[HS]:
        return self.get_component(LightComponent).hs

    @property
    def brightness(self) -> Optional[int]:
        if light_component := self.get_component(LightEffectComponent):
            if light_component.brightness is not None:
                return light_component.brightness
        return self.get_component(LightComponent).brightness

    @property
    def is_led_strip(self) -> bool:
        return self.components.has("light_strip")

    async def set_brightness(self, brightness: int) -> Try[bool]:
        return await self.get_component(LightComponent).set_brightness(brightness)

    async def set_hue_saturation(self, hue: int, saturation: int) -> Try[bool]:
        return await self.get_component(LightComponent).set_hue_saturation(
            hue, saturation
        )

    async def set_color_temperature(self, color_temperature: int) -> Try[bool]:
        return await self.get_component(LightComponent).set_color_temperature(
            color_temperature
        )

    async def set_light_effect(self, effect: LightEffect) -> Try[bool]:
        if self.has_effect:
            return await self.get_component(LightEffectComponent).set_light_effect(effect)
        else:
            return Failure(Exception("Setting effect not supported"))

    async def set_light_effect_brightness(
        self, effect: LightEffect, brightness: int
    ) -> Try[bool]:
        if self.has_effect:
            return await self.get_component(
                LightEffectComponent
            ).set_light_effect_brightness(effect, brightness)
        else:
            return Failure(Exception("Setting brightness of effect not supported"))

    async def turn_on(self):
        return await self.get_component(LightComponent).turn_on()

    async def turn_off(self):
        return await self.get_component(LightComponent).turn_off()

    def _get_components_to_activate(self, components: Components) -> list[C]:
        active_components = [LightComponent(self.client)]
        if components.has("light_strip_lighting_effect"):
            active_components.append(LightEffectComponent(self.client))
        return active_components
