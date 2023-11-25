import unittest
from asyncio import sleep

from plugp100.api.ledstrip_device import LedStripDevice
from plugp100.api.light_effect import LightEffect
from tests.integration.tapo_test_helper import (
    _test_expose_device_info,
    get_test_config,
    _test_device_usage,
    get_initialized_client,
)


class LedStripTest(unittest.IsolatedAsyncioTestCase):
    _device = None
    _api = None

    async def asyncSetUp(self) -> None:
        credential, ip = await get_test_config(device_type="ledstrip")
        self._api = await get_initialized_client(credential, ip)
        self._device = LedStripDevice(self._api)

    async def asyncTearDown(self):
        await self._api.close()

    async def test_expose_device_info(self):
        state = (await self._device.get_state()).get_or_raise().info
        await _test_expose_device_info(state, self)

    async def test_expose_device_usage_info(self):
        state = (await self._device.get_device_usage()).get_or_raise()
        await _test_device_usage(state, self)

    async def test_should_turn_on_off(self):
        await self._device.on()
        state = (await self._device.get_state()).get_or_raise()
        self.assertEqual(True, state.device_on)
        await self._device.off()
        state = (await self._device.get_state()).get_or_raise()
        self.assertEqual(False, state.device_on)

    async def test_should_set_brightness(self):
        await self._device.on()
        await self._device.set_brightness(40)
        state = (await self._device.get_state()).get_or_raise()
        self.assertEqual(40, state.brightness)

    async def test_should_set_hue_saturation(self):
        await self._device.on()
        await self._device.set_hue_saturation(120, 10)
        state = (await self._device.get_state()).get_or_raise()
        self.assertEqual(120, state.hue)
        self.assertEqual(10, state.saturation)

    async def test_should_set_color_temperature(self):
        await self._device.on()
        await self._device.set_color_temperature(2780)
        state = (await self._device.get_state()).get_or_raise()
        self.assertEqual(2780, state.color_temp)

    async def test_should_set_light_effect(self):
        await self._device.on()
        await self._device.set_light_effect(LightEffect.christmas_light())
        state = (await self._device.get_state()).get_or_raise()
        self.assertEqual(LightEffect.christmas_light().name, state.lighting_effect.name)
        self.assertEqual(
            LightEffect.christmas_light().enable, state.lighting_effect.enable
        )

    async def test_should_set_brightness_of_light_effect(self):
        await self._device.on()
        await self._device.set_light_effect(LightEffect.aurora())
        await sleep(2)
        await self._device.set_light_effect_brightness(LightEffect.aurora(), 40)
        state = (await self._device.get_state()).get_or_raise()
        self.assertEqual(40, state.brightness)
        self.assertEqual(LightEffect.aurora().name, state.lighting_effect.name)
