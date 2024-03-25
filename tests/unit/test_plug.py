from plugp100.new.device_type import DeviceType
from plugp100.new.tapodevice import TapoDevice
from plugp100.new.tapoplug import TapoPlug
from tests.conftest import plug


@plug
async def test_must_expose_device_info(device: TapoDevice):
    assert device.device_type == DeviceType.Plug

    assert device.device_id is not None
    assert device.mac is not None
    assert device.model is not None
    assert device.overheated is not None
    assert device.nickname is not None
    assert device.device_info.rssi is not None
    assert device.device_info.friendly_name is not None
    assert device.device_info.signal_level is not None
    assert device.device_info.get_semantic_firmware_version() is not None


@plug
async def test_must_turn_on(device: TapoPlug):
    await device.turn_on()
    await device.update()
    assert device.is_on is True


@plug
async def test_must_turn_off(device: TapoPlug):
    await device.turn_off()
    await device.update()
    assert device.is_on is False
