import dataclasses
from typing import Any
from datetime import datetime
import pytz

from plugp100.common.functional.either import Right, Either, Left

@dataclasses.dataclass
class TimeInfo:
    time_diff: int
    timestamp: int
    region: str

    def local_time(self) -> datetime:
        """Return datetime object using the given """
        return datetime.fromtimestamp(self.timestamp, tz=pytz.timezone(self.region))

    @staticmethod
    def try_from_json(kwargs: dict[str, Any]) -> Either['TimeInfo', Exception]:
        try:
            return Right(TimeInfo(
                time_diff=kwargs.get('time_diff'),
                timestamp=kwargs.get('timestamp'),
                region=kwargs.get('region')
            ))
        except Exception as e:
            return Left(e)
