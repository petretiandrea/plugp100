---
title: Getting Started
sidebar_position: 2
---

# Getting Started

## Install

```bash
pip install plugp100
```

## Create credentials

```python
from plugp100 import AuthCredential

credentials = AuthCredential("your-email", "your-password")
```

## Connect when you only know the device IP

```python
import asyncio

from plugp100 import AuthCredential, DeviceConnectConfiguration, connect


async def main():
    credentials = AuthCredential("your-email", "your-password")
    config = DeviceConnectConfiguration(
        host="192.168.1.10",
        credentials=credentials,
    )

    device = await connect(config)
    await device.update()

    print(type(device).__name__)
    print(device.protocol_version)
    print(device.nickname)

    await device.client.close()


asyncio.run(main())
```

## Connect when you already know protocol details

```python
import asyncio

from plugp100 import AuthCredential, DeviceConnectConfiguration, connect


async def main():
    credentials = AuthCredential("your-email", "your-password")
    config = DeviceConnectConfiguration(
        host="192.168.1.10",
        credentials=credentials,
        device_type="SMART.TAPOPLUG",
        encryption_type="klap",
        encryption_version=2,
    )

    device = await connect(config)
    await device.update()

    print(device.protocol_version)

    await device.client.close()


asyncio.run(main())
```

## Common lifecycle

```python
device = await connect(config)
await device.update()

# read properties or call device-specific APIs here

await device.client.close()
```

## What `update()` does

`update()` negotiates supported components the first time, fetches device info, and refreshes the active component state. Without it, many properties are not initialized yet.
