import unittest

from plugp100.api.power_strip_device import PowerStripDevice
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.either import value_or_raise
from tests.tapo_test_helper import _test_expose_device_info, get_test_config, _test_device_usage


class PowerStripTest(unittest.IsolatedAsyncioTestCase):
    _device = None
    _api = None

    async def asyncSetUp(self) -> None:
        username, password, ip = await get_test_config(device_type="power_strip")
        self._api = TapoClient(username, password)
        self._device = PowerStripDevice(self._api, ip)
        await self._device.login()

    async def asyncTearDown(self):
        await self._api.close()

    async def test_expose_device_info(self):
        state = value_or_raise(await self._device.get_state()).info
        await _test_expose_device_info(state, self)

    async def test_expose_device_usage_info(self):
        state = value_or_raise(await self._device.get_device_usage())
        await _test_device_usage(state, self)

    async def test_should_turn_on_each_socket(self):
        children = value_or_raise(await self._device.get_children())
        for socket_id, socket in children.items():
            await self._device.on(socket_id)

        children = value_or_raise((await self._device.get_children()))
        for socket_id, socket in children.items():
            self.assertEqual(True, socket.device_on)

    async def test_should_turn_off_each_socket(self):
        children = value_or_raise(await self._device.get_children())
        for socket_id, _ in children.items():
            await self._device.off(socket_id)

        children = value_or_raise((await self._device.get_children()))
        for _, socket in children.items():
            self.assertEqual(False, socket.device_on)

    async def test_should_expose_sub_info_each_socket(self):
        children = value_or_raise((await self._device.get_children()))
        for _, socket in children.items():
            self.assertIsNotNone(socket.nickname)
            self.assertIsNot(socket.nickname, '')
            self.assertIsNotNone(socket.device_id)
            self.assertIsNotNone(socket.original_device_id)
