from plugp100.devices import DeviceType, TapoBulb, TapoDevice, TapoHub, TapoPlug
from plugp100.devices.children import S200ButtonDevice, T31Device
from plugp100.devices.factory import DeviceConnectConfiguration


def test_new_devices_package_exports_canonical_types():
    assert DeviceType.Plug.value == "plug"
    assert TapoDevice.__name__ == "TapoDevice"
    assert TapoPlug.__name__ == "TapoPlug"
    assert TapoBulb.__name__ == "TapoBulb"
    assert TapoHub.__name__ == "TapoHub"
    assert DeviceConnectConfiguration.__name__ == "DeviceConnectConfiguration"
    assert S200ButtonDevice.__name__ == "TriggerButtonDevice"
    assert T31Device.__name__ == "TemperatureHumiditySensor"
