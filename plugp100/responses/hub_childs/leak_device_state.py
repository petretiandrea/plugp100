from dataclasses import dataclass
from typing import Any

from plugp100.common.functional.tri import Try
from plugp100.responses.hub_childs.hub_child_base_info import HubChildBaseInfo


@dataclass
class LeakDeviceState:
    base_info: HubChildBaseInfo
    in_alarm: bool
    water_leak_status: str

    @staticmethod
    def try_from_json(kwargs: dict[str, Any]) -> Try["LeakDeviceState"]:
        return HubChildBaseInfo.from_json(kwargs).flat_map(
            lambda base_info: Try.of(
                lambda: LeakDeviceState(
                    base_info=base_info,
                    in_alarm=kwargs.get("in_alarm", False),
                    water_leak_status=kwargs.get("water_leak_status"),
                )
            )
        )
