import unittest

from plugp100.api.hub.hub_device import HubDevice
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.either import value_or_raise
from tests.tapo_test_helper import _test_expose_device_info, get_test_config

unittest.TestLoader.sortTestMethodsUsing = staticmethod(lambda x, y: -1)


class HubTest(unittest.IsolatedAsyncioTestCase):
    _device = None
    _api = None

    async def asyncSetUp(self) -> None:
        username, password, ip = await get_test_config(device_type="hub")
        self._api = TapoClient(username, password)
        self._device = HubDevice(self._api, ip)
        await self._device.login()

    async def asyncTearDown(self):
        await self._api.close()

    async def test_expose_device_info(self):
        state = value_or_raise(await self._device.get_state()).info
        await _test_expose_device_info(state, self)

    async def test_should_turn_siren_on(self):
        await self._device.turn_alarm_on()
        state = value_or_raise(await self._device.get_state())
        self.assertEqual(True, state.in_alarm)

    async def test_should_turn_siren_off(self):
        await self._device.turn_alarm_off()
        state = value_or_raise(await self._device.get_state())
        self.assertEqual(False, state.in_alarm)

    async def test_should_get_supported_alarm_tones(self):
        await self._device.turn_alarm_off()
        state = value_or_raise(await self._device.get_supported_alarm_tones())
        self.assertTrue(len(state.tones) > 0)

    async def test_should_get_children(self):
        state = value_or_raise(await self._device.get_children())
        self.assertTrue(len(state.get_device_ids()) > 0)
