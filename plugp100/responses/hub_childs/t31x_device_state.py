import base64
import enum
from dataclasses import dataclass
from datetime import time, datetime
from typing import Any

import semantic_version

from plugp100.common.functional.either import Either, Right, Left


class TemperatureUnit(enum.Enum):
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"


@dataclass
class T31DeviceState:
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

    current_humidity: int
    current_humidity_exception: int

    current_temperature: float
    current_temperature_exception: float

    temperature_unit: TemperatureUnit

    @staticmethod
    def from_json(kwargs: dict[str, Any]) -> Either['T31DeviceState', Exception]:
        try:
            return Right(T31DeviceState(**kwargs))
        except Exception as e:
            return Left(e)

    def __init__(self, **kwargs):
        self.firmware_version = kwargs["fw_ver"]
        self.hardware_version = kwargs["hw_ver"]
        self.device_id = kwargs['device_id']
        self.parent_device_id = kwargs['parent_device_id']
        self.mac = kwargs["mac"]
        self.type = kwargs["type"]
        self.model = kwargs["model"]
        self.status = kwargs.get("status", False)
        self.rssi = kwargs.get("rssi", 0)
        self.signal_level = kwargs.get("signal_level", 0)
        self.at_low_battery = kwargs.get('at_low_battery', False)
        self.nickname = base64.b64decode(kwargs["nickname"]).decode("UTF-8")
        self.last_onboarding_timestamp = kwargs.get('lastOnboardingTimestamp', 0)
        self.report_interval_seconds = kwargs.get('report_interval', 0)
        self.current_humidity = kwargs.get('current_humidity')
        self.current_humidity_exception = kwargs.get('current_humidity_exception')
        self.current_temperature = kwargs.get('current_temp')
        self.current_temperature_exception = kwargs.get('current_temp_exception')
        self.temperature_unit = next([member for member in TemperatureUnit if member.value == kwargs.get('temp_unit')],
                                     TemperatureUnit.CELSIUS)

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
class TemperatureHumidityRecordsRaw:
    local_time: datetime
    past24h_humidity_exceptions: list[int]
    past24h_humidity: list[int]
    past24_temperature_exceptions: list[float]
    past24_temperature: list[float]
    temperature_unit: TemperatureUnit

    @staticmethod
    def from_json(kwargs: dict[str, Any]) -> Either['TemperatureHumidityRecordsRaw', Exception]:
        try:
            return Right(TemperatureHumidityRecordsRaw(**kwargs))
        except Exception as e:
            return Left(e)

    def __init__(self, **kwargs):
        self.local_time = datetime.fromtimestamp(kwargs.get('local_time'))
        self.past24_temperature = kwargs.get('past24h_temp', [])
        self.past24_temperature_exceptions = kwargs.get('past24h_temp_exception', [])
        self.past24h_humidity = kwargs.get('past24h_humidity', [])
        self.past24h_humidity_exceptions = kwargs.get('past24h_humidity_exception', [])
