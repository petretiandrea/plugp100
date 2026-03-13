import dataclasses
import logging
from typing import List, Optional

from plugp100.events.state_tracker import StateTracker
from plugp100.models.hub_children.button import S200BEvent
from plugp100.models.hub_children.logs import TriggerLogResponse


@dataclasses.dataclass
class EventSubscriptionOptions:
    polling_interval_millis: int
    debounce_millis: int = 500


class EventLogsStateTracker(StateTracker[TriggerLogResponse[S200BEvent], S200BEvent]):
    def __init__(self, debounce_millis: int, logger: logging.Logger = None):
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
