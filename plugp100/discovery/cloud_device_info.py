from dataclasses import dataclass
from typing import Optional, Any, cast

from plugp100.common.functional.either import Right, Either, Left


@dataclass
class CloudDeviceInfo:
    deviceType: str
    role: int
    fwVer: str
    appServerUrl: str
    deviceRegion: str
    deviceId: str
    deviceName: str
    deviceHwVer: str
    alias: str
    deviceMac: str
    oemId: str
    deviceModel: str
    hwId: str
    fwId: str
    isSameRegion: bool
    status: int
    ipAddress: Optional[str]

    @staticmethod
    def try_from_json(kwargs: dict[str, Any]) -> Either['CloudDeviceInfo', Exception]:
        try:
            return Right(
                CloudDeviceInfo(
                    deviceType=kwargs.get('deviceType'),
                    role=cast(int, kwargs.get('role')),
                    fwVer=kwargs.get('fwVer'),
                    appServerUrl=kwargs.get('appServerUrl'),
                    deviceRegion=kwargs.get('deviceRegion'),
                    deviceId=kwargs.get('deviceId'),
                    deviceName=kwargs.get('deviceName'),
                    deviceHwVer=kwargs.get('deviceHwVer'),
                    alias=kwargs.get('alias'),
                    deviceMac=kwargs.get('deviceMac'),
                    oemId=kwargs.get('oemId'),
                    deviceModel=kwargs.get('deviceModel'),
                    hwId=kwargs.get('hwId'),
                    fwId=kwargs.get('fwId'),
                    isSameRegion=cast(bool, kwargs.get('isSameRegion')),
                    status=cast(int, kwargs.get('status')),
                    ipAddress=kwargs.get('ipAddress', None),
                )
            )
        except Exception as e:
            return Left(e)

    def update_ip_address(self, address: str):
        self.ipAddress = address
