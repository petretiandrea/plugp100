from typing import Any

from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.api.requests.trigger_logs_params import GetTriggerLogsParams
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.tri import Try
from plugp100.components.base import DeviceComponent
from plugp100.models.hub_children.button import S200BEvent, parse_s200b_event
from plugp100.models.hub_children.logs import TriggerLogResponse


class TriggerLogComponent(DeviceComponent):
    def __init__(self, client: TapoClient, device_id: str | None = None):
        self._client = client
        self._device_id = device_id

    async def update(self, current_state: dict[str, Any] | None = None):
        pass

    async def get_event_logs(
        self,
        page_size: int,
        start_id: int = 0,
    ) -> Try[TriggerLogResponse[S200BEvent]]:
        request = TapoRequest.get_child_event_logs(
            GetTriggerLogsParams(page_size, start_id)
        )
        return (await self._client.control_child(self._device_id, request)).flat_map(
            lambda x: TriggerLogResponse[S200BEvent].try_from_json(x, parse_s200b_event)
        )
