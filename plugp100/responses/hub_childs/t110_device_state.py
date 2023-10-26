from dataclasses import dataclass
from typing import Any, Union

from plugp100.common.functional.tri import Try
from plugp100.responses.hub_childs.hub_child_base_info import HubChildBaseInfo


@dataclass
class T110SmartDoorState:
    base_info: HubChildBaseInfo
    report_interval_seconds: int  # Seconds between each report
    is_open: bool

    @staticmethod
    def try_from_json(kwargs: dict[str, Any]) -> Try["T110SmartDoorState"]:
        return HubChildBaseInfo.from_json(kwargs).flat_map(
            lambda base_info: Try.of(
                lambda: T110SmartDoorState(
                    base_info=base_info,
                    report_interval_seconds=kwargs.get("report_interval", 0),
                    is_open=kwargs.get("open"),
                )
            )
        )


@dataclass
class OpenEvent:
    id: int
    timestamp: int


@dataclass
class CloseEvent:
    id: int
    timestamp: int


T110Event = Union[OpenEvent, CloseEvent]


def parse_t110_event(item: dict[str, Any]) -> T110Event:
    event_type = item["event"]
    if event_type == "close":
        return CloseEvent(item["id"], item["timestamp"])
    else:
        return OpenEvent(item.get("id"), item.get("timestamp"))
