import dataclasses
import logging
from logging import Logger
from typing import List, Callable, Any, Optional

from plugp100.api.hub.hub_device import HubDevice
from plugp100.common.functional.tri import Try
from plugp100.common.poll_tracker import PollTracker, PollSubscription
from plugp100.common.state_tracker import StateTracker
from plugp100.requests.tapo_request import TapoRequest
from plugp100.requests.trigger_logs_params import GetTriggerLogsParams
from plugp100.responses.components import Components
from plugp100.responses.hub_childs.s200b_device_state import (
    S200BDeviceState,
    S200BEvent,
    parse_s200b_event,
)
from plugp100.responses.hub_childs.trigger_log_response import TriggerLogResponse

TriggerLogsSubscription = Callable[[], Any]


@dataclasses.dataclass
class EventSubscriptionOptions:
    polling_interval_millis: int
    debounce_millis: int = 500


class S200ButtonDevice:
    _DEFAULT_POLLING_PAGE_SIZE = 5

    def __init__(self, hub: HubDevice, device_id: str):
        self._hub = hub
        self._device_id = device_id
        self._logger = logging.getLogger(f"ButtonDevice[${device_id}]")
        self._poll_tracker: Optional[PollTracker] = None

    async def get_device_info(self) -> Try[S200BDeviceState]:
        """
        The function `get_device_info` sends a request to retrieve device information and returns either the device state or
        an exception.
        @  return: an instance of the `Either` class, which can hold either an instance of `S200BDeviceState` or an instance
        of `Exception`.
        """
        return (
            await self._hub.control_child(self._device_id, TapoRequest.get_device_info())
        ).flat_map(S200BDeviceState.try_from_json)

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
                state_tracker=_EventLogsStateTracker(
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

    async def get_component_negotiation(self) -> Try[Components]:
        return (
            await self._hub.control_child(
                self._device_id, TapoRequest.component_negotiation()
            )
        ).map(Components.try_from_json)


class _EventLogsStateTracker(StateTracker[TriggerLogResponse[S200BEvent], S200BEvent]):
    def __init__(self, debounce_millis: int, logger: Logger = None):
        super().__init__(logger=logger)
        self._debounce_millis = debounce_millis

    def _compute_state_changes(
        self,
        new_state: TriggerLogResponse[S200BEvent],
        last_state: Optional[TriggerLogResponse[S200BEvent]],
    ) -> List[S200BEvent]:
        if last_state is None or len(last_state.events) == 0:
            return []
        last_event_id = last_state.event_start_id
        last_event_timestamp = last_state.events[0].timestamp
        return list(
            filter(
                lambda x: x.id > last_event_id
                and x.timestamp - last_event_timestamp <= self._debounce_millis,
                new_state.events,
            )
        )
