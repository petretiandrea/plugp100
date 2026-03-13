from plugp100 import (
    AuthCredential,
    DeviceConnectConfiguration,
    DeviceType,
    DiscoveredDevice,
    EncryptionSchema,
    TapoBulb,
    TapoClient,
    TapoDevice,
    TapoDiscovery,
    TapoHub,
    TapoPlug,
    __version__,
    connect_discovered_device,
    connect,
)


def test_root_package_exports_explicit_api():
    assert AuthCredential.__name__ == "AuthCredential"
    assert TapoClient.__name__ == "TapoClient"
    assert DeviceConnectConfiguration.__name__ == "DeviceConnectConfiguration"
    assert connect.__name__ == "connect"
    assert DeviceType.Plug.value == "plug"
    assert TapoDevice.__name__ == "TapoDevice"
    assert TapoPlug.__name__ == "TapoPlug"
    assert TapoBulb.__name__ == "TapoBulb"
    assert TapoHub.__name__ == "TapoHub"
    assert TapoDiscovery.__name__ == "TapoDiscovery"
    assert DiscoveredDevice.__name__ == "DiscoveredDevice"
    assert EncryptionSchema.__name__ == "EncryptionSchema"
    assert connect_discovered_device.__name__ == "connect_discovered_device"
