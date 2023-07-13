from plugp100.api.light_effect import LightEffect
from plugp100.api.tapo_client import TapoClient, Json
from plugp100.common.functional.either import Either
from plugp100.requests.set_device_info.set_light_color_info_params import LightColorDeviceInfoParams
from plugp100.requests.set_device_info.set_light_info_params import LightDeviceInfoParams
from plugp100.requests.set_device_info.set_plug_info_params import SetPlugInfoParams
from plugp100.responses.device_state import LedStripDeviceState


class LedStripDevice:

    def __init__(self, api: TapoClient, address: str):
        self._api = api
        self._address = address

    async def login(self) -> Either[True, Exception]:
        return await self._api.login(self._address)

    async def get_state(self) -> Either[LedStripDeviceState, Exception]:
        return (await self._api.get_device_info()) | LedStripDeviceState.try_from_json

    async def on(self) -> Either[True, Exception]:
        return await self._api.set_device_info(SetPlugInfoParams(True))

    async def off(self) -> Either[True, Exception]:
        return await self._api.set_device_info(SetPlugInfoParams(False))

    async def set_brightness(self, brightness: int) -> Either[True, Exception]:
        return await self._api.set_device_info(LightDeviceInfoParams(brightness=brightness))

    async def set_hue_saturation(self, hue: int, saturation: int) -> Either[True, Exception]:
        return await self._api.set_device_info(LightColorDeviceInfoParams(hue=hue, saturation=saturation, color_temp=0))

    async def set_color_temperature(self, color_temperature: int) -> Either[True, Exception]:
        return await self._api.set_device_info(LightColorDeviceInfoParams(color_temp=color_temperature))

    async def set_light_effect(self, effect: LightEffect) -> Either[True, Exception]:
        return await self._api.set_lighting_effect(effect)

    async def get_state_as_json(self) -> Either[Json, Exception]:
        return await self._api.get_device_info()
