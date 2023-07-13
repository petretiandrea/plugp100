from dataclasses import dataclass


@dataclass
class PlayAlarmParams(object):
    alarm_duration: int
    alarm_type: str
    alarm_volume: str
