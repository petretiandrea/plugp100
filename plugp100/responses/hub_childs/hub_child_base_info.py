import base64
from typing import Any

import semantic_version

from plugp100.common.functional.tri import Try


class HubChildBaseInfo:
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

    @staticmethod
    def from_json(kwargs: dict[str, Any]) -> Try["HubChildBaseInfo"]:
        return Try.of(lambda: HubChildBaseInfo(**kwargs))

    def __init__(self, **kwargs):
        self.firmware_version = kwargs["fw_ver"]
        self.hardware_version = kwargs["hw_ver"]
        self.device_id = kwargs["device_id"]
        self.parent_device_id = kwargs["parent_device_id"]
        self.mac = kwargs["mac"]
        self.type = kwargs["type"]
        self.model = kwargs["model"]
        self.status = kwargs.get("status", False)
        self.rssi = kwargs.get("rssi", 0)
        self.signal_level = kwargs.get("signal_level", 0)
        self.at_low_battery = kwargs.get("at_low_battery", False)
        self.nickname = base64.b64decode(kwargs["nickname"]).decode("UTF-8")
        self.last_onboarding_timestamp = kwargs.get("lastOnboardingTimestamp", 0)

    def get_semantic_firmware_version(self) -> semantic_version.Version:
        pieces = self.firmware_version.split("Build")
        try:
            if len(pieces) > 0:
                return semantic_version.Version(pieces[0].strip())
            else:
                return semantic_version.Version("0.0.0")
        except ValueError:
            return semantic_version.Version("0.0.0")
