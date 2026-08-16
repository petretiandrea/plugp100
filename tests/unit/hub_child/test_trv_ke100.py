from plugp100.devices.children import KE100Device
from plugp100.models.hub_child import TRVState
from plugp100.models.temperature import TemperatureUnit
from tests.conftest import trv, trv_device


@trv
async def test_should_get_child(trv_device: KE100Device):
    child = trv_device
    assert child.parent_device_id == "802D86324AC15B78B560A284ED9A2E292137268A"

    assert child.mac == "11AA22BB33CC"
    assert child.device_id is not None
    assert child.device_info.rssi == -67
    assert child.model == "KE100"
    assert child.device_info.get_semantic_firmware_version() is not None
    assert child.nickname == "my-name"
    assert child.temperature == 20.5
    assert child.target_temperature == 27.5
    assert child.temperature_offset == 0
    assert child.range_control_temperature == (5, 30)
    assert child.battery_percentage == 100
    assert child.is_frost_protection_on is False
    assert child.state == TRVState.HEATING
    assert child.temperature_unit, TemperatureUnit.CELSIUS
    assert child.battery_low is False
    assert child.is_child_protection_on is False


@trv
async def test_should_set_target_temp(trv_device: KE100Device):
    child = trv_device
    await child.set_target_temp({"temperature": 24})
    await child.update()
    assert child.target_temperature == 24


@trv
async def test_should_set_temp_offset(trv_device: KE100Device):
    child = trv_device
    await child.set_temp_offset(-5)
    await child.update()
    assert child.temperature_offset == -5


@trv
async def test_should_set_frost_protection_on(trv_device: KE100Device):
    child = trv_device
    await child.set_frost_protection_on()
    await child.update()
    assert child.is_frost_protection_on is True


@trv
async def test_should_set_frost_protection_off(trv_device: KE100Device):
    child = trv_device
    await child.set_frost_protection_off()
    await child.update()
    assert child.is_frost_protection_on is False


@trv
async def test_should_set_child_protection_on(trv_device: KE100Device):
    child = trv_device
    await child.set_child_protection_on()
    await child.update()
    assert child.is_child_protection_on is True


@trv
async def test_should_set_child_protection_off(trv_device: KE100Device):
    child = trv_device
    await child.set_child_protection_off()
    await child.update()
    assert child.is_child_protection_on is False
