import asyncio
import unittest

from plugp100.api.hub.hub_device import HubDevice
from tests.integration.tapo_test_helper import (
    _test_expose_device_info,
    get_test_config,
    _test_device_usage,
    get_initialized_client,
)

unittest.TestLoader.sortTestMethodsUsing = staticmethod(lambda x, y: -1)


class HubTest(unittest.IsolatedAsyncioTestCase):
    _device = None
    _api = None

    async def asyncSetUp(self) -> None:
        credential, ip = await get_test_config(device_type="hub")
        self._api = await get_initialized_client(credential, ip)
        self._device = HubDevice(self._api, subscription_polling_interval_millis=5000)

    async def asyncTearDown(self):
        await self._api.close()

    async def test_expose_device_info(self):
        state = (await self._device.get_state()).get_or_raise().info
        await _test_expose_device_info(state, self)

    async def test_expose_device_usage_info(self):
        state = (await self._device.get_device_usage()).get_or_raise()
        await _test_device_usage(state, self)

    async def test_should_turn_siren_on(self):
        await self._device.turn_alarm_on()
        state = (await self._device.get_state()).get_or_raise()
        self.assertEqual(True, state.in_alarm)

    async def test_should_turn_siren_off(self):
        await self._device.turn_alarm_off()
        state = (await self._device.get_state()).get_or_raise()
        self.assertEqual(False, state.in_alarm)

    async def test_should_get_supported_alarm_tones(self):
        await self._device.turn_alarm_off()
        state = (await self._device.get_supported_alarm_tones()).get_or_raise()
        self.assertTrue(len(state.tones) > 0)

    async def test_should_get_children(self):
        state = (await self._device.get_children()).get_or_raise()
        self.assertTrue(len(state.get_device_ids()) > 0)

    async def test_should_get_base_children_info(self):
        children = (
            (await self._device.get_children()).get_or_raise().get_children_base_info()
        )
        self.assertTrue(len(children) > 0)

    async def test_should_subscribe_to_association_changes(self):
        unsub = self._device.subscribe_device_association(lambda x: print(x))
        await asyncio.sleep(10)
        unsub()
