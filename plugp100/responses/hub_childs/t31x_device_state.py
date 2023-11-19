import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from plugp100.common.functional.tri import Try
from plugp100.responses.hub_childs.hub_child_base_info import HubChildBaseInfo
from plugp100.responses.temperature_unit import TemperatureUnit


@dataclass
class T31DeviceState:
    base_info: HubChildBaseInfo
    report_interval_seconds: int  # Seconds between each report

    current_humidity: int
    current_humidity_exception: int

    current_temperature: float
    current_temperature_exception: float

    temperature_unit: TemperatureUnit

    @staticmethod
    def from_json(kwargs: dict[str, Any]) -> Try["T31DeviceState"]:
        return HubChildBaseInfo.from_json(kwargs).flat_map(
            lambda base_info: Try.of(
                lambda: T31DeviceState(**kwargs, base_info=base_info)
            )
        )

    def __init__(self, **kwargs):
        self.base_info = kwargs["base_info"]
        self.report_interval_seconds = kwargs.get("report_interval", 0)
        self.current_humidity = kwargs.get("current_humidity")
        self.current_humidity_exception = kwargs.get("current_humidity_exception")
        self.current_temperature = kwargs.get("current_temp")
        self.current_temperature_exception = kwargs.get("current_temp_exception")
        self.temperature_unit = next(
            [
                member
                for member in TemperatureUnit
                if member.value == kwargs.get("temp_unit")
            ].__iter__(),
            TemperatureUnit.CELSIUS,
        )


@dataclass
class TemperatureHumidityRecordsRaw:
    local_time: datetime
    past24h_humidity_exceptions: list[int]
    past24h_humidity: list[int]
    past24_temperature_exceptions: list[float]
    past24_temperature: list[float]

    @staticmethod
    def from_json(kwargs: dict[str, Any]) -> Try["TemperatureHumidityRecordsRaw"]:
        return Try.of(lambda: TemperatureHumidityRecordsRaw(**kwargs))

    def __init__(self, **kwargs):
        self.local_time = datetime.fromtimestamp(kwargs.get("local_time"))
        self.past24_temperature = kwargs.get("past24h_temp", [])
        self.past24_temperature_exceptions = kwargs.get("past24h_temp_exception", [])
        self.past24h_humidity = kwargs.get("past24h_humidity", [])
        self.past24h_humidity_exceptions = kwargs.get("past24h_humidity_exception", [])
