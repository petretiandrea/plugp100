import logging
from typing import Optional, List

from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.api.tapo_client import TapoClient
from plugp100.common.utils.json_utils import dataclass_encode_json
from plugp100.new.device_type import DeviceType
from plugp100.new.tapodevice import AbstractTapoDevice
from plugp100.api.requests.set_device_info.set_plug_info_params import SetPlugInfoParams
from plugp100.responses.child_device_list import PowerStripChild
from plugp100.responses.components import Components
from plugp100.responses.device_state import DeviceInfo

_LOGGER = logging.getLogger("TapoPlugStrip")


class TapoPlugStrip(AbstractTapoDevice):
    def __init__(self, host: str, port: Optional[int], client: TapoClient):
        super().__init__(host, port, client, DeviceType.PlugStrip)
        self._children_socket = []

    async def update(self):
        await super().update()

        if self.components.has("control_child"):
            children = (await self.client.get_child_device_list()).get_or_raise()
            if len(self._children_socket) == 0:
                _LOGGER.info("Initializing %s child sockets", children.sum)
                socket_children = children.get_children(
                    lambda x: PowerStripChild.try_from_json(**x)
                )
                for socket in socket_children:
                    socket_device = TapoStripSocket(self, socket.device_id)
                    self._children_socket.append(socket_device)
                    await socket_device.update()

    @property
    def sockets(self) -> List["TapoStripSocket"]:
        return self._children_socket


class TapoStripSocket(AbstractTapoDevice):
    def __init__(self, parent: TapoPlugStrip, child_id: str):
        super().__init__(parent.host, parent.port, parent.client, DeviceType.Plug)
        self.child_id = child_id
        self._parent_info = parent.device_info

    async def update(self):
        state = (
            await self.client.control_child(
                child_id=self.child_id, request=TapoRequest.get_device_info()
            )
        ).get_or_raise()
        components = (
            self._last_update["components"]
            if "components" in self._last_update
            else Components.try_from_json(
                (
                    await self.client.control_child(
                        child_id=self.child_id,
                        request=TapoRequest.component_negotiation(),
                    )
                ).get_or_raise()
            )
        )

        self._last_update = {
            "device_info": DeviceInfo(
                **{
                    **state,
                    "overheated": False
                    if state.get("overheat_status") == "normal"
                    else True,
                }
            ),
            "state": state,
            "components": components,
        }

    async def turn_on(self):
        request = TapoRequest.set_device_info(
            dataclass_encode_json(SetPlugInfoParams(device_on=True))
        )
        return await self.client.control_child(self.child_id, request)

    async def turn_off(self):
        request = TapoRequest.set_device_info(
            dataclass_encode_json(SetPlugInfoParams(device_on=False))
        )
        return await self.client.control_child(self.child_id, request)

    @property
    def is_on(self) -> bool:
        return self._last_update.get("state", {}).get("device_on", False)

    @property
    def parent_device_id(self) -> str:
        return self._last_update.get("state", {}).get("original_device_id")
