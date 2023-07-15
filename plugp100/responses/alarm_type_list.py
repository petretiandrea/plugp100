from dataclasses import dataclass
from typing import List, Any


@dataclass
class AlarmTypeList(object):
    tones: List[str]

    @staticmethod
    def try_from_json(kwargs: dict[str, Any]):
        return AlarmTypeList(
            kwargs.get('alarm_type_list', []),
        )
