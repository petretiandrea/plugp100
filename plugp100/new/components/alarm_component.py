from typing import Any

from plugp100.api.requests.set_device_info.play_alarm_params import PlayAlarmParams
from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.tri import Try
from plugp100.common.utils.json_utils import dataclass_encode_json
from plugp100.new.components.device_component import DeviceComponent
from plugp100.responses.alarm_type_list import AlarmTypeList


class AlarmComponent(DeviceComponent):
    def __init__(self, client: TapoClient):
        self._client = client
        self._alarm_on = False

    @property
    def is_alarm_on(self) -> bool:
        return self._alarm_on

    async def update(self, current_state: dict[str, Any] | None = None):
        self._alarm_on = current_state.get("in_alarm", False)

    async def turn_alarm_on(self, alarm: PlayAlarmParams = None) -> Try[bool]:
        request = TapoRequest(
            method="play_alarm",
            params=dataclass_encode_json(alarm) if alarm is not None else None,
        )
        return (await self._client.execute_raw_request(request)).map(lambda _: True)

    async def turn_alarm_off(self) -> Try[bool]:
        return (
            await self._client.execute_raw_request(
                TapoRequest(method="stop_alarm", params=None)
            )
        ).map(lambda _: True)

    async def get_supported_alarm_tones(self) -> Try[AlarmTypeList]:
        return (
            await self._client.execute_raw_request(
                TapoRequest(method="get_support_alarm_type_list", params=None)
            )
        ).flat_map(AlarmTypeList.try_from_json)
