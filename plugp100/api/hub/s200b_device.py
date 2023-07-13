from plugp100.api.hub.hub_device import HubDevice
from plugp100.common.functional.either import Either
from plugp100.requests.tapo_request import TapoRequest
from plugp100.requests.trigger_logs_params import GetTriggerLogsParams
from plugp100.responses.hub_childs.s200b_device_state import S200BDeviceState, S200BEvent, parse_s200b_event
from plugp100.responses.hub_childs.trigger_log_response import TriggerLogResponse


class S200ButtonDevice:

    def __init__(self, hub: HubDevice, device_id: str):
        self._hub = hub
        self._device_id = device_id

    async def get_device_info(self) -> Either[S200BDeviceState, Exception]:
        """
        The function `get_device_info` sends a request to retrieve device information and returns either the device state or
        an exception.
        @  return: an instance of the `Either` class, which can hold either an instance of `S200BDeviceState` or an instance
        of `Exception`.
        """
        request = TapoRequest.get_device_info()
        return await self._hub.control_child(self._device_id, request) | S200BDeviceState.try_from_json

    async def get_event_logs(
            self,
            page_size: int,
            start_id: int = 0,
    ) -> Either[TriggerLogResponse[S200BEvent], Exception]:
        """
        Use start_id = 0 to get latest page_size events
        @param page_size: the number of max event returned
        @param start_id: start item id from start to returns in reverse time order
        @return: Trigger Logs or Error
        """
        request = TapoRequest.get_child_event_logs(GetTriggerLogsParams(page_size, start_id))
        response = await self._hub.control_child(self._device_id, request)
        return response.map(lambda x: TriggerLogResponse[S200BEvent].try_from_json(x, parse_s200b_event))
