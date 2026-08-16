from dataclasses import dataclass
from typing import Any, Union


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
    if event_type == "doubleClick":
        return DoubleClickEvent(item["id"], item["timestamp"])
    return RotationEvent(
        item.get("id"), item.get("timestamp"), item.get("params")["rotate_deg"]
    )


__all__ = [
    "DoubleClickEvent",
    "RotationEvent",
    "S200BEvent",
    "SingleClickEvent",
    "parse_s200b_event",
]
