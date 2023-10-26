from dataclasses import dataclass
from typing import Any, Union

from plugp100.common.functional.tri import Try
from plugp100.responses.hub_childs.hub_child_base_info import HubChildBaseInfo


@dataclass
class S200BDeviceState:
    base_info: HubChildBaseInfo
    report_interval_seconds: int  # Seconds between each report

    @staticmethod
    def try_from_json(kwargs: dict[str, Any]) -> Try["S200BDeviceState"]:
        return HubChildBaseInfo.from_json(kwargs).flat_map(
            lambda base_info: Try.of(
                lambda: S200BDeviceState(
                    base_info=base_info,
                    report_interval_seconds=kwargs.get("report_interval", 0),
                )
            )
        )


@dataclass
class RotationEvent:
    id: int
    timestamp: int
    degrees: int


@dataclass
class SingleClickEvent:
    id: int
    timestamp: int


@dataclass
class DoubleClickEvent:
    id: int
    timestamp: int


S200BEvent = Union[RotationEvent, SingleClickEvent, DoubleClickEvent]


def parse_s200b_event(item: dict[str, Any]) -> S200BEvent:
    event_type = item["event"]
    if event_type == "singleClick":
        return SingleClickEvent(item["id"], item["timestamp"])
    elif event_type == "doubleClick":
        return DoubleClickEvent(item["id"], item["timestamp"])
    else:
        return RotationEvent(
            item.get("id"), item.get("timestamp"), item.get("params")["rotate_deg"]
        )
