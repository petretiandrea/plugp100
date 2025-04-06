import asyncio
import unittest

from plugp100.new.device_factory import connect
from plugp100.new.tapohub import TapoHub
from tests.integration.tapo_test_helper import (
    _test_expose_device_info,
    get_test_config,
)

unittest.TestLoader.sortTestMethodsUsing = staticmethod(lambda x, y: -1)


class HubTest(unittest.IsolatedAsyncioTestCase):
    _device = None
    _api = None

    async def asyncSetUp(self) -> None:
        config = await get_test_config(device_type="hub")
        self._device: TapoHub = await connect(config)
        await self._device.update()

    async def asyncTearDown(self):
        await self._device.client.close()

    async def test_expose_device_info(self):
        await _test_expose_device_info(self._device, self)

    # async def test_expose_device_usage_info(self):
    #    state = (await self._device.get_device_usage()).get_or_raise()
    #    await _test_device_usage(state, self)

    async def test_should_turn_siren_on(self):
        await self._device.turn_alarm_on()
        await self._device.update()
        self.assertEqual(True, self._device.is_alarm_on)

    async def test_should_turn_siren_off(self):
        await self._device.turn_alarm_off()
        await self._device.update()
        self.assertEqual(False, self._device.is_alarm_on)

    async def test_should_get_supported_alarm_tones(self):
        await self._device.turn_alarm_off()
        state = (await self._device.get_supported_alarm_tones()).get_or_raise()
        self.assertTrue(len(state.tones) > 0)

    async def test_should_get_children(self):
        self.assertTrue(len(self._device.children) > 0)

    async def test_should_get_base_children_info(self):
        for child in self._device.children:
            self.assertIsNotNone(child.device_id)

    async def test_should_subscribe_to_association_changes(self):
        unsub = self._device.subscribe_device_association(lambda x: print(x))
        await asyncio.sleep(10)
        unsub()

    async def test_has_components(self):
        state = self._device.components
        self.assertTrue(len(state.as_list()) > 0)
        self.assertTrue(state.has("child_device"))
        self.assertTrue(state.has("control_child"))
        self.assertTrue(state.has("alarm"))

    async def test_children_has_components(self):
        for child in self._device.children:
            self.assertTrue(len(child.components.as_list()) > 0)
