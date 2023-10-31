from typing import Union, Optional, Any

from plugp100.api.hub.hub_device import HubDevice
from plugp100.api.hub.s200b_device import S200ButtonDevice
from plugp100.api.hub.switch_child_device import SwitchChildDevice
from plugp100.api.hub.t100_device import T100MotionSensor
from plugp100.api.hub.t110_device import T110SmartDoor
from plugp100.api.hub.water_leak_device import WaterLeakSensor
from plugp100.api.hub.t31x_device import T31Device

HubChildDevice = Union[
    T100MotionSensor,
    T110SmartDoor,
    T31Device,
    S200ButtonDevice,
    SwitchChildDevice,
    WaterLeakSensor,
]


def create_hub_child_device(
    hub: HubDevice, child_state: dict[str, Any]
) -> Optional[HubChildDevice]:
    model = child_state.get("model").lower()
    device_id = child_state.get("device_id")
    if "t31" in model:
        return T31Device(hub, device_id)
    elif "t110" in model:
        return T110SmartDoor(hub, device_id)
    elif "s200" in model:
        return S200ButtonDevice(hub, device_id)
    elif "t100" in model:
        return T100MotionSensor(hub, device_id)
    elif "t300" in model:
        return WaterLeakSensor(hub, device_id)
    elif any(supported in model for supported in ["s200", "s210"]):
        return SwitchChildDevice(hub, device_id)
    else:
        return None
