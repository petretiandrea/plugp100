from dataclasses import dataclass
from typing import Any, Union


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
    return OpenEvent(item.get("id"), item.get("timestamp"))


__all__ = ["CloseEvent", "OpenEvent", "T110Event", "parse_t110_event"]
