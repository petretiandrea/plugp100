import unittest

from plugp100.new.device_factory import connect
from plugp100.new.tapoplug import TapoPlug
from tests.integration.tapo_test_helper import (
    _test_expose_device_info,
    get_test_config,
)


class PowerStripTest(unittest.IsolatedAsyncioTestCase):
    _device = None
    _api = None

    async def asyncSetUp(self) -> None:
        connect_config = await get_test_config(device_type="power_strip")
        self._device: TapoPlug = await connect(connect_config)
        await self._device.update()

    async def asyncTearDown(self):
        await self._device.client.close()

    async def test_expose_device_info(self):
        await _test_expose_device_info(self._device, self)

    # async def test_expose_device_usage_info(self):
    #    state = (await self._device.get_device_usage()).get_or_raise()
    #    await _test_device_usage(state, self)

    async def test_should_turn_on_each_socket(self):
        for socket in self._device.sockets:
            await socket.turn_on()

        for socket in self._device.sockets:
            await socket.update()
            self.assertEqual(True, socket.is_on)

    async def test_should_turn_off_each_socket(self):
        for socket in self._device.sockets:
            await socket.turn_off()

        for socket in self._device.sockets:
            await socket.update()
            self.assertEqual(False, socket.is_on)

    async def test_should_expose_sub_info_each_socket(self):
        for socket in self._device.sockets:
            self.assertIsNotNone(socket.nickname)
            self.assertIsNot(socket.nickname, "")
            self.assertIsNotNone(socket.device_id)
            self.assertIsNotNone(socket.parent_device_id)

    async def test_has_components(self):
        components = self._device.components
        self.assertTrue(len(components.as_list()) > 0)
        self.assertTrue(components.has("control_child"))
        self.assertTrue(components.has("child_device"))

    async def test_children_has_components(self):
        for socket in self._device.sockets:
            components = socket.components
            self.assertTrue(len(components.as_list()) > 0)
