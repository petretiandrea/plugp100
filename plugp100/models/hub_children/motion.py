from dataclasses import dataclass
from typing import Any


@dataclass
class MotionDetectedEvent:
    id: int
    timestamp: int


T100Event = MotionDetectedEvent


def parse_t100_event(item: dict[str, Any]) -> T100Event:
    return MotionDetectedEvent(item["id"], item["timestamp"])


__all__ = ["MotionDetectedEvent", "T100Event", "parse_t100_event"]
