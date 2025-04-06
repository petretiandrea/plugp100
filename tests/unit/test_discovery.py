from unittest.mock import patch, AsyncMock

from plugp100.common.credentials import AuthCredential
from plugp100.discovery import DiscoveredDevice
from plugp100.new.tapobulb import TapoBulb
from tests.conftest import load_fixture


def test_must_convert_discovered_device_to_dict():
    discovery_data = load_fixture("discovery.json")
    discovered_device = DiscoveredDevice.from_dict(discovery_data)
    assert discovered_device is not None
    dictionary = discovered_device.as_dict
    assert dictionary["mgt_encrypt_schm"] == discovery_data["mgt_encrypt_schm"]
    assert dictionary["mac"] == discovery_data["mac"]
    assert dictionary["ip"] == discovery_data["ip"]
    assert dictionary["device_id"] == discovery_data["device_id"]
    assert dictionary["device_type"] == discovery_data["device_type"]
    assert dictionary["device_model"] == discovery_data["device_model"]


async def test_discovered_device_should_get_real_tapo_device():
    discovered_device = DiscoveredDevice.from_dict(load_fixture("discovery.json"))
    device = await discovered_device.get_tapo_device(
        credentials=AuthCredential("test", "test")
    )
    assert device is not None
    assert device.protocol_version == "Klap V2"
    assert device.host == "1.2.3.4"
    assert isinstance(device, TapoBulb)


async def test_should_not_get_device_info_if_discovery_has_type():
    discovered_device = DiscoveredDevice.from_dict(load_fixture("discovery.json"))

    with patch(
        "plugp100.protocol.tapo_protocol.TapoProtocol.send_request",
        side_effect=AsyncMock(return_value=None),
    ) as send_request:
        device = await discovered_device.get_tapo_device(
            credentials=AuthCredential("test", "test")
        )
        send_request.assert_not_called()
        assert device is not None
