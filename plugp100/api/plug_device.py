from plugp100.api.tapo_client import TapoClient, Json
from plugp100.responses.device_state import PlugDeviceState
from plugp100.common.functional.either import Either
from plugp100.requests.set_device_info.set_plug_info_params import SetPlugInfoParams
from plugp100.responses.energy_info import EnergyInfo
from plugp100.responses.power_info import PowerInfo


class PlugDevice:

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

    async def on(self) -> Either[True, Exception]:
        """
        The function `on` sets the device info to True using the `SetPlugInfoParams` class.
        @return: an instance of the `Either` class, which can hold either a `True` value or an `Exception` object.
        """
        return await self._api.set_device_info(SetPlugInfoParams(True))

    async def off(self) -> Either[True, Exception]:
        """
        The function `off` sets the device info to False using the `SetPlugInfoParams` class.
        @return: an `Either` object, which can either be `True` or an `Exception`.
        """
        return await self._api.set_device_info(SetPlugInfoParams(False))

    async def get_energy_usage(self) -> Either[EnergyInfo, Exception]:
        """
        The function `get_energy_usage` asynchronously retrieves energy usage information from an API and returns it as an
        `EnergyInfo` object, or returns an `Exception` if an error occurs.
        @return: an `Either` type, which can either be an `EnergyInfo` object or an `Exception` object.
        """
        return await self._api.get_energy_usage()

    async def get_current_power(self) -> Either[PowerInfo, Exception]:
        """
        The function `get_current_power` asynchronously retrieves the current power information using an API and returns
        either the power information or an exception.
        @return: an instance of the `Either` class, which can contain either a `PowerInfo` object or an `Exception` object.
        """
        return await self._api.get_current_power()

    async def get_state_as_json(self) -> Either[Json, Exception]:
        return await self._api.get_device_info()
