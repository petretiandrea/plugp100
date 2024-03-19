import asyncio
import unittest

from plugp100.new.device_factory import connect
from plugp100.new.event_polling.event_subscription import EventSubscriptionOptions
from plugp100.new.tapohub import TapoHub, S200ButtonDevice
from plugp100.responses.hub_childs.s200b_device_state import (
    SingleClickEvent,
    RotationEvent,
)
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
        self._device: S200ButtonDevice = self._hub.find_child_device_by_model("S200B")
        await self._device.update()

    async def asyncTearDown(self):
        await self._hub.client.close()

    async def test_should_get_state(self):
        self.assertIsNotNone(self._device.parent_device_id)
        self.assertIsNotNone(self._device.device_id)
        self.assertIsNotNone(self._device.mac)
        self.assertIsNotNone(self._device.rssi)
        self.assertIsNotNone(self._device.model)
        self.assertIsNotNone(self._device.firmware_version)
        self.assertIsNotNone(self._device.nickname)
        self.assertIsNotNone(self._device.report_interval_seconds)
        self.assertEqual(self._device.battery_low, False)

    async def test_should_get_button_events(self):
        logs = (await self._device.get_event_logs(100)).get_or_raise()
        single_click_logs = list(
            filter(lambda x: isinstance(x, SingleClickEvent), logs.events)
        )
        rotation_logs = list(filter(lambda x: isinstance(x, RotationEvent), logs.events))
        self.assertEqual(len(logs.events), logs.size)
        self.assertTrue(len(single_click_logs) > 0)
        self.assertIsNotNone(single_click_logs[0].id)
        self.assertIsNotNone(single_click_logs[0].timestamp)
        self.assertTrue(len(rotation_logs) > 0)
        self.assertIsNotNone(rotation_logs[0].id)
        self.assertIsNotNone(rotation_logs[0].degrees)
        self.assertIsNotNone(rotation_logs[0].timestamp)

    async def test_should_poll_button_events(self):
        unsub = self._device.subscribe_event_logs(
            lambda event: print(event), EventSubscriptionOptions(2000, 500)
        )
        await asyncio.sleep(60)
        unsub()

    async def test_has_components(self):
        state = self._device.components
        self.assertTrue(len(state.as_list()) > 0)
        self.assertTrue(state.has("trigger_log"))
        self.assertTrue(state.has("battery_detect"))
        self.assertTrue(state.has("double_click"))
