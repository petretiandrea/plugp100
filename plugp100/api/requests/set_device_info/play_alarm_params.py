from dataclasses import dataclass
from typing import Optional


@dataclass
class PlayAlarmParams(object):
    alarm_duration: Optional[int] = None
    alarm_type: Optional[str] = None
    alarm_volume: Optional[str] = None
