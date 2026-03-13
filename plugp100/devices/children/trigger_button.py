import logging
from typing import Any, Callable, Optional

from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.tri import Try
from plugp100.components.trigger_log import TriggerLogComponent
from plugp100.devices.children.base import TapoHubChildDevice
from plugp100.devices.types import DeviceType
from plugp100.events.event_subscription import (
    EventLogsStateTracker,
    EventSubscriptionOptions,
)
from plugp100.events.poll_tracker import PollSubscription, PollTracker
from plugp100.models.hub_children.button import S200BEvent
from plugp100.models.hub_children.logs import TriggerLogResponse


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

    def _get_components_to_activate(self, components):
        active_components = []
        if components.has("trigger_log"):
            active_components.append(TriggerLogComponent(self.client, self._child_id))
        return super()._get_components_to_activate(components) + active_components

    async def get_event_logs(
        self,
        page_size: int,
        start_id: int = 0,
    ) -> Try[TriggerLogResponse[S200BEvent]]:
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


__all__ = ["TriggerButtonDevice"]
