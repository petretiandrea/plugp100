from plugp100.api.base_tapo_device import _BaseTapoDevice
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.tri import Try
from plugp100.requests.set_device_info.set_plug_info_params import SetPlugInfoParams
from plugp100.requests.set_device_info.set_plug_countdown_rule_params  import SetPlugCountdownRuleParams
from plugp100.responses.device_state import PlugDeviceState
from plugp100.responses.energy_info import EnergyInfo
from plugp100.responses.power_info import PowerInfo


class PlugDevice(_BaseTapoDevice):
    def __init__(self, api: TapoClient):
        super().__init__(api)

    async def get_state(self) -> Try[PlugDeviceState]:
        """
        The function `get_state` asynchronously retrieves device information and returns either the device state or an
        exception.
        @return: an instance of the `Either` class, which can hold either a `PlugDeviceState` object or an `Exception`
        object.
        """
        return (await self._api.get_device_info()).flat_map(PlugDeviceState.try_from_json)

    async def on(self) -> Try[bool]:
        """
        The function `on` sets the device info to True using the `SetPlugInfoParams` class.
        @return: an instance of the `Either` class, which can hold either a `True` value or an `Exception` object.
        """
        return await self._api.set_device_info(SetPlugInfoParams(True))

    async def off(self) -> Try[bool]:
        """
        The function `off` sets the device info to False using the `SetPlugInfoParams` class.
        @return: an `Either` object, which can either be `True` or an `Exception`.
        """
        return await self._api.set_device_info(SetPlugInfoParams(False))

    async def get_energy_usage(self) -> Try[EnergyInfo]:
        """
        The function `get_energy_usage` asynchronously retrieves energy usage information from an API and returns it as an
        `EnergyInfo` object, or returns an `Exception` if an error occurs.
        @return: an `Either` type, which can either be an `EnergyInfo` object or an `Exception` object.
        """
        return await self._api.get_energy_usage()

    async def get_current_power(self) -> Try[PowerInfo]:
        """
        The function `get_current_power` asynchronously retrieves the current power information using an API and returns
        either the power information or an exception.
        @return: an instance of the `Either` class, which can contain either a `PowerInfo` object or an `Exception` object.
        """
        return await self._api.get_current_power()

    async def on_countdown_rule(self, delay: int, enable: bool = True) -> Try(bool):
        """
        The function `on_countdown_rule` sets a countdown to turn the device `on` with delay
            using the `SetPlugCountdownRuleParams` class.
        @param delay: The `delay` parameter sets the delay or countdown length in seconds before the new state is applied
        @return: an `Either` object, which can either be `True` or an `Exception`.
        """
        return await self._api.set_device_countdown_rule(
            SetPlugCountdownRuleParams(desired_states={"on": True}, delay=delay, enable=enable)
        )

    async def off_countdown_rule(self, delay: int, enable: bool = True) -> Try(bool):
        """
        The function `off_countdown_rule` sets a countdown to turn the device `off` with delay
            using the `SetPlugCountdownRuleParams` class.
        @param delay: The `delay` parameter sets the delay or countdown length in seconds before the new state is applied
        @return: an `Either` object, which can either be `True` or an `Exception`.
        """
        return await self._api.set_device_countdown_rule(
            SetPlugCountdownRuleParams(desired_states={"on": False}, delay=delay)
        )
