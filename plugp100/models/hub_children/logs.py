from dataclasses import dataclass
from typing import Any, Callable, Generic, List, TypeVar

from plugp100.common.functional.tri import Try

T = TypeVar("T")


@dataclass
class TriggerLogResponse(Generic[T]):
    event_start_id: int
    size: int
    events: List[T]

    @staticmethod
    def try_from_json(
        json: [str, Any], parse_log_item: Callable[[Any], T]
    ) -> Try["TriggerLogResponse[T]"]:
        return Try.of(
            lambda: TriggerLogResponse[T](
                event_start_id=json["start_id"],
                size=json["sum"],
                events=list(map(parse_log_item, json["logs"])),
            )
        )


__all__ = ["TriggerLogResponse"]
