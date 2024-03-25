import unittest

from plugp100.new.device_factory import connect
from tests.integration.tapo_test_helper import (
    _test_expose_device_info,
    get_test_config,
    _test_device_usage,
)


class PlugTest(unittest.IsolatedAsyncioTestCase):
    _device = None
    _api = None

    async def asyncSetUp(self) -> None:
        config = await get_test_config(device_type="plug")
        self._device = await connect(config)

    async def asyncTearDown(self):
        await self._api.close()

    async def test_expose_device_info(self):
        await _test_expose_device_info(self._device, self)

    async def test_expose_device_usage_info(self):
        state = (await self._device.get_device_usage()).get_or_raise()
        await _test_device_usage(state, self)

    async def test_should_turn_on(self):
        await self._device.on()
        state = (await self._device.get_state()).get_or_raise()
        self.assertEqual(True, state.device_on)

    async def test_should_turn_off(self):
        await self._device.off()
        state = (await self._device.get_state()).get_or_raise()
        self.assertEqual(False, state.device_on)

    async def test_has_components(self):
        state = (await self._device.get_component_negotiation()).get_or_raise()
        self.assertTrue(len(state.as_list()) > 0)
