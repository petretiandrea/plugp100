from plugp100.api.base_tapo_device import _BaseTapoDevice
from plugp100.api.light_effect import LightEffect
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.tri import Try
from plugp100.requests.set_device_info.set_light_color_info_params import (
    LightColorDeviceInfoParams,
)
from plugp100.requests.set_device_info.set_light_info_params import (
    LightDeviceInfoParams,
)
from plugp100.requests.set_device_info.set_plug_info_params import SetPlugInfoParams
from plugp100.responses.device_state import LedStripDeviceState


class LedStripDevice(_BaseTapoDevice):
    def __init__(self, api: TapoClient):
        super().__init__(api)

    async def get_state(self) -> Try[LedStripDeviceState]:
        return (await self._api.get_device_info()).flat_map(
            LedStripDeviceState.try_from_json
        )

    async def on(self) -> Try[bool]:
        return await self._api.set_device_info(SetPlugInfoParams(True))

    async def off(self) -> Try[bool]:
        return await self._api.set_device_info(SetPlugInfoParams(False))

    async def set_brightness(self, brightness: int) -> Try[bool]:
        return await self._api.set_device_info(
            LightDeviceInfoParams(brightness=brightness)
        )

    async def set_hue_saturation(self, hue: int, saturation: int) -> Try[bool]:
        return await self._api.set_device_info(
            LightColorDeviceInfoParams(hue=hue, saturation=saturation, color_temp=0)
        )

    async def set_color_temperature(self, color_temperature: int) -> Try[bool]:
        return await self._api.set_device_info(
            LightColorDeviceInfoParams(color_temp=color_temperature)
        )

    async def set_light_effect(self, effect: LightEffect) -> Try[bool]:
        return await self._api.set_lighting_effect(effect)

    async def set_light_effect_brightness(
        self, effect: LightEffect, brightness: int
    ) -> Try[bool]:
        effect.brightness = brightness
        effect.bAdjusted = 1
        effect.enable = 1
        return await self._api.set_lighting_effect(effect)
