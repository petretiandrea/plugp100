import base64
from dataclasses import dataclass
from typing import Optional, Any, Dict

import semantic_version

from plugp100.api.light_effect import LightEffect
from plugp100.common.functional.tri import Try


class DeviceState:
    pass


@dataclass
class PlugDeviceState(DeviceState):
    info: "DeviceInfo"
    device_on: bool
    on_time: int

    power_protection_status: str
    default_states: Dict

    auto_off: bool
    auto_off_time_remaining: int

    @staticmethod
    def try_from_json(kwargs: dict[str, Any]) -> Try["PlugDeviceState"]:
        return Try.of(
            lambda: PlugDeviceState(
                info=DeviceInfo(**kwargs),
                device_on=kwargs.get("device_on", False),
                power_protection_status=kwargs.get("power_protection_status"),
                on_time=kwargs.get("on_time"),
                auto_off=kwargs.get("auto_off_status") == "on",
                auto_off_time_remaining=kwargs.get("auto_off_remain_time"),
                default_states=kwargs.get("default_states"),
            )
        )


@dataclass
class LightDeviceState(DeviceState):
    info: "DeviceInfo"
    device_on: bool
    brightness: Optional[int]
    hue: Optional[int]
    saturation: Optional[int]
    color_temp: Optional[int]
    color_temp_range: Optional[tuple[int, int]]

    @staticmethod
    def try_from_json(kwargs: dict[str, Any]) -> Try["LightDeviceState"]:
        color_temp_range = tuple(kwargs.get("color_temp_range", []))
        return Try.of(
            lambda: LightDeviceState(
                info=DeviceInfo(**kwargs),
                device_on=kwargs.get("device_on", False),
                brightness=kwargs.get("brightness", None),
                hue=kwargs.get("hue", None),
                saturation=kwargs.get("saturation", None),
                color_temp=kwargs.get("color_temp", None),
                color_temp_range=None if color_temp_range == () else color_temp_range,
            )
        )


@dataclass
class LedStripDeviceState(DeviceState):
    info: "DeviceInfo"
    device_on: bool
    brightness: Optional[int]
    hue: Optional[int]
    saturation: Optional[int]
    color_temp: Optional[int]
    lighting_effect: Optional[LightEffect]
    color_temp_range: Optional[tuple[int, int]]

    @staticmethod
    def try_from_json(kwargs: dict[str, Any]) -> Try["LedStripDeviceState"]:
        color_temp_range = tuple(kwargs.get("color_temp_range", []))
        return Try.of(
            lambda: LedStripDeviceState(
                info=DeviceInfo(**kwargs),
                device_on=kwargs.get("device_on", False),
                brightness=kwargs.get("brightness", None),
                hue=kwargs.get("hue", None),
                color_temp_range=None if color_temp_range == () else color_temp_range,
                saturation=kwargs.get("saturation", None),
                color_temp=kwargs.get("color_temp", None),
                lighting_effect=LightEffect(**kwargs.get("lighting_effect"))
                if "lighting_effect" in kwargs
                else None,
            )
        )


@dataclass
class DeviceInfo:
    device_id: str
    hardware_id: str
    oem_id: str
    firmware_version: str
    hardware_version: str
    ip: Optional[str]
    mac: str
    nickname: str
    model: str
    type: str
    overheated: bool

    # wifi
    ssid: Optional[str]
    signal_level: int
    rssi: int
    friendly_name: str

    # location data
    has_set_location_info: bool
    latitude: Optional[int]
    longitude: Optional[int]
    timezone: Optional[str]
    time_difference: Optional[int]
    language: Optional[str]

    is_hardware_v2: bool = property(lambda self: self.hardware_version == "2.0")

    def __init__(self, **kwargs):
        self.device_id = kwargs["device_id"]
        self.hardware_id = kwargs["hw_id"]
        self.oem_id = kwargs["oem_id"]
        self.firmware_version = kwargs["fw_ver"]
        self.hardware_version = kwargs["hw_ver"]
        self.mac = kwargs["mac"]
        self.nickname = base64.b64decode(kwargs["nickname"]).decode("UTF-8")
        self.model = kwargs["model"]
        self.type = kwargs["type"]
        self.overheated = kwargs.get("overheated", False)
        self.ip = kwargs.get("ip")
        self.ssid = (
            base64.b64decode(kwargs["ssid"]).decode() if "ssid" in kwargs else None
        )
        self.signal_level = kwargs.get("signal_level", 0)
        self.rssi = kwargs.get("rssi", 0)
        self.friendly_name = self.model if self.nickname == "" else self.nickname

        self.has_set_location_info = kwargs.get("has_set_location_info", False)
        self.latitude = kwargs.get("latitude")
        self.longitude = kwargs.get("longitude")
        self.timezone = kwargs.get("region")
        self.time_difference = kwargs.get("time_diff")
        self.language = kwargs.get("lang")

    def get_semantic_firmware_version(self) -> semantic_version.Version:
        pieces = self.firmware_version.split("Build")
        try:
            if len(pieces) > 0:
                return semantic_version.Version(pieces[0].strip())
            else:
                return semantic_version.Version("0.0.0")
        except ValueError:
            return semantic_version.Version("0.0.0")


@dataclass
class HubDeviceState(DeviceState):
    info: "DeviceInfo"
    in_alarm: bool

    @staticmethod
    def try_from_json(kwargs: dict[str, Any]) -> Try["HubDeviceState"]:
        return Try.of(
            lambda: HubDeviceState(
                info=DeviceInfo(**kwargs),
                in_alarm=kwargs.get("in_alarm", False),
            )
        )
