import dataclasses
from typing import Dict, Any

from plugp100.common.functional.either import Right, Either, Left


@dataclasses.dataclass
class Usage:
    today: float
    past7_days: float
    past30_days: float

    def __init__(self, info: Dict[str, Any]):
        self.today = info.get("today", -1.0)
        self.past7_days = info.get("past7", -1.0)
        self.past30_days = info.get("past30", -1.0)


@dataclasses.dataclass
class DeviceUsageInfo:
    time_usage: Usage
    power_usage: Usage
    saved_power: Usage

    @staticmethod
    def try_from_json(kwargs: dict[str, Any]) -> Either["DeviceUsageInfo", Exception]:
        try:
            return Right(
                DeviceUsageInfo(
                    time_usage=Usage(kwargs.get("time_usage", {})),
                    power_usage=Usage(kwargs.get("power_usage", {})),
                    saved_power=Usage(kwargs.get("saved_power", {})),
                )
            )
        except Exception as e:
            return Left(e)
