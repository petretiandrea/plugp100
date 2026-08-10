from plugp100.devices.children.base import TapoHubChildDevice
from plugp100.devices.children.door import SmartDoorSensor
from plugp100.devices.children.motion import MotionSensor
from plugp100.devices.children.strip_socket import TapoStripSocket
from plugp100.devices.children.switch import SwitchChildDevice
from plugp100.devices.children.temperature import TemperatureHumiditySensor
from plugp100.devices.children.trigger_button import TriggerButtonDevice
from plugp100.devices.children.trv import KE100Device
from plugp100.devices.children.water_leak import WaterLeakSensor

S200ButtonDevice = TriggerButtonDevice
T31Device = TemperatureHumiditySensor

__all__ = [
    "KE100Device",
    "MotionSensor",
    "S200ButtonDevice",
    "SmartDoorSensor",
    "SwitchChildDevice",
    "T31Device",
    "TapoHubChildDevice",
    "TapoStripSocket",
    "TemperatureHumiditySensor",
    "TriggerButtonDevice",
    "WaterLeakSensor",
]
