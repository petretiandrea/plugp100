import uuid
from dataclasses import dataclass
from typing import List, Optional, Any, cast

import aiohttp

from plugp100.common.functional.tri import Try, Failure
from plugp100.common.utils.http_client import AsyncHttp
from plugp100.responses.tapo_response import TapoResponse

_TAPO_CLOUD_URL = "https://wap.tplinkcloud.com"


class CloudClient:
    async def get_devices(
        self, username: str, password: str, http_session: aiohttp.ClientSession
    ) -> Try[List["CloudDeviceInfo"]]:
        http_client = AsyncHttp(http_session)
        token = await self._login_cloud(
            http_client, username, password, str(uuid.uuid4())
        )
        if token.is_success():
            return await self._get_cloud_devices(http_client, token.value)

        return token.map(lambda _: [])

    async def _login_cloud(
        self, http: AsyncHttp, username: str, password: str, terminal_uuid: str
    ) -> Try[str]:
        try:
            login_request = {
                "method": "login",
                "params": {
                    "appType": "Tapo_Android",
                    "cloudUserName": username,
                    "cloudPassword": password,
                    "terminalUUID": terminal_uuid,
                },
            }

            response = await http.async_make_post(_TAPO_CLOUD_URL, login_request)
            json = await response.json(content_type=None)
            if json and json.get("error_code", -1) == 0:
                return Try.of(json.get("result").get("token"))
            elif json and "msg" in json:
                return Failure(Exception(json.get("msg")))
        except Exception as e:
            return Try.of(e)

    async def _get_cloud_devices(
        self, http: AsyncHttp, auth_token: str
    ) -> Try[List["CloudDeviceInfo"]]:
        request = {"method": "getDeviceList"}
        response = await http.async_make_post(
            f"{_TAPO_CLOUD_URL}?token={auth_token}", request
        )
        json = await response.json(content_type=None)
        device_list = TapoResponse.try_from_json(json).map(
            lambda x: x.result["deviceList"]
        )
        if device_list.is_success():
            devices = [
                device
                for device in [
                    CloudDeviceInfo.try_from_json(device) for device in device_list.value
                ]
                if device.is_success()
            ]
            devices = [device.value for device in devices]
            return Try.of(devices)
        return device_list.map(lambda _: [])


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
    def try_from_json(kwargs: dict[str, Any]) -> Try["CloudDeviceInfo"]:
        return Try.of(
            lambda: CloudDeviceInfo(
                deviceType=kwargs.get("deviceType"),
                role=cast(int, kwargs.get("role")),
                fwVer=kwargs.get("fwVer"),
                appServerUrl=kwargs.get("appServerUrl"),
                deviceRegion=kwargs.get("deviceRegion"),
                deviceId=kwargs.get("deviceId"),
                deviceName=kwargs.get("deviceName"),
                deviceHwVer=kwargs.get("deviceHwVer"),
                alias=kwargs.get("alias"),
                deviceMac=kwargs.get("deviceMac"),
                oemId=kwargs.get("oemId"),
                deviceModel=kwargs.get("deviceModel"),
                hwId=kwargs.get("hwId"),
                fwId=kwargs.get("fwId"),
                isSameRegion=cast(bool, kwargs.get("isSameRegion")),
                status=cast(int, kwargs.get("status")),
                ipAddress=kwargs.get("ipAddress", None),
            )
        )

    def update_ip_address(self, address: str):
        self.ipAddress = address
