from plugp100.api.tapo_client import TapoClient, Json
from plugp100.common.functional.either import Either
from plugp100.common.utils.json_utils import dataclass_encode_json
from plugp100.requests.set_device_info.set_plug_info_params import SetPlugInfoParams
from plugp100.requests.tapo_request import TapoRequest
from plugp100.responses.child_device_list import ChildDeviceList
from plugp100.responses.device_state import PlugDeviceState


class PowerStripDevice:

    def __init__(self, api: TapoClient, address: str):
        self._api = api
        self._address = address

    async def login(self) -> Either[True, Exception]:
        """
        The function `login` attempts to log in to an API using a given address and returns either `True` if successful or
        an `Exception` if there is an error.
        @return: The login method is returning an Either type, which can either be True or an Exception.
        """
        return await self._api.login(self._address)

    async def get_state(self) -> Either[PlugDeviceState, Exception]:
        """
        The function `get_state` asynchronously retrieves device information and returns either the device state or an
        exception.
        @return: an instance of the `Either` class, which can hold either a `PlugDeviceState` object or an `Exception`
        object.
        """
        return (await self._api.get_device_info()) | PlugDeviceState.try_from_json

    async def off(self) -> Either[True, Exception]:
        """
        The function `off` sets the device info to False using the `SetPlugInfoParams` class.
        @return: an `Either` object, which can either be `True` or an `Exception`.
        """
        return await self._api.set_device_info(SetPlugInfoParams(False))

    async def get_children(self) -> Either[ChildDeviceList, Exception]:
        return await self._api.get_child_device_list()

    async def on(self, device_id: str):
        request = dataclass_encode_json(SetPlugInfoParams(device_on=False))
        return await self._control_child(device_id, request)

    async def _control_child(self, device_id: str, request: TapoRequest) -> Either[Json, Exception]:
        return await self._api.control_child(device_id, request)

    async def get_state_as_json(self) -> Either[Json, Exception]:
        return await self._api.get_device_info()
