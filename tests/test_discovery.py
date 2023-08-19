import unittest

from plugp100.api.plug_device import PlugDevice
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.either import value_or_raise
from plugp100.discovery.tapo_discovery import TapoDiscovery
from tests.tapo_test_helper import _test_expose_device_info, get_test_config, _test_device_usage, get_test_credentials


class DiscoveryTest(unittest.IsolatedAsyncioTestCase):
    _discovery = None

    async def asyncSetUp(self) -> None:
        self._discovery = TapoDiscovery()

    async def test_should_discovery_by_cloud(self):
        username, password = await get_test_credentials()
        devices = await self._discovery.discovery_cloud(username, password)
        print(devices)

