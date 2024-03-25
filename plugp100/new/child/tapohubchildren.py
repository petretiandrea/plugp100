import logging
from typing import Optional, Any, Callable

from plugp100.api.requests.set_device_info.set_trv_info_params import TRVDeviceInfoParams
from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.api.requests.trigger_logs_params import GetTriggerLogsParams
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.tri import Try
from plugp100.common.utils.json_utils import dataclass_encode_json
from plugp100.new.components.battery_component import BatteryComponent
from plugp100.new.components.humidity_component import HumidityComponent
from plugp100.new.components.motion_sensor_component import MotionSensorComponent
from plugp100.new.components.on_off_component import OnOffComponent
from plugp100.new.components.report_mode_component import ReportModeComponent
from plugp100.new.components.smart_door_component import SmartDoorComponent
from plugp100.new.components.temperature_component import TemperatureComponent
from plugp100.new.components.temperature_humidity_records import (
    TemperatureHumidityRecordComponent,
)
from plugp100.new.components.trigger_log_component import TriggerLogComponent
from plugp100.new.components.water_leak_component import WaterLeakComponent
from plugp100.new.device_type import DeviceType
from plugp100.new.event_polling.event_subscription import (
    EventSubscriptionOptions,
    EventLogsStateTracker,
)
from plugp100.new.event_polling.poll_tracker import PollTracker, PollSubscription
from plugp100.new.tapodevice import TapoDevice, C
from plugp100.responses.components import Components
from plugp100.responses.hub_childs.ke100_device_state import KE100DeviceState, TRVState
from plugp100.responses.hub_childs.s200b_device_state import (
    S200BEvent,
)
from plugp100.responses.hub_childs.t100_device_state import (
    T100Event,
    parse_t100_event,
)
from plugp100.responses.hub_childs.t110_device_state import T110Event
from plugp100.responses.hub_childs.t31x_device_state import (
    TemperatureHumidityRecordsRaw,
)
from plugp100.responses.hub_childs.trigger_log_response import TriggerLogResponse
from plugp100.responses.temperature_unit import TemperatureUnit


class TapoHubChildDevice(TapoDevice):
    def __init__(
        self,
        host: str,
        port: Optional[int],
        client: TapoClient,
        device_id: str,
        parent_device_id: str,
        device_type: DeviceType = DeviceType.Hub,
    ):
        super().__init__(host, port, client, device_type, device_id)
        self._parent_device_id = parent_device_id

    @property
    def parent_device_id(self) -> str:
        return self._parent_device_id

    @property
    def battery_low(self) -> bool:
        return self.get_component(BatteryComponent).is_battery_low

    @property
    def report_interval_seconds(self) -> int:
        return self.get_component(ReportModeComponent).report_interval_seconds

    def _get_components_to_activate(self, components: Components) -> list[C]:
        active_components = [ReportModeComponent()]
        if components.has("battery_detect"):
            active_components.append(BatteryComponent())
        return active_components


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


TriggerLogsSubscription = Callable[[], Any]


class TriggerButtonDevice(TapoHubChildDevice):
    _DEFAULT_POLLING_PAGE_SIZE = 5

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
        self._logger = logging.getLogger(f"ButtonDevice[${child_id}]")
        self._poll_tracker: Optional[PollTracker] = None

    def _get_components_to_activate(self, components: Components) -> list[C]:
        active_components = []
        if components.has("trigger_log"):
            active_components.append(TriggerLogComponent(self.client, self._child_id))
        return super()._get_components_to_activate(components) + active_components

    async def get_event_logs(
        self,
        page_size: int,
        start_id: int = 0,
    ) -> Try[TriggerLogResponse[S200BEvent]]:
        """
        Use start_id = 0 to get latest page_size events
        @param page_size: the number of max event returned
        @param start_id: start item id from start to returns in reverse time order
        @return: Trigger Logs or Error
        """
        return await self.get_component(TriggerLogComponent).get_event_logs(
            page_size, start_id
        )

    def subscribe_event_logs(
        self,
        callback: Callable[[S200BEvent], Any],
        event_subscription_options: EventSubscriptionOptions,
    ) -> PollSubscription:
        if self._poll_tracker is None:
            self._poll_tracker = PollTracker(
                state_provider=self._poll_event_logs,
                state_tracker=EventLogsStateTracker(
                    event_subscription_options.debounce_millis, logger=self._logger
                ),
                interval_millis=event_subscription_options.polling_interval_millis,
                logger=self._logger,
            )
        return self._poll_tracker.subscribe(callback)

    async def _poll_event_logs(
        self, last_state: Optional[TriggerLogResponse[S200BEvent]]
    ):
        response = await self.get_event_logs(self._DEFAULT_POLLING_PAGE_SIZE, 0)
        return response.get_or_else(TriggerLogResponse(0, 0, []))


class SwitchChildDevice(TapoHubChildDevice):
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

    def _get_components_to_activate(self, components: Components) -> list[C]:
        return super()._get_components_to_activate(components) + [
            OnOffComponent(self.client, self._child_id)
        ]

    async def on(self) -> Try[bool]:
        return await self.get_component(OnOffComponent).turn_on()

    async def off(self) -> Try[bool]:
        return await self.get_component(OnOffComponent).turn_off()

    @property
    def is_on(self) -> bool:
        return self.get_component(OnOffComponent).device_on


class MotionSensor(TapoHubChildDevice):
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

    def _get_components_to_activate(self, components: Components) -> list[C]:
        return super()._get_components_to_activate(components) + [MotionSensorComponent()]

    async def get_event_logs(
        self,
        page_size: int,
        start_id: int = 0,
    ) -> Try[TriggerLogResponse[T100Event]]:
        request = TapoRequest.get_child_event_logs(
            GetTriggerLogsParams(page_size, start_id)
        )
        return (await self.client.control_child(self._device_id, request)).flat_map(
            lambda x: TriggerLogResponse[T100Event].try_from_json(x, parse_t100_event)
        )

    @property
    def is_detected(self) -> bool:
        return self.get_component(MotionSensorComponent).detected


class SmartDoorSensor(TapoHubChildDevice):
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

    def _get_components_to_activate(self, components: Components) -> list[C]:
        return super()._get_components_to_activate(components) + [SmartDoorComponent()]

    async def get_event_logs(
        self,
        page_size: int,
        start_id: int = 0,
    ) -> Try[TriggerLogResponse[T110Event]]:
        request = TapoRequest.get_child_event_logs(
            GetTriggerLogsParams(page_size, start_id)
        )
        response = await self.client.control_child(self._device_id, request)
        return response.flat_map(
            lambda x: TriggerLogResponse[T110Event].try_from_json(x, parse_t100_event)
        )


class TemperatureHumiditySensor(TapoHubChildDevice):
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

    def _get_components_to_activate(self, components: Components) -> list[C]:
        active_components = []
        if components.has("temperature"):
            active_components.append(TemperatureComponent())
        if components.has("humidity"):
            active_components.append(HumidityComponent())
        if components.has("temp_humidity_record"):
            active_components.append(
                TemperatureHumidityRecordComponent(self.client, self._child_id)
            )
        return super()._get_components_to_activate(components) + active_components

    async def get_temperature_humidity_records(
        self,
    ) -> Try[TemperatureHumidityRecordsRaw]:
        return await self.get_component(
            TemperatureHumidityRecordComponent
        ).get_temperature_humidity_records()

    @property
    def current_humidity(self) -> int:
        return self.get_component(HumidityComponent).current_humidity

    @property
    def current_humidity_error(self) -> int:
        return self.get_component(HumidityComponent).current_humidity_error

    @property
    def current_temperature(self) -> float:
        return self.get_component(TemperatureComponent).current_temperature

    @property
    def current_temperature_error(self) -> float:
        return self.get_component(TemperatureComponent).current_temperature_error

    @property
    def temperature_unit(self) -> TemperatureUnit:
        return self.get_component(TemperatureComponent).temperature_unit


class WaterLeakSensor(TapoHubChildDevice):
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

    def _get_components_to_activate(self, components: Components) -> list[C]:
        return super()._get_components_to_activate(components) + [WaterLeakComponent()]

    @property
    def is_alarm_active(self) -> bool:
        return self.get_component(WaterLeakComponent).in_alarm

    @property
    def water_leak_status(self) -> str:
        return self.get_component(WaterLeakComponent).water_leak_status
