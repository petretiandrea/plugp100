import base64
from dataclasses import dataclass
from typing import Any, Union

import semantic_version

from plugp100.common.functional.either import Either, Right, Left

@dataclass
class T110SmartDoorState:
    hardware_version: str
    firmware_version: str
    device_id: str
    parent_device_id: str
    mac: str
    type: str
    model: str
    status: str
    rssi: int
    signal_level: int
    at_low_battery: bool
    nickname: str
    last_onboarding_timestamp: int
    report_interval_seconds: int  # Seconds between each report
    is_open: bool

    @staticmethod
    def try_from_json(kwargs: dict[str, Any]) -> Either['T110SmartDoorState', Exception]:
        try:
            return Right(T110SmartDoorState(
                firmware_version=kwargs["fw_ver"],
                hardware_version=kwargs["hw_ver"],
                device_id=kwargs['device_id'],
                parent_device_id=kwargs['parent_device_id'],
                mac=kwargs["mac"],
                type=kwargs["type"],
                model=kwargs["model"],
                status=kwargs.get("status", False),
                rssi=kwargs.get("rssi", 0),
                signal_level=kwargs.get("signal_level", 0),
                at_low_battery=kwargs.get('at_low_battery', False),
                nickname=base64.b64decode(kwargs["nickname"]).decode("UTF-8"),
                last_onboarding_timestamp=kwargs.get('lastOnboardingTimestamp', 0),
                report_interval_seconds=kwargs.get('report_interval', 0),
                is_open=kwargs.get('open')
            ))
        except Exception as e:
            return Left(e)

    def get_semantic_firmware_version(self) -> semantic_version.Version:
        pieces = self.firmware_version.split("Build")
        try:
            if len(pieces) > 0:
                return semantic_version.Version(pieces[0].strip())
            else:
                return semantic_version.Version('0.0.0')
        except ValueError:
            return semantic_version.Version('0.0.0')


@dataclass
class OpenEvent:
    id: int
    timestamp: int


@dataclass
class CloseEvent:
    id: int
    timestamp: int


T110Event = Union[OpenEvent, CloseEvent]


def parse_t110_event(item: dict[str, Any]) -> T110Event:
    event_type = item['event']
    if event_type == 'close':
        return CloseEvent(item['id'], item['timestamp'])
    else:
        return OpenEvent(item.get('id'), item.get('timestamp'))
