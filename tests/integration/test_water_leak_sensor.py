import unittest

from plugp100.new.tapohub import TapoHub
from tests.integration.tapo_test_helper import (
    get_test_config,
    get_initialized_client,
)

unittest.TestLoader.sortTestMethodsUsing = staticmethod(lambda x, y: -1)


class WaterLeakSensorTest(unittest.IsolatedAsyncioTestCase):
    _hub = None
    _device = None
    _api = None

    async def asyncSetUp(self) -> None:
        credential, ip = await get_test_config(device_type="hub")
        self._api = await get_initialized_client(credential, ip)
        self._hub = TapoHub("", 80, self._api)
        await self._hub.update()
        self._device = filter(lambda x: "p300" in x.model, self._hub.children)

    async def asyncTearDown(self):
        await self._api.close()

    async def test_should_get_state(self):
        state = (await self._device.get_device_state()).get_or_raise()
        self.assertIsNotNone(state.base_info.parent_device_id)
        self.assertIsNotNone(state.base_info.device_id)
        self.assertIsNotNone(state.base_info.mac)
        self.assertIsNotNone(state.base_info.rssi)
        self.assertIsNotNone(state.base_info.model)
        self.assertIsNotNone(state.base_info.get_semantic_firmware_version())
        self.assertIsNotNone(state.base_info.nickname)
        self.assertIsNotNone(state.report_interval_seconds)
        self.assertEqual(state.base_info.at_low_battery, False)
        self.assertEqual(state.base_info.status, "online")
