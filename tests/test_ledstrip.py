import unittest

from plugp100.api.ledstrip_device import LedStripDevice
from plugp100.api.light_effect import LightEffect
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.either import value_or_raise
from tests.tapo_test_helper import _test_expose_device_info, get_test_config


class LedStripTest(unittest.IsolatedAsyncioTestCase):
    _device = None
    _api = None

    async def asyncSetUp(self) -> None:
        username, password, ip = await get_test_config(device_type="ledstrip")
        self._api = TapoClient(username, password)
        self._device = LedStripDevice(self._api, ip)
        await self._device.login()

    async def asyncTearDown(self):
        await self._api.close()

    async def test_expose_device_info(self):
        state = value_or_raise(await self._device.get_state()).info
        await _test_expose_device_info(state, self)

    async def test_should_turn_on_off(self):
        await self._device.on()
        state = value_or_raise(await self._device.get_state())
        self.assertEqual(True, state.device_on)
        await self._device.off()
        state = value_or_raise(await self._device.get_state())
        self.assertEqual(False, state.device_on)

    async def test_should_set_brightness(self):
        await self._device.on()
        await self._device.set_brightness(40)
        state = value_or_raise(await self._device.get_state())
        self.assertEqual(40, state.brightness)

    async def test_should_set_hue_saturation(self):
        await self._device.on()
        await self._device.set_hue_saturation(120, 10)
        state = value_or_raise(await self._device.get_state())
        self.assertEqual(120, state.hue)
        self.assertEqual(10, state.saturation)

    async def test_should_set_color_temperature(self):
        await self._device.on()
        await self._device.set_color_temperature(2780)
        state = value_or_raise(await self._device.get_state())
        self.assertEqual(2780, state.color_temp)

    async def test_should_set_light_effect(self):
        await self._device.on()
        await self._device.set_light_effect(LightEffect.christmas_light())
        state = value_or_raise(await self._device.get_state())
        self.assertEqual(LightEffect.christmas_light().name, state.lighting_effect.name)
        self.assertEqual(LightEffect.christmas_light().enable, state.lighting_effect.enable)
