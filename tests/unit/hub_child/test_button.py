import pytest

from plugp100.devices.children import TriggerButtonDevice
from plugp100.devices.types import DeviceType
from tests.conftest import button_device

button = pytest.mark.parametrize(
    "device",
    [("h100.json", "hub_children/s200.json")],
    indirect=True,
    ids=lambda x: (x[1]),
)


@button
async def test_should_get_expose_state(button_device: TriggerButtonDevice):
    child = button_device
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
async def test_should_get_trigger_logs(button_device: TriggerButtonDevice):
    child = button_device
    events = (await child.get_event_logs(10)).get_or_raise()
    assert len(events.events) <= 10
    assert events.event_start_id == 25
    assert events.size == events.event_start_id
