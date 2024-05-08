import asyncio
import logging

from plugp100.common.credentials import AuthCredential
from plugp100.discovery.tapo_discovery import TapoDiscovery
from plugp100.new.device_factory import connect, DeviceConnectConfiguration


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
        encryption_type="klap",
        encryption_version=2,
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


async def main():
    credentials = AuthCredential("<tapo_username>", "<tapo_password>")
    await example_discovery(credentials)
    await example_connect_knowing_device_and_protocol(credentials, "<tapo_device_ip>")
    await example_connect_by_guessing(credentials, "<tapo_device_ip>")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(asyncio.sleep(0.1))
    loop.close()
