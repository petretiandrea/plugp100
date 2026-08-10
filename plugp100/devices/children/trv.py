from typing import Any, Optional

from plugp100.api.requests.set_device_info.set_trv_info_params import TRVDeviceInfoParams
from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.tri import Try
from plugp100.common.utils.json_utils import dataclass_encode_json
from plugp100.components.battery import BatteryComponent
from plugp100.devices.base import C
from plugp100.devices.children.base import TapoHubChildDevice
from plugp100.devices.types import DeviceType
from plugp100.models.components import Components
from plugp100.models.hub_children.trv import KE100DeviceState, TRVState
from plugp100.models.temperature import TemperatureUnit


class KE100Device(TapoHubChildDevice):
    def __init__(
        self,
        host: str,
        port: Optional[int],
        client: TapoClient,
        child_id: str,
        parent_device_id: str,
        device_type: DeviceType = DeviceType.Sensor,
    ):
        super().__init__(host, port, client, child_id, parent_device_id, device_type)
        self._last_state: KE100DeviceState | None = None

    def _get_components_to_activate(self, components: Components) -> list[C]:
        return super()._get_components_to_activate(components) + [BatteryComponent()]

    async def _update_from_state(self, state: dict[str, Any]):
        self._last_state = KE100DeviceState.from_json(state).get_or_raise()
        return await super()._update_from_state(state)

    @property
    def state(self) -> TRVState:
        return self._last_state.trv_state

    @property
    def temperature_unit(self) -> TemperatureUnit:
        return self._last_state.temperature_unit

    @property
    def temperature(self) -> float:
        return self._last_state.current_temperature

    @property
    def target_temperature(self) -> float:
        return self._last_state.target_temperature

    @property
    def temperature_offset(self) -> float:
        return self._last_state.temperature_offset

    @property
    def range_control_temperature(self) -> tuple[int, int]:
        return (
            self._last_state.min_control_temperature,
            self._last_state.max_control_temperature,
        )

    @property
    def battery_percentage(self) -> int:
        return self._last_state.battery_percentage

    @property
    def is_frost_protection_on(self) -> int:
        return self._last_state.frost_protection_on

    @property
    def is_child_protection_on(self) -> int:
        return self._last_state.child_protection

    async def set_target_temp(self, kwargs: Any) -> Try[bool]:
        return await self._send_trv_control_request(
            TRVDeviceInfoParams(target_temp=kwargs["temperature"])
        )

    async def set_temp_offset(self, value: int) -> Try[bool]:
        return await self._send_trv_control_request(
            TRVDeviceInfoParams(temp_offset=value)
        )

    async def set_frost_protection_on(self) -> Try[bool]:
        return await self._send_trv_control_request(
            TRVDeviceInfoParams(frost_protection_on=True)
        )

    async def set_frost_protection_off(self) -> Try[bool]:
        return await self._send_trv_control_request(
            TRVDeviceInfoParams(frost_protection_on=False)
        )

    async def set_child_protection_on(self) -> Try[bool]:
        return await self._send_trv_control_request(
            TRVDeviceInfoParams(child_protection=True)
        )

    async def set_child_protection_off(self) -> Try[bool]:
        return await self._send_trv_control_request(
            TRVDeviceInfoParams(child_protection=False)
        )

    async def _send_trv_control_request(self, params: TRVDeviceInfoParams) -> Try[bool]:
        request = TapoRequest.set_device_info(dataclass_encode_json(params))
        return (await self.client.control_child(self._child_id, request)).map(
            lambda _: True
        )


__all__ = ["KE100Device"]
