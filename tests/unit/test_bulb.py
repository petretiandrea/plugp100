from plugp100.api.light_effect import LightEffect
from plugp100.new.device_type import DeviceType
from plugp100.new.tapobulb import TapoBulb, HS
from tests.conftest import bulb, bulb_led_strip


@bulb
async def test_must_expose_device_info(device: TapoBulb):
    assert device.device_type == DeviceType.Bulb

    assert device.device_id is not None
    assert device.mac is not None
    assert device.model is not None
    assert device.overheated is not None
    assert device.nickname is not None
    assert device.device_info.rssi is not None
    assert device.device_info.friendly_name is not None
    assert device.device_info.signal_level is not None
    assert device.device_info.get_semantic_firmware_version() is not None
    assert device.has_effect is not None
    assert device.is_color_temperature is not None
    assert device.is_color is not None
    assert device.is_on is not None

    assert device.components is not None
    assert len(device.components.component_list) > 0


@bulb
async def test_must_turn_on(device: TapoBulb):
    await device.turn_on()
    await device.update()
    assert device.is_on is True


@bulb
async def test_must_turn_off(device: TapoBulb):
    await device.turn_off()
    await device.update()
    assert device.is_on is False


@bulb
async def test_must_change_brightness(device: TapoBulb):
    await device.set_brightness(40)
    await device.update()
    assert device.brightness == 40


@bulb
async def test_must_change_hue_saturation(device: TapoBulb):
    if device.is_color:
        assert device.hs is not None
        await device.set_hue_saturation(50, 200)
        await device.update()
        assert device.hs == HS(50, 200)
    else:
        assert device.hs is None


@bulb
async def test_must_change_color_temperature(device: TapoBulb):
    assert device.color_temp_range is not None
    if device.is_color_temperature:
        await device.set_color_temperature(3400)
        await device.update()
        assert device.color_temp == 3400
    else:
        assert device.color_temp is None


@bulb_led_strip
async def test_must_set_lighting_effect(device: TapoBulb):
    assert device.color_temp_range is not None
    assert device.has_effect is True
    await device.set_light_effect(LightEffect.christmas_light())
    await device.update()
    assert device.effect.enable == 1
    assert device.effect == LightEffect.christmas_light()
    assert device.brightness == 100


@bulb_led_strip
async def test_must_set_lighting_effect_brightness(device: TapoBulb):
    await device.set_light_effect_brightness(LightEffect.christmas_light(), 50)
    await device.update()
    assert device.effect.enable == 1
    assert device.brightness == 50
    assert device.effect.brightness == 50
    assert device.effect.name == LightEffect.christmas_light().name
