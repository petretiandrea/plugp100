from typing import Any, TYPE_CHECKING

from plugp100.api.tapo_client import TapoClient
from plugp100.components.base import DeviceComponent
from plugp100.devices.children.strip_socket import TapoStripSocket
from plugp100.models.child import PowerStripChild

if TYPE_CHECKING:
    from plugp100.devices.base import TapoDevice


class SocketChildrenComponent(DeviceComponent):
    def __init__(self, parent_device: "TapoDevice", client: TapoClient):
        self._client = client
        self._children_socket: list[TapoStripSocket] = []
        self._parent_device = parent_device

    @property
    def sockets(self) -> list[TapoStripSocket]:
        return self._children_socket

    async def update(self, current_state: dict[str, Any] | None = None):
        if len(self._children_socket) == 0:
            children = (await self._client.get_child_device_list()).get_or_raise()
            socket_children = children.get_children(
                lambda x: PowerStripChild.try_from_json(**x)
            )
            for socket in socket_children:
                socket_device = TapoStripSocket(
                    host=self._parent_device.host,
                    port=self._parent_device.port,
                    client=self._client,
                    parent_device=self._parent_device.device_info,
                    child_id=socket.device_id,
                )
                self._children_socket.append(socket_device)
                await socket_device.update()
