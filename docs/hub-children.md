---
title: Hub Children
sidebar_position: 5
---

# Hub Children

Hub child devices are exposed through `TapoHub.children`.

## Common child behavior

Most child devices inherit from a shared hub child base and expose:

- `parent_device_id`
- `report_interval_seconds`
- `battery_low` when the device supports battery reporting

## Supported child types

Current child device classes include:

- `TriggerButtonDevice`
- `TemperatureHumiditySensor`
- `MotionSensor`
- `SmartDoorSensor`
- `WaterLeakSensor`
- `SwitchChildDevice`
- `KE100Device`

Aliases:

- `S200ButtonDevice` -> `TriggerButtonDevice`
- `T31Device` -> `TemperatureHumiditySensor`

## Example

```python
from plugp100.devices.children import TemperatureHumiditySensor, TriggerButtonDevice

await hub.update()

for child in hub.children:
    if isinstance(child, TemperatureHumiditySensor):
        await child.update()
        print(child.current_temperature, child.current_humidity)

    if isinstance(child, TriggerButtonDevice):
        logs = await child.get_event_logs(page_size=5)
        print(logs.get_or_else(None))
```

## Temperature and humidity sensors

`TemperatureHumiditySensor` exposes:

- `current_temperature`
- `current_temperature_error`
- `current_humidity`
- `current_humidity_error`
- `temperature_unit`
- `await get_temperature_humidity_records()`

## Buttons

`TriggerButtonDevice` exposes:

- `await get_event_logs(page_size, start_id=0)`
- `subscribe_event_logs(...)`

## TRV devices

`KE100Device` exposes:

- `state`
- `temperature`
- `target_temperature`
- `temperature_offset`
- `battery_percentage`
- `await set_target_temp(...)`
- `await set_temp_offset(...)`
- `await set_frost_protection_on()`
- `await set_frost_protection_off()`
- `await set_child_protection_on()`
- `await set_child_protection_off()`
