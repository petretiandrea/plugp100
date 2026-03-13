from plugp100.api import TapoClient
from plugp100.common.credentials import AuthCredential
from plugp100.devices import DeviceType, TapoBulb, TapoDevice, TapoHub, TapoPlug
from plugp100.devices.factory import DeviceConnectConfiguration, connect
from plugp100.discovery import (
    DiscoveredDevice,
    EncryptionSchema,
    TapoDiscovery,
    connect_discovered_device,
)

__version__ = "5.1.6"

__all__ = [
    "AuthCredential",
    "DeviceConnectConfiguration",
    "DeviceType",
    "DiscoveredDevice",
    "EncryptionSchema",
    "TapoBulb",
    "TapoClient",
    "TapoDevice",
    "TapoDiscovery",
    "TapoHub",
    "TapoPlug",
    "__version__",
    "connect_discovered_device",
    "connect",
]
