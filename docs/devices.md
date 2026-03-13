---
title: Devices
sidebar_position: 4
---

# Devices

After `connect(...)`, the library returns a typed device instance.

## Base device API

All device types inherit from `TapoDevice`.

Common properties and methods:

- `await device.update()`
- `device.protocol_version`
- `device.nickname`
- `device.model`
- `device.device_id`
- `device.mac`
- `device.overheated`
- `device.firmware_version`
- `device.hardware_version`
- `device.raw_state`
- `device.get_device_components`

## Plugs

`TapoPlug` exposes:

- `await turn_on()`
- `await turn_off()`
- `is_on`
- `is_strip`
- `sockets`

Example:

```python
if isinstance(device, TapoPlug):
    await device.turn_on()
    await device.update()
    print(device.is_on)
```

## Bulbs and led strips

`TapoBulb` exposes:

- `await turn_on()`
- `await turn_off()`
- `await set_brightness(...)`
- `await set_hue_saturation(...)`
- `await set_color_temperature(...)`
- `await set_light_effect(...)`
- `brightness`
- `hs`
- `color_temp`
- `is_on`
- `is_led_strip`
- `has_effect`

Example:

```python
if isinstance(device, TapoBulb):
    await device.set_brightness(50)
    await device.update()
    print(device.brightness)
```

## Hubs

`TapoHub` exposes:

- `children`
- `find_child_device_by_model(...)`
- `has_alarm`
- `is_alarm_on`
- `await turn_alarm_on(...)`
- `await turn_alarm_off()`
- `await get_supported_alarm_tones()`

Example:

```python
if isinstance(device, TapoHub):
    await device.update()
    for child in device.children:
        print(type(child).__name__, child.device_id)
```

## Firmware helpers

Every `TapoDevice` also exposes:

- `await get_latest_firmware()`
- `await get_firmware_download_state()`
- `await start_firmware_upgrade()`

These methods return `Try[...]` values or booleans depending on the operation.
