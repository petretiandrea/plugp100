import abc
import base64
import logging
from typing import Optional, List, Set, Any, Callable, cast

from plugp100.api.hub.hub_device_tracker import HubConnectedDeviceTracker, HubDeviceEvent
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.tri import Try, Failure
from plugp100.common.utils.json_utils import dataclass_encode_json, Json
from plugp100.new.device_type import DeviceType
from plugp100.new.event_polling.event_subscription import (
    EventSubscriptionOptions,
    EventLogsStateTracker,
)
from plugp100.new.event_polling.poll_tracker import PollTracker, PollSubscription
from plugp100.new.tapodevice import AbstractTapoDevice, TapoDevice
from plugp100.requests.set_device_info.play_alarm_params import PlayAlarmParams
from plugp100.requests.set_device_info.set_plug_info_params import SetPlugInfoParams
from plugp100.requests.set_device_info.set_trv_info_params import TRVDeviceInfoParams
from plugp100.requests.tapo_request import TapoRequest
from plugp100.requests.trigger_logs_params import GetTriggerLogsParams
from plugp100.responses.alarm_type_list import AlarmTypeList
from plugp100.responses.components import Components
from plugp100.responses.device_state import DeviceInfo
from plugp100.responses.hub_childs.hub_child_base_info import HubChildBaseInfo
from plugp100.responses.hub_childs.ke100_device_state import KE100DeviceState, TRVState
from plugp100.responses.hub_childs.leak_device_state import LeakDeviceState
from plugp100.responses.hub_childs.s200b_device_state import (
    S200BDeviceState,
    S200BEvent,
    parse_s200b_event,
)
from plugp100.responses.hub_childs.switch_child_device_state import SwitchChildDeviceState
from plugp100.responses.hub_childs.t100_device_state import (
    T100Event,
    T100MotionSensorState,
    parse_t100_event,
)
from plugp100.responses.hub_childs.t110_device_state import T110SmartDoorState, T110Event
from plugp100.responses.hub_childs.t31x_device_state import (
    TemperatureHumidityRecordsRaw,
    T31DeviceState,
)
from plugp100.responses.hub_childs.trigger_log_response import TriggerLogResponse
from plugp100.responses.temperature_unit import TemperatureUnit

_LOGGER = logging.getLogger("TapoHub")

subscription_polling_interval_millis: int = 5000


class TapoHub(AbstractTapoDevice):
    def __init__(self, host: str, port: Optional[int], client: TapoClient):
        super().__init__(host, port, client, DeviceType.Hub)
        self._children = []
        self._tracker = HubConnectedDeviceTracker(_LOGGER)
        self._poll_tracker = PollTracker(
            state_provider=self._poll_device_list,
            state_tracker=self._tracker,
            interval_millis=subscription_polling_interval_millis,
            logger=_LOGGER,
        )

    def subscribe_device_association(
        self, callback: Callable[[HubDeviceEvent], Any]
    ) -> PollSubscription:
        return self._poll_tracker.subscribe(callback)

    async def update(self):
        await super().update()

        if self.components.has("control_child"):
            if len(self._children) == 0:
                children = (
                    await self.client.get_child_device_list(all_pages=True)
                ).get_or_raise()
                _LOGGER.info("Initializing %s children", children.sum)
                for child in children.get_children_base_info():
                    child_device = _hub_child_create(self, child)
                    self._children.append(child_device)

                for child_device in self._children:
                    await child_device.update()

    @property
    def is_alarm_on(self) -> bool:
        return self._last_update.get("state").get("in_alarm", False)

    @property
    def has_alarm(self):
        return self.components.has("alarm")

    @property
    def children(self) -> List["TapoHubChildDevice"]:
        return self._children

    async def turn_alarm_on(self, alarm: PlayAlarmParams = None) -> Try[bool]:
        if self.has_alarm:
            request = TapoRequest(
                method="play_alarm",
                params=dataclass_encode_json(alarm) if alarm is not None else None,
            )
            return (await self.client.execute_raw_request(request)).map(lambda _: True)
        return Failure(Exception("Device not support alarm"))

    async def turn_alarm_off(self) -> Try[bool]:
        if self.has_alarm:
            return (
                await self.client.execute_raw_request(
                    TapoRequest(method="stop_alarm", params=None)
                )
            ).map(lambda _: True)
        return Failure(Exception("Device not support alarm"))

    async def get_supported_alarm_tones(self) -> Try[AlarmTypeList]:
        if self.has_alarm:
            return (
                await self.client.execute_raw_request(
                    TapoRequest(method="get_support_alarm_type_list", params=None)
                )
            ).flat_map(AlarmTypeList.try_from_json)
        return Failure(Exception("Device not support alarm"))

    async def control_child(self, device_id: str, request: TapoRequest) -> Try[Json]:
        return await self.client.control_child(device_id, request)

    async def _poll_device_list(self, last_state: Set[str]) -> Set[str]:
        return (
            (await self.client.get_child_device_list())
            .map(lambda x: x.get_device_ids())
            .get_or_else(set())
        )


class TapoHubChildDevice(TapoDevice):
    def __init__(
        self,
        hub: TapoHub,
        device_id: str,
        device_type: DeviceType = DeviceType.Hub,
    ):
        self._hub = hub
        self._device_id = device_id
        self._last_update = {}
        self._device_type = device_type

    @property
    def device_info(self) -> DeviceInfo:
        return self._last_update["device_info"]

    @property
    def components(self) -> Components:
        return self._last_update["components"]

    @property
    def nickname(self) -> str:
        return self.device_info.nickname

    @property
    def mac(self) -> str:
        return self.device_info.mac

    @property
    def model(self) -> str:
        return self.device_info.model

    @property
    def device_id(self) -> str:
        return self.device_info.device_id

    @property
    def device_type(self) -> DeviceType:
        return self._device_type

    @property
    def overheated(self) -> bool:
        return False

    @property
    def parent_device_id(self) -> str:
        return self._last_update["child_info"].parent_device_id

    @property
    def battery_low(self) -> str:
        return self._last_update["child_info"].at_low_battery

    @property
    def last_onboarding(self) -> int:
        return self._last_update["child_info"].last_onboarding_timestamp

    async def update(self):
        if "components" not in self._last_update:
            components = (await self._fetch_components()).get_or_raise()
        else:
            components = self._last_update["components"]

        (info, state) = (await self._fetch_state()).get_or_raise()
        child_info = cast(HubChildBaseInfo, info)
        device_info = DeviceInfo(
            device_id=child_info.device_id,
            hw_id=self._hub.device_info.hardware_id,
            oem_id=self._hub.device_info.oem_id,
            hw_ver=child_info.hardware_version,
            fw_ver=child_info.firmware_version,
            mac=child_info.mac,
            type=child_info.type,
            model=child_info.model,
            rssi=child_info.rssi,
            signal_level=child_info.signal_level,
            nickname=base64.b64encode(child_info.nickname.encode("UTF-8")),
        )

        self._last_update = {
            "components": components,
            "device_info": device_info,
            "state": state,
            "child_info": child_info,
        }

    @abc.abstractmethod
    async def _fetch_components(self) -> Try[Components]:
        pass

    @abc.abstractmethod
    async def _fetch_state(self) -> Try[tuple[HubChildBaseInfo, Any]]:
        pass


class KE100Device(TapoHubChildDevice):
    def __init__(
        self, hub: TapoHub, device_id: str, device_type: DeviceType = DeviceType.Hub
    ):
        super().__init__(hub, device_id, device_type)

    async def _fetch_components(self) -> Try[Components]:
        return (
            await self._hub.control_child(
                self._device_id, TapoRequest.component_negotiation()
            )
        ).map(Components.try_from_json)

    async def _fetch_state(self) -> Try[tuple[HubChildBaseInfo, Any]]:
        return (
            (
                await self._hub.control_child(
                    self._device_id, TapoRequest.get_device_info()
                )
            )
            .flat_map(KE100DeviceState.from_json)
            .map(lambda x: (x.base_info, x))
        )

    @property
    def state(self) -> TRVState:
        return cast(KE100DeviceState, self._last_update["state"]).trv_state

    @property
    def temperature_unit(self) -> TemperatureUnit:
        return cast(KE100DeviceState, self._last_update["state"]).temperature_unit

    @property
    def temperature(self) -> float:
        return cast(KE100DeviceState, self._last_update["state"]).current_temperature

    @property
    def target_temperature(self) -> float:
        return cast(KE100DeviceState, self._last_update["state"]).target_temperature

    @property
    def temperature_offset(self) -> float:
        return cast(KE100DeviceState, self._last_update["state"]).temperature_offset

    @property
    def range_control_temperature(self) -> tuple[int, int]:
        return (
            cast(KE100DeviceState, self._last_update["state"]).min_control_temperature,
            cast(KE100DeviceState, self._last_update["state"]).max_control_temperature,
        )

    @property
    def battery_percentage(self) -> int:
        return cast(KE100DeviceState, self._last_update["state"]).battery_percentage

    @property
    def is_frost_protection_on(self) -> int:
        return cast(KE100DeviceState, self._last_update["state"]).frost_protection_on

    @property
    def is_child_protection_on(self) -> int:
        return cast(KE100DeviceState, self._last_update["state"]).child_protection

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
        return (await self._hub.control_child(self._device_id, request)).map(
            lambda _: True
        )


TriggerLogsSubscription = Callable[[], Any]


class S200ButtonDevice(TapoHubChildDevice):
    _DEFAULT_POLLING_PAGE_SIZE = 5

    def __init__(
        self, hub: TapoHub, device_id: str, device_type: DeviceType = DeviceType.Sensor
    ):
        super().__init__(hub, device_id, device_type)
        self._logger = logging.getLogger(f"ButtonDevice[${device_id}]")
        self._poll_tracker: Optional[PollTracker] = None

    async def _fetch_components(self) -> Try[Components]:
        return (
            await self._hub.control_child(
                self._device_id, TapoRequest.component_negotiation()
            )
        ).map(Components.try_from_json)

    async def _fetch_state(self) -> Try[tuple[HubChildBaseInfo, Any]]:
        return (
            (
                await self._hub.control_child(
                    self._device_id, TapoRequest.get_device_info()
                )
            )
            .flat_map(S200BDeviceState.try_from_json)
            .map(lambda x: (x.base_info, x))
        )

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
        request = TapoRequest.get_child_event_logs(
            GetTriggerLogsParams(page_size, start_id)
        )
        return (await self._hub.control_child(self._device_id, request)).flat_map(
            lambda x: TriggerLogResponse[S200BEvent].try_from_json(x, parse_s200b_event)
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

    @property
    def report_interval_seconds(self) -> int:
        return cast(S200BDeviceState, self._last_update["state"]).report_interval_seconds


class SwitchChildDevice(TapoHubChildDevice):
    def __init__(
        self, hub: TapoHub, device_id: str, device_type: DeviceType = DeviceType.Sensor
    ):
        super().__init__(hub, device_id, device_type)

    async def _fetch_components(self) -> Try[Components]:
        return (
            await self._hub.control_child(
                self._device_id, TapoRequest.component_negotiation()
            )
        ).map(Components.try_from_json)

    async def _fetch_state(self) -> Try[tuple[HubChildBaseInfo, Any]]:
        return (
            (
                await self._hub.control_child(
                    self._device_id, TapoRequest.get_device_info()
                )
            )
            .flat_map(SwitchChildDeviceState.try_from_json)
            .map(lambda x: (x.base_info, x))
        )

    async def on(self) -> Try[bool]:
        request = TapoRequest.set_device_info(
            dataclass_encode_json(SetPlugInfoParams(device_on=True))
        )
        return (await self._hub.control_child(self._device_id, request)).map(
            lambda _: True
        )

    async def off(self) -> Try[bool]:
        request = TapoRequest.set_device_info(
            dataclass_encode_json(SetPlugInfoParams(device_on=False))
        )
        return (await self._hub.control_child(self._device_id, request)).map(
            lambda _: True
        )

    @property
    def is_on(self) -> bool:
        return cast(SwitchChildDeviceState, self._last_update.get("state")).device_on

    @property
    def led_off(self) -> int:
        return cast(SwitchChildDeviceState, self._last_update.get("state")).led_off


class T100MotionSensor(TapoHubChildDevice):
    def __init__(
        self, hub: TapoHub, device_id: str, device_type: DeviceType = DeviceType.Sensor
    ):
        super().__init__(hub, device_id, device_type)

    async def _fetch_components(self) -> Try[Components]:
        return (
            await self._hub.control_child(
                self._device_id, TapoRequest.component_negotiation()
            )
        ).map(Components.try_from_json)

    async def _fetch_state(self) -> Try[tuple[HubChildBaseInfo, Any]]:
        return (
            (
                await self._hub.control_child(
                    self._device_id, TapoRequest.get_device_info()
                )
            )
            .flat_map(T100MotionSensorState.from_json)
            .map(lambda x: (x.base_info, x))
        )

    async def get_event_logs(
        self,
        page_size: int,
        start_id: int = 0,
    ) -> Try[TriggerLogResponse[T100Event]]:
        request = TapoRequest.get_child_event_logs(
            GetTriggerLogsParams(page_size, start_id)
        )
        return (await self._hub.control_child(self._device_id, request)).flat_map(
            lambda x: TriggerLogResponse[T100Event].try_from_json(x, parse_t100_event)
        )

    @property
    def is_detected(self) -> bool:
        return cast(T100MotionSensorState, self._last_update["state"]).detected

    @property
    def report_interval_seconds(self) -> int:
        return cast(
            T100MotionSensorState, self._last_update["state"]
        ).report_interval_seconds


class T110SmartDoor(TapoHubChildDevice):
    def __init__(
        self, hub: TapoHub, device_id: str, device_type: DeviceType = DeviceType.Sensor
    ):
        super().__init__(hub, device_id, device_type)

    async def _fetch_components(self) -> Try[Components]:
        return (
            await self._hub.control_child(
                self._device_id, TapoRequest.component_negotiation()
            )
        ).map(Components.try_from_json)

    async def _fetch_state(self) -> Try[tuple[HubChildBaseInfo, Any]]:
        return (
            (
                await self._hub.control_child(
                    self._device_id, TapoRequest.get_device_info()
                )
            )
            .flat_map(T110SmartDoorState.try_from_json)
            .map(lambda x: (x.base_info, x))
        )

    async def get_event_logs(
        self,
        page_size: int,
        start_id: int = 0,
    ) -> Try[TriggerLogResponse[T110Event]]:
        request = TapoRequest.get_child_event_logs(
            GetTriggerLogsParams(page_size, start_id)
        )
        response = await self._hub.control_child(self._device_id, request)
        return response.flat_map(
            lambda x: TriggerLogResponse[T110Event].try_from_json(x, parse_t100_event)
        )

    @property
    def is_open(self) -> bool:
        return cast(T110SmartDoorState, self._last_update["state"]).is_open

    @property
    def report_interval_seconds(self) -> int:
        return cast(
            T110SmartDoorState, self._last_update["state"]
        ).report_interval_seconds


class T31Device(TapoHubChildDevice):
    def __init__(
        self, hub: TapoHub, device_id: str, device_type: DeviceType = DeviceType.Sensor
    ):
        super().__init__(hub, device_id, device_type)

    async def _fetch_components(self) -> Try[Components]:
        return (
            await self._hub.control_child(
                self._device_id, TapoRequest.component_negotiation()
            )
        ).map(Components.try_from_json)

    async def _fetch_state(self) -> Try[tuple[HubChildBaseInfo, Any]]:
        return (
            (
                await self._hub.control_child(
                    self._device_id, TapoRequest.get_device_info()
                )
            )
            .flat_map(T31DeviceState.from_json)
            .map(lambda x: (x.base_info, x))
        )

    async def get_temperature_humidity_records(
        self,
    ) -> Try[TemperatureHumidityRecordsRaw]:
        request = TapoRequest.get_temperature_humidity_records()
        response = await self._hub.control_child(self._device_id, request)
        return response.flat_map(TemperatureHumidityRecordsRaw.from_json)

    @property
    def current_humidity(self) -> int:
        return cast(T31DeviceState, self._last_update["state"]).current_humidity

    @property
    def current_humidity_exception(self) -> int:
        return cast(T31DeviceState, self._last_update["state"]).current_humidity_exception

    @property
    def current_temperature(self) -> float:
        return cast(T31DeviceState, self._last_update["state"]).current_temperature

    @property
    def current_temperature_exception(self) -> float:
        return cast(
            T31DeviceState, self._last_update["state"]
        ).current_temperature_exception

    @property
    def temperature_unit(self) -> TemperatureUnit:
        return cast(T31DeviceState, self._last_update["state"]).temperature_unit

    @property
    def report_interval_seconds(self) -> int:
        return cast(T31DeviceState, self._last_update["state"]).report_interval_seconds


class WaterLeakSensor(TapoHubChildDevice):
    def __init__(
        self, hub: TapoHub, device_id: str, device_type: DeviceType = DeviceType.Sensor
    ):
        super().__init__(hub, device_id, device_type)

    async def _fetch_components(self) -> Try[Components]:
        return (
            await self._hub.control_child(
                self._device_id, TapoRequest.component_negotiation()
            )
        ).map(Components.try_from_json)

    async def _fetch_state(self) -> Try[tuple[HubChildBaseInfo, Any]]:
        return (
            (
                await self._hub.control_child(
                    self._device_id, TapoRequest.get_device_info()
                )
            )
            .flat_map(LeakDeviceState.try_from_json)
            .map(lambda x: (x.base_info, x))
        )

    @property
    def alarm_active(self) -> bool:
        return cast(LeakDeviceState, self._last_update["state"]).in_alarm

    @property
    def water_leak_status(self) -> str:
        return cast(LeakDeviceState, self._last_update["state"]).water_leak_status


def _hub_child_create(
    hub: TapoHub, device_info: HubChildBaseInfo
) -> Optional[TapoHubChildDevice]:
    model = device_info.model.lower()
    device_id = device_info.device_id
    if "t31" in model:
        return T31Device(hub, device_id)
    elif "t110" in model:
        return T110SmartDoor(hub, device_id)
    elif "s200" in model:
        return S200ButtonDevice(hub, device_id)
    elif "t100" in model:
        return T100MotionSensor(hub, device_id)
    elif "ke100" in model:
        return KE100Device(hub, device_id)
    elif "t300" in model:
        return WaterLeakSensor(hub, device_id)
    elif any(supported in model for supported in ["s220", "s210"]):
        return SwitchChildDevice(hub, device_id)
    return None
