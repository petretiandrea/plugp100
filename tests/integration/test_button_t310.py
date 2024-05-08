import unittest

from plugp100.new.child.tapohubchildren import TemperatureHumiditySensor
from plugp100.new.device_factory import connect
from plugp100.new.tapohub import TapoHub
from plugp100.responses.temperature_unit import TemperatureUnit
from tests.integration.tapo_test_helper import (
    get_test_config,
)

unittest.TestLoader.sortTestMethodsUsing = staticmethod(lambda x, y: -1)


class SensorT310Test(unittest.IsolatedAsyncioTestCase):
    _hub = None
    _device = None
    _api = None

    async def asyncSetUp(self) -> None:
        config = await get_test_config(device_type="hub")
        self._hub: TapoHub = await connect(config)
        await self._hub.update()
        self._device: TemperatureHumiditySensor = self._hub.find_child_device_by_model(
            "T310"
        )
        await self._device.update()

    async def asyncTearDown(self):
        await self._hub.client.close()

    async def test_should_get_state(self):
        self.assertIsNotNone(self._device.parent_device_id)
        self.assertIsNotNone(self._device.device_id)
        self.assertIsNotNone(self._device.mac)
        self.assertIsNotNone(self._device.wifi_info.rssi)
        self.assertIsNotNone(self._device.model)
        self.assertIsNotNone(self._device.firmware_version)
        self.assertIsNotNone(self._device.nickname)
        self.assertIsNotNone(self._device.current_humidity)
        self.assertIsNotNone(self._device.current_temperature)
        self.assertIsNotNone(self._device.current_humidity)
        self.assertIsNotNone(self._device.current_humidity_error)
        self.assertIsNotNone(self._device.current_temperature_error)
        self.assertIsNotNone(self._device.report_interval_seconds)
        self.assertEqual(self._device.temperature_unit, TemperatureUnit.CELSIUS)
        self.assertEqual(self._device.battery_low, False)

    async def test_should_get_temperature_humidity_records(self):
        state = (await self._device.get_temperature_humidity_records()).get_or_raise()
        self.assertTrue(len(state.past24_temperature) > 0)
        self.assertTrue(len(state.past24h_humidity) > 0)
        self.assertTrue(len(state.past24_temperature_exceptions) > 0)
        self.assertTrue(len(state.past24h_humidity_exceptions) > 0)

    async def test_has_components(self):
        state = self._device.components
        self.assertTrue(len(state.as_list()) > 0)
        self.assertTrue(state.has("humidity"))
        self.assertTrue(state.has("temperature"))
        self.assertTrue(state.has("temp_humidity_record"))
        self.assertTrue(state.has("comfort_temperature"))
        self.assertTrue(state.has("comfort_humidity"))
        self.assertTrue(state.has("battery_detect"))
