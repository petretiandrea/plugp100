from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.api.requests.trigger_logs_params import GetTriggerLogsParams
from plugp100.common.functional.tri import Try
from plugp100.components.smart_door import SmartDoorComponent
from plugp100.devices.children.base import TapoHubChildDevice
from plugp100.models.hub_children.door import T110Event, parse_t110_event
from plugp100.models.hub_children.logs import TriggerLogResponse


class SmartDoorSensor(TapoHubChildDevice):
    def _get_components_to_activate(self, components):
        return super()._get_components_to_activate(components) + [SmartDoorComponent()]

    async def get_event_logs(
        self,
        page_size: int,
        start_id: int = 0,
    ) -> Try[TriggerLogResponse[T110Event]]:
        request = TapoRequest.get_child_event_logs(
            GetTriggerLogsParams(page_size, start_id)
        )
        response = await self.client.control_child(self._child_id, request)
        return response.flat_map(
            lambda x: TriggerLogResponse[T110Event].try_from_json(x, parse_t110_event)
        )


__all__ = ["SmartDoorSensor"]
