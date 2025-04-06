import functools
import typing
import unittest

import yaml

from plugp100.common.credentials import AuthCredential
from plugp100.new.device_factory import DeviceConnectConfiguration
from plugp100.new.tapodevice import TapoDevice
from plugp100.responses.device_usage_info import DeviceUsageInfo


async def _test_expose_device_info(device: TapoDevice, test: unittest.TestCase):
    test.assertIsNotNone(device.device_id)
    test.assertIsNotNone(device.mac)
    test.assertIsNotNone(device.wifi_info.rssi)
    test.assertIsNotNone(device.model)
    test.assertIsNotNone(device.firmware_version)
    test.assertIsNotNone(device.nickname)
    test.assertIsNotNone(device.overheated)
    test.assertIsNotNone(device.wifi_info.signal_level)
    test.assertIsNotNone(device.device_type)


async def _test_device_usage(device_usage: DeviceUsageInfo, test: unittest.TestCase):
    state = device_usage
    test.assertIsNotNone(state.time_usage.today)
    test.assertIsNotNone(state.time_usage.past7_days)
    test.assertIsNotNone(state.time_usage.past30_days)
    test.assertIsNotNone(state.power_usage.today)
    test.assertIsNotNone(state.power_usage.past7_days)
    test.assertIsNotNone(state.power_usage.past30_days)
    test.assertIsNotNone(state.saved_power.today)
    test.assertIsNotNone(state.saved_power.past7_days)
    test.assertIsNotNone(state.saved_power.past30_days)


DeviceType = typing.Union["light", "ledstrip", "plug", "hub", "power_strip"]


async def get_test_config(device_type: DeviceType) -> DeviceConnectConfiguration:
    config = _load_file("../../.local.devices.yml")
    username = config["credentials"]["username"]
    password = config["credentials"]["password"]
    ip = config["devices"][device_type]
    return DeviceConnectConfiguration(
        host=ip, credentials=AuthCredential(username, password)
    )


@functools.cache
def _load_file(file_name: str):
    with open(file_name, "r") as config_file:
        return yaml.safe_load(config_file)
