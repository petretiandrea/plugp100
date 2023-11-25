import asyncio
import unittest

from plugp100.api.hub.hub_child_device import create_hub_child_device
from plugp100.api.hub.hub_device import HubDevice
from plugp100.responses.hub_childs.s200b_device_state import (
    SingleClickEvent,
    RotationEvent,
)
from tests.integration.tapo_test_helper import (
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
        self._device = create_hub_child_device(
            self._hub,
            (await self._hub.get_children()).get_or_raise().find_device("S200B"),
        )

    async def asyncTearDown(self):
        await self._api.close()

    async def test_should_get_state(self):
        state = (await self._device.get_device_info()).get_or_raise()
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
        unsub = self._device.subscribe_event_logs(lambda event: print(event))
        await asyncio.sleep(60)
        unsub()
