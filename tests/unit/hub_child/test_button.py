from typing import cast

import pytest

from plugp100.new.child.tapohubchildren import TriggerButtonDevice
from plugp100.new.device_type import DeviceType
from plugp100.new.tapohub import TapoHub

button = pytest.mark.parametrize(
    "device",
    [("h100.json", "hub_children/s200.json")],
    indirect=True,
    ids=lambda x: (x[1]),
)


@button
async def test_should_get_expose_state(device: TapoHub):
    child = cast(TriggerButtonDevice, device.children[0])
    assert child.device_type == DeviceType.Sensor

    assert child.parent_device_id is not None
    assert child.mac is not None
    assert child.device_id is not None
    assert child.device_info.rssi < 0
    assert "s200" in child.model.lower()
    assert child.device_info.get_semantic_firmware_version() is not None
    assert child.nickname is not None
    assert child.battery_low is False
    assert child.report_interval_seconds == 16


@button
async def test_should_get_trigger_logs(device: TapoHub):
    child = cast(TriggerButtonDevice, device.children[0])
    events = (await child.get_event_logs(10)).get_or_raise()
    assert len(events.events) <= 10
    assert events.event_start_id == 25
    assert events.size == events.event_start_id
