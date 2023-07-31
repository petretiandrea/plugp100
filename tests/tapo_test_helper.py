import functools
import unittest
import typing

import yaml

from plugp100.responses.device_state import DeviceInfo


async def _test_expose_device_info(device_info: DeviceInfo, test: unittest.TestCase):
    state = device_info
    test.assertIsNotNone(state.device_id)
    test.assertIsNotNone(state.mac)
    test.assertIsNotNone(state.rssi)
    test.assertIsNotNone(state.model)
    test.assertIsNotNone(state.get_semantic_firmware_version())
    test.assertIsNotNone(state.nickname)
    test.assertIsNotNone(state.overheated)
    test.assertIsNotNone(state.signal_level)
    test.assertIsNotNone(state.type)


DeviceType = typing.Union['light', 'ledstrip', 'plug', 'hub']


async def get_test_config(device_type: DeviceType) -> (str, str, str):
    config = _load_file("../.local.devices.yml")
    username = config['credentials']['username']
    password = config['credentials']['password']
    ip = config['devices'][device_type]
    return username, password, ip


@functools.cache
def _load_file(file_name: str):
    with open(file_name, 'r') as config_file:
        return yaml.safe_load(config_file)
