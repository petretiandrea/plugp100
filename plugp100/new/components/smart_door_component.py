from typing import Any

from plugp100.new.components.device_component import DeviceComponent


# TODO: get component_negotiation for Tapo Smart Door sensor
# this class is actually too specific for SmartDoor, the component can be called open_closed


class SmartDoorComponent(DeviceComponent):
    def __init__(self):
        self.is_open = False

    async def update(self, current_state: dict[str, Any] | None = None):
        self.is_open = current_state["is_open"]
