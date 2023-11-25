import json
import unittest
from unittest.mock import AsyncMock

from plugp100.api.hub.hub_device import HubDevice
from plugp100.api.hub.ke100_device import KE100Device
from plugp100.common.functional.tri import Try
from plugp100.responses.hub_childs.ke100_device_state import TRVState
from plugp100.responses.temperature_unit import TemperatureUnit

hub = AsyncMock(HubDevice)
device_id = "38018301SAS1234ZAD"
ke100_device = KE100Device(hub=hub, device_id=device_id)
device_info = json.loads(
    """
        {
        "trv_states": ["heating"], 
        "device_id": "38018301SAS1234ZAD", 
        "mac": "11AA22BB33CC", 
        "hw_ver": "1.0", 
        "fw_ver": "2.6.0", 
        "type": "SMART.KASAENERGY", 
        "model": "KE100", 
        "hw_id": "3801AABBCCDDEE", 
        "oem_id": "0836ABBU2MCKSA", 
        "specs": "UK", 
        "category": "subg.trv", 
        "bind_count": 1, 
        "status": "online", 
        "lastOnboardingTimestamp": 313213142, 
        "rssi": -67, 
        "signal_level": 3, 
        "jamming_rssi": -117, 
        "jamming_signal_level": 1, 
        "temp_unit": "celsius", 
        "current_temp": 20.5, 
        "target_temp": 27.5,
        "temp_offset": 0, 
        "min_control_temp": 5, 
        "max_control_temp": 30, 
        "frost_protection_on": false, 
        "at_low_battery": false, 
        "battery_percentage": 100, 
        "parent_device_id": "77JJAYBSKD83BBCC", 
        "nickname": "bXktbmFtZQ==", 
        "location": "",
        "avatar": "kasa_trv", 
        "child_protection": false, 
        "region": "Europe/London"}
    """
)


class TRVKE100Test(unittest.IsolatedAsyncioTestCase):
    async def test_should_get_state(self):
        hub.control_child.return_value = Try.of(device_info)
        state = (await ke100_device.get_device_state()).get_or_raise()
        self.assertEqual(state.base_info.parent_device_id, "77JJAYBSKD83BBCC")
        self.assertEqual(state.base_info.device_id, device_id)
        self.assertEqual(state.base_info.mac, "11AA22BB33CC")
        self.assertEqual(state.base_info.rssi, -67)
        self.assertEqual(state.base_info.model, "KE100")
        self.assertEqual(state.base_info.status, "online")
        self.assertIsNotNone(state.base_info.get_semantic_firmware_version())
        self.assertEqual(state.base_info.nickname, "my-name")
        self.assertEqual(state.current_temperature, 20.5)
        self.assertEqual(state.target_temperature, 27.5)
        self.assertEqual(state.temperature_offset, 0)
        self.assertEqual(state.min_control_temperature, 5)
        self.assertEqual(state.max_control_temperature, 30)
        self.assertEqual(state.battery_percentage, 100)
        self.assertEqual(state.min_control_temperature, 5)
        self.assertEqual(state.frost_protection_on, False)
        self.assertEqual(state.trv_state, TRVState.HEATING)
        self.assertEqual(state.temperature_unit, TemperatureUnit.CELSIUS)
        self.assertEqual(state.base_info.at_low_battery, False)

    async def test_should_set_target_temp(self):
        result = (await ke100_device.set_target_temp({"temperature": 24})).get_or_raise()
        call_args = hub.control_child.call_args

        self.assertEqual(call_args[0][0], device_id)
        self.assertEqual(call_args[0][1].params, {"target_temp": 24})
        self.assertTrue(result)

    async def test_should_set_temp_offset(self):
        result = (await ke100_device.set_temp_offset(-5)).get_or_raise()
        call_args = hub.control_child.call_args

        self.assertEqual(call_args[0][0], device_id)
        self.assertEqual(call_args[0][1].params, {"temp_offset": -5})
        self.assertTrue(result)

    async def test_should_set_frost_protection_on(self):
        result = (await ke100_device.set_frost_protection_on()).get_or_raise()
        call_args = hub.control_child.call_args

        self.assertEqual(call_args[0][0], device_id)
        self.assertEqual(call_args[0][1].params, {"frost_protection_on": True})
        self.assertTrue(result)

    async def test_should_set_frost_protection_off(self):
        result = (await ke100_device.set_frost_protection_off()).get_or_raise()
        call_args = hub.control_child.call_args

        self.assertEqual(call_args[0][0], device_id)
        self.assertEqual(call_args[0][1].params, {"frost_protection_on": False})
        self.assertTrue(result)

    async def test_should_set_child_protection_on(self):
        result = (await ke100_device.set_child_protection_on()).get_or_raise()
        call_args = hub.control_child.call_args

        self.assertEqual(call_args[0][0], device_id)
        self.assertEqual(call_args[0][1].params, {"child_protection": True})
        self.assertTrue(result)

    async def test_should_set_child_protection_off(self):
        result = (await ke100_device.set_child_protection_off()).get_or_raise()
        call_args = hub.control_child.call_args

        self.assertEqual(call_args[0][0], device_id)
        self.assertEqual(call_args[0][1].params, {"child_protection": False})
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
