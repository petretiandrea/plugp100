from dataclasses import dataclass
from typing import Any

from plugp100.common.functional.tri import Try
from plugp100.responses.hub_childs.hub_child_base_info import HubChildBaseInfo


@dataclass
class T100MotionSensorState:
    base_info: HubChildBaseInfo
    report_interval_seconds: int  # Seconds between each report
    detected: bool

    @staticmethod
    def from_json(kwargs: dict[str, Any]) -> Try["T100MotionSensorState"]:
        return HubChildBaseInfo.from_json(kwargs).flat_map(
            lambda base_info: Try.of(
                lambda: T100MotionSensorState(
                    base_info=base_info,
                    report_interval_seconds=kwargs.get("report_interval", 0),
                    detected=kwargs.get("detected"),
                )
            )
        )


@dataclass
class MotionDetectedEvent:
    id: int
    timestamp: int


T100Event = MotionDetectedEvent


def parse_t100_event(item: dict[str, Any]) -> T100Event:
    return MotionDetectedEvent(item["id"], item["timestamp"])
