from typing import Any

from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.api.requests.trigger_logs_params import GetTriggerLogsParams
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.tri import Try
from plugp100.new.components.device_component import DeviceComponent
from plugp100.responses.hub_childs.s200b_device_state import S200BEvent, parse_s200b_event
from plugp100.responses.hub_childs.trigger_log_response import TriggerLogResponse


# TODO: actually is too specific for s200b events. Generalize it
class TriggerLogComponent(DeviceComponent):
    async def update(self, current_state: dict[str, Any] | None = None):
        pass

    def __init__(self, client: TapoClient, device_id: str | None = None):
        self._client = client
        self._device_id = device_id

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
        return (await self._client.control_child(self._device_id, request)).flat_map(
            lambda x: TriggerLogResponse[S200BEvent].try_from_json(x, parse_s200b_event)
        )
