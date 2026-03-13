import logging
from typing import Optional

import aiohttp

from plugp100.common.credentials import AuthCredential
from plugp100.devices.base import TapoDevice
from plugp100.devices.factory import DeviceConnectConfiguration, connect
from plugp100.models.discovery import DiscoveredDevice


async def connect_discovered_device(
    discovered_device: DiscoveredDevice,
    credentials: AuthCredential,
    session: Optional[aiohttp.ClientSession] = None,
) -> TapoDevice:
    if encrypt_schema := discovered_device.mgt_encrypt_schm:
        port = (
            encrypt_schema.http_port or 443
            if encrypt_schema.is_support_https
            else encrypt_schema.http_port
        )
        config = DeviceConnectConfiguration(
            host=discovered_device.ip,
            port=port,
            credentials=credentials,
            device_type=discovered_device.device_type,
            encryption_type=encrypt_schema.encrypt_type,
            encryption_version=encrypt_schema.lv,
        )
    else:
        logging.warning(
            "No encryption schema found for discovered device %s %s",
            discovered_device.ip,
            discovered_device.device_type,
        )
        config = DeviceConnectConfiguration(
            host=discovered_device.ip,
            port=80,
            device_type=discovered_device.device_type,
            credentials=credentials,
        )
    return await connect(config, session)


__all__ = ["connect_discovered_device"]
