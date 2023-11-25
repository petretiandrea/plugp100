import unittest

from plugp100.api.power_strip_device import PowerStripDevice
from tests.integration.tapo_test_helper import (
    _test_expose_device_info,
    get_test_config,
    _test_device_usage,
    get_initialized_client,
)


class PowerStripTest(unittest.IsolatedAsyncioTestCase):
    _device = None
    _api = None

    async def asyncSetUp(self) -> None:
        credential, ip = await get_test_config(device_type="power_strip")
        self._api = await get_initialized_client(credential, ip)
        self._device = PowerStripDevice(self._api)

    async def asyncTearDown(self):
        await self._api.close()

    async def test_expose_device_info(self):
        state = (await self._device.get_state()).get_or_raise().info
        await _test_expose_device_info(state, self)

    async def test_expose_device_usage_info(self):
        state = (await self._device.get_device_usage()).get_or_raise()
        await _test_device_usage(state, self)

    async def test_should_turn_on_each_socket(self):
        children = (await self._device.get_children()).get_or_raise()
        for socket_id, socket in children.items():
            await self._device.on(socket_id)

        children = (await self._device.get_children()).get_or_raise()
        for socket_id, socket in children.items():
            self.assertEqual(True, socket.device_on)

    async def test_should_turn_off_each_socket(self):
        children = (await self._device.get_children()).get_or_raise()
        for socket_id, _ in children.items():
            await self._device.off(socket_id)

        children = (await self._device.get_children()).get_or_raise()
        for _, socket in children.items():
            self.assertEqual(False, socket.device_on)

    async def test_should_expose_sub_info_each_socket(self):
        children = (await self._device.get_children()).get_or_raise()
        for _, socket in children.items():
            self.assertIsNotNone(socket.nickname)
            self.assertIsNot(socket.nickname, "")
            self.assertIsNotNone(socket.device_id)
            self.assertIsNotNone(socket.original_device_id)
