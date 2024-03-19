import unittest
from asyncio import sleep

from plugp100.api.light_effect import LightEffect
from plugp100.new.device_factory import connect
from plugp100.new.tapobulb import TapoBulb
from tests.integration.tapo_test_helper import (
    _test_expose_device_info,
    get_test_config,
)


class LedStripTest(unittest.IsolatedAsyncioTestCase):
    _device = None
    _api = None

    async def asyncSetUp(self) -> None:
        config = await get_test_config(device_type="ledstrip")
        self._device: TapoBulb = await connect(config)
        await self._device.update()

    async def asyncTearDown(self):
        await self._device.client.close()

    async def test_expose_device_info(self):
        await _test_expose_device_info(self._device, self)

    # async def test_expose_device_usage_info(self):
    #    state = (await self._device.get_device_usage()).get_or_raise()
    #    await _test_device_usage(state, self)

    async def test_should_turn_on_off(self):
        await self._device.turn_on()
        await self._device.update()
        self.assertEqual(True, self._device.is_on)
        await self._device.turn_off()
        await self._device.update()
        self.assertEqual(False, self._device.is_on)

    async def test_should_set_brightness(self):
        await self._device.turn_on()
        await self._device.set_brightness(40)
        await self._device.update()
        self.assertEqual(40, self._device.brightness)

    async def test_should_set_hue_saturation(self):
        await self._device.turn_on()
        await self._device.set_hue_saturation(120, 10)
        await self._device.update()
        self.assertEqual(120, self._device.hs.hue)
        self.assertEqual(10, self._device.hs.saturation)

    async def test_should_set_color_temperature(self):
        await self._device.turn_on()
        await self._device.set_color_temperature(2780)
        await self._device.update()
        self.assertEqual(2780, self._device.color_temp)

    async def test_should_set_light_effect(self):
        await self._device.turn_on()
        await self._device.set_light_effect(LightEffect.christmas_light())
        await self._device.update()
        self.assertEqual(LightEffect.christmas_light().name, self._device.effect.name)
        self.assertEqual(LightEffect.christmas_light().enable, self._device.effect.enable)

    async def test_should_set_brightness_of_light_effect(self):
        await self._device.turn_on()
        await self._device.set_light_effect(LightEffect.aurora())
        await sleep(2)
        await self._device.set_light_effect_brightness(LightEffect.aurora(), 40)
        await self._device.update()
        self.assertEqual(40, self._device.brightness)
        self.assertEqual(LightEffect.aurora().name, self._device.effect.name)

    async def test_has_components(self):
        state = self._device.components
        self.assertTrue(len(state.as_list()) > 0)
        self.assertTrue(state.has("brightness"))
        self.assertTrue(state.has("color"))
        self.assertTrue(state.has("color_temperature"))
        self.assertTrue(state.has("light_strip_lighting_effect"))
