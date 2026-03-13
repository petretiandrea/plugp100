from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.api.requests.trigger_logs_params import GetTriggerLogsParams
from plugp100.common.functional.tri import Try
from plugp100.components.motion_sensor import MotionSensorComponent
from plugp100.devices.children.base import TapoHubChildDevice
from plugp100.models.hub_children.logs import TriggerLogResponse
from plugp100.models.hub_children.motion import T100Event, parse_t100_event


class MotionSensor(TapoHubChildDevice):
    def _get_components_to_activate(self, components):
        return super()._get_components_to_activate(components) + [MotionSensorComponent()]

    async def get_event_logs(
        self,
        page_size: int,
        start_id: int = 0,
    ) -> Try[TriggerLogResponse[T100Event]]:
        request = TapoRequest.get_child_event_logs(
            GetTriggerLogsParams(page_size, start_id)
        )
        return (await self.client.control_child(self._child_id, request)).flat_map(
            lambda x: TriggerLogResponse[T100Event].try_from_json(x, parse_t100_event)
        )

    @property
    def is_detected(self) -> bool:
        return self.get_component(MotionSensorComponent).detected


__all__ = ["MotionSensor"]
