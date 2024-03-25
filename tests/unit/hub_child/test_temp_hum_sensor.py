from typing import cast

import pytest

from plugp100.new.child.tapohubchildren import TemperatureHumiditySensor
from plugp100.new.device_type import DeviceType
from plugp100.new.tapohub import TapoHub
from plugp100.responses.temperature_unit import TemperatureUnit

temp_hum_sensor = pytest.mark.parametrize(
    "device",
    [("h100.json", "hub_children/t310.json")],
    indirect=True,
    ids=lambda x: (x[1]),
)


@temp_hum_sensor
async def test_should_get_expose_state(device: TapoHub):
    child = cast(TemperatureHumiditySensor, device.children[0])
    assert child.device_type == DeviceType.Sensor

    assert child.parent_device_id is not None
    assert child.mac is not None
    assert child.device_id is not None
    assert child.device_info.rssi < 0
    assert "t31" in child.model.lower()
    assert child.device_info.get_semantic_firmware_version() is not None
    assert child.nickname is not None
    assert child.battery_low is False
    assert child.report_interval_seconds == 16
    assert child.current_temperature >= 0
    assert child.current_humidity >= 0
    assert child.temperature_unit is TemperatureUnit.CELSIUS
    assert child.current_temperature_error == 0
    assert child.current_humidity_error == 0


@temp_hum_sensor
async def test_should_get_humidity_temperature_records(device: TapoHub):
    child = cast(TemperatureHumiditySensor, device.children[0])
    records = (await child.get_temperature_humidity_records()).get_or_raise()
    assert records.local_time is not None
    assert len(records.past24_temperature) > 0
    assert len(records.past24_temperature) == len(records.past24h_humidity)
    assert len(records.past24_temperature_exceptions) == len(
        records.past24h_humidity_exceptions
    )
