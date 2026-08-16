---
title: Architecture
sidebar_position: 6
---

# Architecture

The library is organized around a clear boundary between domain code and infrastructure code.

## Domain packages

- `plugp100.devices`
- `plugp100.components`
- `plugp100.models`
- `plugp100.events`

These packages represent devices, reusable features, normalized models, and event logic.

## Communication boundary

All device communication now lives under `plugp100.api`:

- `plugp100.api.requests`
- `plugp100.api.protocol`
- `plugp100.api.transport`
- `plugp100.api.encryption`
- `plugp100.api.discovery`

This boundary contains request building, protocol negotiation, transport responses, crypto helpers, and low-level discovery I/O.

## Discovery split

Discovery is intentionally split into two levels:

- `plugp100.api.discovery`: low-level UDP, RSA, packet parsing, and cloud calls
- `plugp100.models.discovery`: normalized discovery models
- `plugp100.discovery`: high-level facade and orchestration helpers

For example:

- `TapoDiscovery.scan(...)` performs infrastructure discovery work
- `DiscoveredDevice` is a plain model
- `connect_discovered_device(...)` turns a discovery result into a real `TapoDevice`

## Components

Each device activates a set of components based on negotiated support from the device.

Examples:

- `OnOffComponent`
- `EnergyComponent`
- `LightComponent`
- `HubChildrenComponent`
- `AlarmComponent`

This keeps the device classes small while still exposing a convenient user-facing API.

## Typing and `Try`

Many lower-level operations return `Try[...]` instead of raising immediately.

Typical usage:

```python
result = await device.get_latest_firmware()
if result.is_success():
    print(result.value)
else:
    print(result.error())
```

This pattern is used mostly in the communication and component layers, while the public device workflow stays straightforward.
