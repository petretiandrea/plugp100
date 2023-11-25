import functools
import unittest
import typing

import yaml

from plugp100.common.credentials import AuthCredential
from plugp100.responses.device_state import DeviceInfo
from plugp100.responses.device_usage_info import DeviceUsageInfo
from plugp100.api.tapo_client import TapoClient


async def _test_expose_device_info(device_info: DeviceInfo, test: unittest.TestCase):
    state = device_info
    test.assertIsNotNone(state.device_id)
    test.assertIsNotNone(state.mac)
    test.assertIsNotNone(state.rssi)
    test.assertIsNotNone(state.model)
    test.assertIsNotNone(state.get_semantic_firmware_version())
    test.assertIsNotNone(state.nickname)
    test.assertIsNot(state.friendly_name, "")
    test.assertIsNotNone(state.overheated)
    test.assertIsNotNone(state.signal_level)
    test.assertIsNotNone(state.type)


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


async def get_test_config(device_type: DeviceType) -> (AuthCredential, str):
    config = _load_file("../../.local.devices.yml")
    username = config["credentials"]["username"]
    password = config["credentials"]["password"]
    ip = config["devices"][device_type]
    return AuthCredential(username, password), ip


async def get_initialized_client(credential: AuthCredential, ip: str) -> TapoClient:
    client = TapoClient.create(credential, ip)
    await client.initialize()
    return client


@functools.cache
def _load_file(file_name: str):
    with open(file_name, "r") as config_file:
        return yaml.safe_load(config_file)
