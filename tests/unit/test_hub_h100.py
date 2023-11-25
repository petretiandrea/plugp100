import unittest
from functools import reduce
from unittest.mock import AsyncMock

from plugp100.api.hub.hub_device import HubDevice
from plugp100.api.tapo_client import TapoClient
from plugp100.common.credentials import AuthCredential
from plugp100.protocol.tapo_protocol import TapoProtocol
from tests.unit.test_utils import wrap_as_tapo_response, generate_random_children


class HubH100Test(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self._mock_protocol = AsyncMock(TapoProtocol)
        api = TapoClient(
            auth_credential=AuthCredential("", ""), url="", protocol=self._mock_protocol
        )
        self.hub = HubDevice(api=api, subscription_polling_interval_millis=1000)

    async def asyncTearDown(self):
        self._mock_protocol.reset_mock()

    async def test_should_get_all_children(self):
        children = generate_random_children(10, 55)
        self._mock_protocol.send_request.side_effect = [
            wrap_as_tapo_response(it) for it in children
        ]

        expected = reduce(lambda x, y: x.merge(y), children)
        state = (await self.hub.get_children()).get_or_raise()
        self.assertListEqual(state.child_device_list, expected.child_device_list)
