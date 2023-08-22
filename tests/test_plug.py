import unittest

from plugp100.api.plug_device import PlugDevice
from plugp100.api.tapo_client import TapoClient
from tests.tapo_test_helper import (
    _test_expose_device_info,
    get_test_config,
    _test_device_usage,
)


class PlugTest(unittest.IsolatedAsyncioTestCase):
    _device = None
    _api = None

    async def asyncSetUp(self) -> None:
        username, password, ip = await get_test_config(device_type="plug")
        self._api = TapoClient(username, password)
        self._device = PlugDevice(self._api, ip)
        await self._device.login()

    async def asyncTearDown(self):
        await self._api.close()

    async def test_expose_device_info(self):
        state = (await self._device.get_state()).get_or_raise().info
        await _test_expose_device_info(state, self)

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
