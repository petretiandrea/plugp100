import unittest

from plugp100.api.hub.hub_device import HubDevice
from plugp100.api.hub.t31x_device import T31Device
from plugp100.api.tapo_client import TapoClient
from plugp100.responses.hub_childs.t31x_device_state import TemperatureUnit
from tests.tapo_test_helper import (
    get_test_config,
    get_initialized_client,
)

unittest.TestLoader.sortTestMethodsUsing = staticmethod(lambda x, y: -1)


class SensorT310Test(unittest.IsolatedAsyncioTestCase):
    _hub = None
    _device = None
    _api = None

    async def asyncSetUp(self) -> None:
        credential, ip = await get_test_config(device_type="hub")
        self._api = await get_initialized_client(credential, ip)
        self._hub = HubDevice(self._api)
        self._device = T31Device(
            self._hub,
            (await self._hub.get_children()).get_or_raise().find_device("T310").pop(),
        )

    async def asyncTearDown(self):
        await self._api.close()

    async def test_should_get_state(self):
        state = (await self._device.get_device_state()).get_or_raise()
        self.assertIsNotNone(state.parent_device_id)
        self.assertIsNotNone(state.device_id)
        self.assertIsNotNone(state.mac)
        self.assertIsNotNone(state.rssi)
        self.assertIsNotNone(state.model)
        self.assertIsNotNone(state.get_semantic_firmware_version())
        self.assertIsNotNone(state.nickname)
        self.assertIsNotNone(state.current_humidity)
        self.assertIsNotNone(state.current_temperature)
        self.assertIsNotNone(state.current_humidity_exception)
        self.assertIsNotNone(state.current_temperature_exception)
        self.assertIsNotNone(state.current_temperature_exception)
        self.assertIsNotNone(state.report_interval_seconds)
        self.assertEqual(state.temperature_unit, TemperatureUnit.CELSIUS)
        self.assertEqual(state.at_low_battery, False)

    async def test_should_get_temperature_humidity_records(self):
        state = (await self._device.get_temperature_humidity_records()).get_or_raise()
        self.assertTrue(len(state.past24_temperature) > 0)
        self.assertTrue(len(state.past24h_humidity) > 0)
        self.assertTrue(len(state.past24_temperature_exceptions) > 0)
        self.assertTrue(len(state.past24h_humidity_exceptions) > 0)
