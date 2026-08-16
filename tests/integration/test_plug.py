import unittest

from plugp100.devices.factory import connect
from plugp100.devices.plug import TapoPlug
from tests.integration.tapo_test_helper import _test_expose_device_info, get_test_config


class PlugTest(unittest.IsolatedAsyncioTestCase):
    _device = None
    _api = None

    async def asyncSetUp(self) -> None:
        config = await get_test_config(device_type="plug")
        self._device: TapoPlug = await connect(config)
        await self._device.update()

    async def asyncTearDown(self):
        await self._device.client.close()

    async def test_expose_device_info(self):
        await _test_expose_device_info(self._device, self)

    async def test_should_turn_on(self):
        await self._device.turn_on()
        await self._device.update()
        self.assertEqual(True, self._device.is_on)

    async def test_should_turn_off(self):
        await self._device.turn_off()
        await self._device.update()
        self.assertEqual(False, self._device.is_on)

    async def test_has_components(self):
        state = self._device.components
        self.assertTrue(len(state.as_list()) > 0)
