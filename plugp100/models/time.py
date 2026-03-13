import dataclasses
from datetime import datetime
from typing import Any

from plugp100.common.functional.tri import Try


@dataclasses.dataclass
class TimeInfo:
    time_diff: int
    timestamp: int
    region: str

    def local_time(self) -> datetime:
        from zoneinfo import ZoneInfo

        return datetime.fromtimestamp(self.timestamp, tz=ZoneInfo(self.region))

    @staticmethod
    def try_from_json(kwargs: dict[str, Any]) -> Try["TimeInfo"]:
        return Try.of(
            lambda: TimeInfo(
                time_diff=kwargs.get("time_diff"),
                timestamp=kwargs.get("timestamp"),
                region=kwargs.get("region"),
            )
        )
