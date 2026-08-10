---
title: Discovery
sidebar_position: 3
---

# Discovery

The library supports local network discovery and then a second step to connect to the discovered device.

## Scan the local network

```python
import asyncio

from plugp100 import TapoDiscovery


async def main():
    devices = await TapoDiscovery.scan(timeout=5)
    for device in devices:
        print(device.ip, device.device_type, device.device_model)


asyncio.run(main())
```

`TapoDiscovery.scan(...)` returns a list of `DiscoveredDevice`.

## Connect a discovered device

```python
import asyncio

from plugp100 import AuthCredential, TapoDiscovery, connect_discovered_device


async def main():
    credentials = AuthCredential("your-email", "your-password")
    discovered_devices = await TapoDiscovery.scan(timeout=5)

    for discovered in discovered_devices:
        device = await connect_discovered_device(discovered, credentials)
        await device.update()

        print(type(device).__name__, device.protocol_version, device.nickname)

        await device.client.close()


asyncio.run(main())
```

## Discovery result model

`DiscoveredDevice` contains normalized metadata such as:

- `device_type`
- `device_model`
- `ip`
- `mac`
- `device_id`
- `mgt_encrypt_schm`

If the device exposes encryption schema data, it is available in `EncryptionSchema`.

## Single device scan

```python
device = await TapoDiscovery.single_scan("192.168.1.10", timeout=5)
```

This is useful when you want to probe one IP instead of broadcasting on the whole network.
