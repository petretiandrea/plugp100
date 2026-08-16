import dataclasses
import enum
from typing import Any


@dataclasses.dataclass
class LatestFirmware:
    type: str
    firmware_version: str
    release_date: str
    release_note: str
    firmware_size: int
    need_to_upgrade: bool

    @staticmethod
    def from_json(data: dict[str, Any]) -> "LatestFirmware":
        return LatestFirmware(
            type=data.get("type"),
            firmware_version=data.get("fw_ver"),
            release_date=data.get("release_date"),
            release_note=data.get("release_note"),
            firmware_size=data.get("fw_size"),
            need_to_upgrade=data.get("need_to_upgrade", False),
        )


class FirmwareDownloadStatus(enum.Enum):
    IDLE = 0
    PREPARING = 1
    DOWNLOADING = 2
    DOWNLOADED = 3
    NOT_TRANSFERRED = 4
    DOWNLOAD_FAIL = -1001
    CHECK_FAIL = -1002
    TRANSFER_FAIL = -1003
    LOW_BATTERY = -1004


@dataclasses.dataclass
class FirmwareDownloadProgress:
    status: FirmwareDownloadStatus
    download_in_progress: int
    reboot_time: int
    upgrade_time: int
    auto_upgrade: int

    @staticmethod
    def from_json(data: dict[str, Any]) -> "FirmwareDownloadProgress":
        return FirmwareDownloadProgress(
            status=FirmwareDownloadStatus(data.get("status", 0)),
            download_in_progress=data.get("download_progress", 0),
            reboot_time=data.get("reboot_time", 0),
            upgrade_time=data.get("upgrade_time", 0),
            auto_upgrade=data.get("auto_upgrade", False),
        )
