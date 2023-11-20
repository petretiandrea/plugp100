from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from plugp100.responses.temperature_unit import TemperatureUnit
from plugp100.responses.hub_childs.hub_child_base_info import HubChildBaseInfo

from plugp100.common.functional.tri import Try


class TRVState(Enum):
    HEATING = "heating"
    OFF = ""


@dataclass
class KE100DeviceState:
    base_info: HubChildBaseInfo

    trv_state: TRVState
    temperature_unit: TemperatureUnit
    current_temperature: float
    target_temperature: float

    temperature_offset: int
    min_control_temperature: int
    max_control_temperature: int

    battery_percentage: int
    frost_protection_on: bool
    child_protection: bool

    @staticmethod
    def from_json(kwargs: "dict[str, Any]") -> Try["KE100DeviceState"]:
        return HubChildBaseInfo.from_json(kwargs).flat_map(
            lambda base_info: Try.of(
                lambda: KE100DeviceState(**kwargs, base_info=base_info)
            ),
        )

    def __init__(self, **kwargs):
        self.base_info = kwargs["base_info"]
        self.current_temperature = kwargs.get("current_temp")
        self.target_temperature = kwargs["target_temp"]
        self.temperature_offset = kwargs["temp_offset"]
        self.min_control_temperature = kwargs["min_control_temp"]
        self.max_control_temperature = kwargs["max_control_temp"]
        self.battery_percentage = kwargs["battery_percentage"]
        self.frost_protection_on = kwargs["frost_protection_on"]
        self.child_protection = kwargs["child_protection"]
        self.temperature_unit = next(
            [
                member
                for member in TemperatureUnit
                if member.value == kwargs.get("temp_unit")
            ].__iter__(),
            TemperatureUnit.CELSIUS,
        )
        self.trv_state = next(
            [
                member
                for member in TRVState
                if kwargs.get("trv_states")
                and member.value == kwargs.get("trv_states")[0]
            ].__iter__(),
            None,
        )
