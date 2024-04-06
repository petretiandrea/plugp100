# Plug P100
This is a fork of original work of [@K4CZP3R](https://github.com/K4CZP3R/tapo-p100-python)

The purpose of this fork is to provide the library as PyPi package. 

# How to install
```pip install plugp100```

## Library Architecture
The library was rewritten by taking inspiration from [Component Gaming Design Pattern](https://gameprogrammingpatterns.com/component.html) to achieve better decoupling from device and its capabilities.
Each Tapo Device, now, is something like a container of Device Component. A Device Component represent a specific feature, so a Tapo Device can be composed by multiple device component.
e.g. `EnergyComponent`, `OverheatComponent`, `OnOffComponent` and so on.

There 3 main Tapo Device class family, which simplify access to underlying components:
- TapoBulb
- TapoPlug
- TapoHub


## Supported Devices

This library supports a wide range of Tapo devices, including:

- Tapo Smart Plugs
- Tapo Smart Plug Strip
- Tapo Smart Led Strip
- Tapo Smart Bulb
- Tapo HUB H100
  - Water Leak
  - Trigger Button (like S200)
  - Switch
  - Smart Door
  - Temperature Humidity Sensor

Every device class has more than one component which enrich the basic capability of Tapo Device. 
You can see the supported components inside `plugp100/new/components` package.


## Usage

Replace `<tapo_username>`, `<tapo_password>`, and `<tapo_device_ip>` with your Tapo account credentials and device IP address.

### Authentication

Before using the library, make sure to have your Tapo credentials ready:

```python
from plugp100.common.credentials import AuthCredential

credentials = AuthCredential("<tapo_username>", "<tapo_password>")
```

### Example: Discovery

Use the library to discover Tapo devices on the network:

```python
import asyncio
import logging
from plugp100.common.credentials import AuthCredential
from plugp100.discovery.tapo_discovery import TapoDiscovery

async def example_discovery(credentials: AuthCredential):
    discovered = await TapoDiscovery.scan(timeout=5)
    for discovered_device in discovered:
        try:
            device = await discovered_device.get_tapo_device(credentials)
            await device.update()
            print({
                'type': type(device),
                'protocol': device.protocol_version,
                'raw_state': device.raw_state
            })
            await device.client.close()
        except Exception as e:
            logging.error(f"Failed to update {discovered_device.ip} {discovered_device.device_type}", exc_info=e)

async def main():
    credentials = AuthCredential("<tapo_username>", "<tapo_password>")
    await example_discovery(credentials)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(asyncio.sleep(0.1))
    loop.close()
```

### Example: Connecting by only ip address

Connect to a Tapo device without knowing its device type and protocol. The library will try to guess:

```python
import asyncio
from plugp100.common.credentials import AuthCredential
from plugp100.new.device_factory import connect, DeviceConnectConfiguration

async def example_connect_by_guessing(credentials: AuthCredential, host: str):
    device_configuration = DeviceConnectConfiguration(
        host=host,
        credentials=credentials
    )
    device = await connect(device_configuration)
    await device.update()
    print({
        'type': type(device),
        'protocol': device.protocol_version,
        'raw_state': device.raw_state,
        'components': device.get_device_components
    })

async def main():
    credentials = AuthCredential("<tapo_username>", "<tapo_password>")
    await example_connect_by_guessing(credentials, "<tapo_device_ip>")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(asyncio.sleep(0.1))
    loop.close()
```

### Example: Connecting by knowing Protocol

Connect to a Tapo device with known device type and protocol details:

```python
import asyncio
from plugp100.common.credentials import AuthCredential
from plugp100.new.device_factory import connect, DeviceConnectConfiguration

async def example_connect_knowing_device_and_protocol(credentials: AuthCredential, host: str):
    device_configuration = DeviceConnectConfiguration(
        host=host,
        credentials=credentials,
        device_type="SMART.TAPOPLUG",
        encryption_type="klap",
        encryption_version=2
    )
    device = await connect(device_configuration)
    await device.update()
    print({
        'type': type(device),
        'protocol': device.protocol_version,
        'raw_state': device.raw_state,
        'components': device.get_device_components
    })

async def main():
    credentials = AuthCredential("<tapo_username>", "<tapo_password>")
    await example_connect_knowing_device_and_protocol(credentials, "<tapo_device_ip>")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(asyncio.sleep(0.1))
    loop.close()
```



## Supported Protocols

- Klap v1
- Klap v2
- Passthorugh
- Ipcamera-like?! (work in progress hub H200)
