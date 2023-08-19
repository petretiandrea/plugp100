import logging
import uuid
from typing import cast, List

import aiohttp

from plugp100.common.functional.either import Either, Left, Right
from plugp100.common.utils.http_client import AsyncHttp
from plugp100.discovery.cloud_device_info import CloudDeviceInfo
from plugp100.discovery.local_device_finder import LocalDeviceFinder
from plugp100.responses.tapo_response import TapoResponse

logger = logging.getLogger(__name__)

_TAPO_CLOUD_URL = "https://wap.tplinkcloud.com"


class TapoDiscovery:

    async def discovery_cloud(
            self,
            username: str,
            password: str,
            http_session: aiohttp.ClientSession = None
    ) -> Either[List[CloudDeviceInfo], Exception]:
        http_client = AsyncHttp(aiohttp.ClientSession() if http_session is None else http_session)
        local_device_finder = LocalDeviceFinder()
        token = await self._login_cloud(http_client, username, password, str(uuid.uuid4()))
        if token.is_right():
            cloud_devices = (await self._get_cloud_devices(http_client, cast(Right, token).value))
            if cloud_devices.is_right():
                return Right(await self._resolve_device_mac(local_device_finder, cast(Right, cloud_devices).value))
            else:
                return cloud_devices
        return token.map(lambda _: [])

    async def _login_cloud(
            self,
            http: AsyncHttp,
            username: str,
            password: str,
            terminal_uuid: str
    ) -> Either[str, Exception]:
        try:
            login_request = {
                "method": 'login',
                "params": {
                    "appType": 'Tapo_Android',
                    "cloudUserName": username,
                    "cloudPassword": password,
                    "terminalUUID": terminal_uuid,
                },
            }

            response = await http.async_make_post(_TAPO_CLOUD_URL, login_request)
            json = await response.json(content_type=None)
            if json and json.get('error_code', -1) == 0:
                return Right(json.get('result').get('token'))
            elif json and 'msg' in json:
                return Left(Exception(json.get('msg')))
        except Exception as e:
            return Left(e)

    async def _get_cloud_devices(self, http: AsyncHttp, auth_token: str) -> Either[List[CloudDeviceInfo], Exception]:
        request = {
            "method": 'getDeviceList'
        }
        response = await http.async_make_post(f"{_TAPO_CLOUD_URL}?token={auth_token}", request)
        json = await response.json(content_type=None)
        device_list = TapoResponse.try_from_json(json).map(lambda x: x.result['deviceList'])
        if device_list.is_right():
            devices = [device for device in
                       [CloudDeviceInfo.try_from_json(device) for device in cast(Right, device_list).value] if
                       isinstance(device, Right)]
            devices = [cast(Right, device).value for device in devices]
            return Right(devices)
        return device_list.map(lambda _: [])

    async def _resolve_device_mac(self, finder: LocalDeviceFinder, devices: List[CloudDeviceInfo]) -> List[CloudDeviceInfo]:
        for device in devices:
            device.update_ip_address(await finder.get_ip_from_mac_one(device.deviceMac))

        return devices
