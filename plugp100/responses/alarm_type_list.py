from dataclasses import dataclass
from typing import List, Any

from plugp100.common.functional.either import Left, Right, Either


@dataclass
class AlarmTypeList(object):
    tones: List[str]

    @staticmethod
    def try_from_json(kwargs: dict[str, Any]) -> Either["AlarmTypeList", Exception]:
        try:
            return Right(
                AlarmTypeList(
                    kwargs.get("alarm_type_list", []),
                )
            )
        except Exception as e:
            return Left(e)
