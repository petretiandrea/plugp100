from plugp100.new.device_type import DeviceType
from plugp100.new.tapoplug import TapoPlug
from tests.conftest import plug_strip


@plug_strip
async def test_must_expose_device_info(device: TapoPlug):
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
    assert len(device.sockets) > 0


@plug_strip
async def test_must_expose_socks_info(device: TapoPlug):
    for sock in device.sockets:
        assert sock.device_type == DeviceType.Plug
        assert sock.device_id != device.device_id
        assert sock.device_id is not None
        assert sock.mac is not None
        assert sock.model is not None
        assert sock.overheated is not None
        assert sock.nickname is not None
        assert sock.device_info.rssi is not None
        assert sock.device_info.friendly_name is not None
        assert sock.device_info.signal_level is not None
        assert sock.device_info.get_semantic_firmware_version() is not None


@plug_strip
async def test_must_turn_on(device: TapoPlug):
    for sock in device.sockets:
        await sock.turn_on()
        await sock.update()
        assert sock.is_on is True


@plug_strip
async def test_must_turn_off(device: TapoPlug):
    for sock in device.sockets:
        await sock.turn_off()
        await sock.update()
        assert sock.is_on is False
