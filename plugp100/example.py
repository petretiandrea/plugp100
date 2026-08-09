import asyncio
import logging
import os

from dotenv import load_dotenv

from plugp100.common.credentials import AuthCredential
from plugp100.discovery.tapo_discovery import TapoDiscovery
from plugp100.devices.device_factory import connect, DeviceConnectConfiguration


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


# Example get device from discovery
async def example_discovery(credentials: AuthCredential):
    discovered = await TapoDiscovery.scan(timeout=5)
    for discovered_device in discovered:
        try:
            device = await discovered_device.get_tapo_device(credentials)
            await device.update()
            print(
                {
                    "type": type(device),
                    "protocol": device.protocol_version,
                    "raw_state": device.raw_state,
                }
            )
            await device.client.close()
        except Exception as e:
            logging.error(
                f"Failed to update {discovered_device.ip} {discovered_device.device_type}",
                exc_info=e,
            )


# Example by knowing protocol details and device class
async def example_connect_knowing_device_and_protocol(
    credentials: AuthCredential, host: str
):
    device_configuration = DeviceConnectConfiguration(
        host=host,
        credentials=credentials,
        device_type="SMART.TAPOPLUG",
        encryption_type="tpap",
    )
    device = await connect(device_configuration)
    await device.update()
    print(
        {
            "type": type(device),
            "protocol": device.protocol_version,
            "raw_state": device.raw_state,
            "components": device.get_device_components,
        }
    )
    await device.client.close()


# Example without knowing device class and protocol. The library will try
# to get info to establish protocol and device class
async def example_connect_by_guessing(credentials: AuthCredential, host: str):
    device_configuration = DeviceConnectConfiguration(host=host, credentials=credentials)
    device = await connect(device_configuration)
    await device.update()
    print(
        {
            "type": type(device),
            "protocol": device.protocol_version,
            "raw_state": device.raw_state,
            "components": device.get_device_components,
        }
    )
    await device.client.close()


async def main():
    load_dotenv()
    credentials = AuthCredential(
        required_env("TAPO_USERNAME"), required_env("TAPO_PASSWORD")
    )
    host = required_env("TAPO_DEVICE_IP")
    await example_discovery(credentials)
    await example_connect_knowing_device_and_protocol(credentials, host)
    await example_connect_by_guessing(credentials, host)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(asyncio.sleep(0.1))
    loop.close()
