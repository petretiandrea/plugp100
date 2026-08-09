import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

from plugp100.common.functional.tri import Success
from plugp100.new.components.hub_children_component import HubChildrenComponent
from plugp100.new.device_type import DeviceType
from plugp100.new.tapohub import TapoHub
from tests.conftest import hub, hub_lot_devices


@hub
async def test_must_expose_device_info(device: TapoHub):
    assert device.device_type == DeviceType.Hub

    assert device.device_id is not None
    assert device.mac is not None
    assert device.model is not None
    assert device.overheated is not None
    assert device.nickname is not None
    assert device.device_info.rssi is not None
    assert device.device_info.friendly_name is not None
    assert device.device_info.signal_level is not None
    assert device.device_info.get_semantic_firmware_version() is not None
    assert len(device.children) == 0


@hub
async def test_turn_on_alarm(device: TapoHub):
    if device.has_alarm:
        await device.turn_alarm_on()
        await device.update()
        assert device.is_alarm_on is True


@hub
async def test_turn_on_alarm(device: TapoHub):
    if device.has_alarm:
        await device.turn_alarm_off()
        await device.update()
        assert device.is_alarm_on is False


@hub
async def test_get_alarm_tones(device: TapoHub):
    if device.has_alarm:
        tones = (await device.get_supported_alarm_tones()).get_or_raise()
        assert len(tones.tones) > 0


@hub_lot_devices
async def test_should_get_all_children(device: TapoHub):
    assert len(device.children) == 17


async def test_unsupported_children_are_skipped_without_reinitializing(caplog):
    child_list = SimpleNamespace(
        get_children_base_info=lambda: [SimpleNamespace(model="AC")]
    )
    client = SimpleNamespace(
        get_child_device_list=AsyncMock(return_value=Success(child_list))
    )
    component = HubChildrenComponent(SimpleNamespace(), client)

    with caplog.at_level(logging.WARNING, logger="HubChildrenComponent"):
        await component.update()
        await component.update()

    assert component.children == []
    client.get_child_device_list.assert_awaited_once_with(all_pages=True)
    assert caplog.messages.count("Found child device not supported, model AC") == 1
