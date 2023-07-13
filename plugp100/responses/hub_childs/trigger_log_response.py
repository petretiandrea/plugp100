from dataclasses import dataclass
from typing import TypeVar, List, Generic, Any, Callable

T = TypeVar("T")


@dataclass
class TriggerLogResponse(Generic[T]):
    event_start_id: int
    size: int
    events: List[T]

    @staticmethod
    def try_from_json(json: [str, Any], parse_log_item: Callable[[Any], T]) -> 'TriggerLogResponse[T]':
        return TriggerLogResponse[T](
            event_start_id=json['start_id'],
            size=json['sum'],
            events=list(map(parse_log_item, json['logs']))
        )
