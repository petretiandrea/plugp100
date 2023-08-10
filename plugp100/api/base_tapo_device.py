from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.either import Either
from plugp100.common.utils.json_utils import Json
from plugp100.requests.tapo_request import TapoRequest
from plugp100.responses.device_usage_info import DeviceUsageInfo


class _BaseTapoDevice:

    def __init__(self, api: TapoClient, address: str):
        self._api = api
        self._address = address

    async def login(self) -> Either[True, Exception]:
        """
        The function `login` attempts to log in to an API using a given address and returns either `True` if successful or
        an `Exception` if there is an error.
        @return: The login method is returning an Either type, which can either be True or an Exception.
        """
        login_result = await self._api.login(self._address, use_v2=False)
        if login_result.is_left():
            return await self._api.login(self._address, use_v2=True)
        return login_result

    async def get_device_usage(self) -> Either[DeviceUsageInfo, Exception]:
        return (await self._api.execute_raw_request(TapoRequest(method="get_device_usage", params=None))) | \
               DeviceUsageInfo.try_from_json

    async def get_state_as_json(self) -> Either[Json, Exception]:
        return await self._api.get_device_info()
