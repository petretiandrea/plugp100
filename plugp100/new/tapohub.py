import logging
from typing import Optional, List, Set, Any, Callable

from plugp100.api.requests.set_device_info.play_alarm_params import PlayAlarmParams
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.tri import Try, Failure
from plugp100.new.components.alarm_component import AlarmComponent
from plugp100.new.components.hub_children_component import HubChildrenComponent
from plugp100.new.device_type import DeviceType
from plugp100.new.event_polling.poll_tracker import PollTracker, PollSubscription
from plugp100.new.hub_device_tracker import HubConnectedDeviceTracker, HubDeviceEvent
from plugp100.new.tapodevice import TapoDevice, C
from plugp100.responses.alarm_type_list import AlarmTypeList
from plugp100.responses.components import Components

_LOGGER = logging.getLogger("TapoHub")

subscription_polling_interval_millis: int = 5000


class TapoHub(TapoDevice):
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

    @property
    def is_alarm_on(self) -> bool:
        return self.get_component(AlarmComponent).is_alarm_on

    @property
    def has_alarm(self):
        return self.get_component(AlarmComponent) is not None

    @property
    def children(self) -> List["TapoDevice"]:
        return self.get_component(HubChildrenComponent).children

    async def turn_alarm_on(self, alarm: PlayAlarmParams = None) -> Try[bool]:
        if self.has_alarm:
            return await self.get_component(AlarmComponent).turn_alarm_on(alarm)
        return Failure(Exception("Device not support alarm"))

    async def turn_alarm_off(self) -> Try[bool]:
        if self.has_alarm:
            return await self.get_component(AlarmComponent).turn_alarm_off()
        return Failure(Exception("Device not support alarm"))

    async def get_supported_alarm_tones(self) -> Try[AlarmTypeList]:
        if self.has_alarm:
            return await self.get_component(AlarmComponent).get_supported_alarm_tones()
        return Failure(Exception("Device not support alarm"))

    def find_child_device_by_model(self, model_filter: str) -> Optional["TapoDevice"]:
        return self.get_component(HubChildrenComponent).find_child_device_by_model(
            model_filter
        )

    async def _poll_device_list(self, last_state: Set[str]) -> Set[str]:
        return (
            (await self.client.get_child_device_list())
            .map(lambda x: x.get_device_ids())
            .get_or_else(set())
        )

    def _get_components_to_activate(self, components: Components) -> list[C]:
        active_components = []
        if components.has("alarm"):
            active_components.append(AlarmComponent(self.client))
        if components.has("control_child"):
            active_components.append(HubChildrenComponent(self, self.client))
        return active_components
