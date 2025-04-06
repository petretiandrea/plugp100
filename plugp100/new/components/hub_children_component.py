import logging
from typing import Any, Optional

from plugp100.api.tapo_client import TapoClient
from plugp100.new.child.tapohubchildren import (
    SmartDoorSensor,
    TriggerButtonDevice,
    SwitchChildDevice,
    MotionSensor,
    WaterLeakSensor,
    TemperatureHumiditySensor,
    KE100Device,
)
from plugp100.new.components.device_component import DeviceComponent
from plugp100.new.tapodevice import TapoDevice
from plugp100.responses.hub_childs.hub_child_base_info import HubChildBaseInfo

_LOGGER = logging.getLogger("HubChildrenComponent")


class HubChildrenComponent(DeviceComponent):
    def __init__(self, parent_device: TapoDevice, client: TapoClient):
        self._client = client
        self._children: [TapoDevice] = []
        self._parent_device = parent_device

    @property
    def children(self) -> [TapoDevice]:
        return self._children

    async def update(self, current_state: dict[str, Any] | None = None):
        if len(self._children) == 0:
            children = (
                await self._client.get_child_device_list(all_pages=True)
            ).get_or_raise()
            # _LOGGER.info("Initializing %s children", children.sum)
            for child in children.get_children_base_info():
                child_device = _hub_child_create(self._parent_device, self._client, child)
                if child_device is not None:
                    self._children.append(child_device)
                else:
                    _LOGGER.warning(f"Found child device not supported, model {child.model}", )
                    _LOGGER.warning(
                        "Please request support by opening an issue to https://github.com/petretiandrea/plugp100/issues/new")

            for child_device in self._children:
                await child_device.update()

    def find_child_device_by_model(self, model_filter: str) -> Optional["TapoDevice"]:
        return next(
            (
                child
                for child in self.children
                if child.device_id is not None
                   and model_filter.lower() in child.model.lower()
            ),
            None,
        )


# TODO: make based on device type
def _hub_child_create(
        parent_device: TapoDevice,
        client: TapoClient,
        child_info: HubChildBaseInfo,
) -> Optional[TapoDevice]:
    model = child_info.model.lower()
    if "t31" in model:
        return TemperatureHumiditySensor(
            host=parent_device.host,
            port=parent_device.port,
            client=client,
            child_id=child_info.device_id,
            parent_device_id=parent_device.device_info.device_id,
        )
    elif "t110" in model:
        return SmartDoorSensor(
            host=parent_device.host,
            port=parent_device.port,
            client=client,
            child_id=child_info.device_id,
            parent_device_id=parent_device.device_info.device_id,
        )
    elif "s200" in model:
        return TriggerButtonDevice(
            host=parent_device.host,
            port=parent_device.port,
            client=client,
            child_id=child_info.device_id,
            parent_device_id=parent_device.device_info.device_id,
        )
    elif "t100" in model:
        return MotionSensor(
            host=parent_device.host,
            port=parent_device.port,
            client=client,
            child_id=child_info.device_id,
            parent_device_id=parent_device.device_info.device_id,
        )
    elif "ke100" in model:
        return KE100Device(
            host=parent_device.host,
            port=parent_device.port,
            client=client,
            child_id=child_info.device_id,
            parent_device_id=parent_device.device_info.device_id,
        )
    elif "t300" in model:
        return WaterLeakSensor(
            host=parent_device.host,
            port=parent_device.port,
            client=client,
            child_id=child_info.device_id,
            parent_device_id=parent_device.device_info.device_id,
        )
    elif any(supported in model for supported in ["s220", "s210"]):
        return SwitchChildDevice(
            host=parent_device.host,
            port=parent_device.port,
            client=client,
            child_id=child_info.device_id,
            parent_device_id=parent_device.device_info.device_id,
        )
    return None
