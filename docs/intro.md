---
title: Introduction
sidebar_position: 1
slug: /
---

# plugp100

`plugp100` is an async Python library to control TP-Link Tapo devices.

It exposes a small public surface for the most common workflows:

- discover devices on the local network
- connect to a device when you only know its IP
- connect to a device when you already know its protocol details
- work with typed device classes such as `TapoPlug`, `TapoBulb`, and `TapoHub`

## Main concepts

- `AuthCredential`: Tapo account credentials
- `DeviceConnectConfiguration`: connection parameters for a device
- `connect(...)`: create a typed device instance
- `TapoDiscovery.scan(...)`: discover devices on the LAN
- `connect_discovered_device(...)`: turn a discovered device into a real `TapoDevice`

## Public entrypoints

```python
from plugp100 import (
    AuthCredential,
    DeviceConnectConfiguration,
    TapoBulb,
    TapoDiscovery,
    TapoHub,
    TapoPlug,
    connect,
    connect_discovered_device,
)
```

## Supported device families

- smart plugs
- power strips
- smart bulbs
- led strips
- hubs
- several hub child devices such as buttons, door sensors, motion sensors, TRVs, and temperature/humidity sensors

## Important usage rules

- The library is async. Most operations require `await`.
- Call `await device.update()` before reading state-dependent properties.
- Close network resources when you are done: `await device.client.close()`.

Continue with [Getting Started](./getting-started.md).
