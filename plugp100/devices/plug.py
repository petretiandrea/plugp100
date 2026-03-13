from typing import List, Optional

from plugp100.api.tapo_client import TapoClient
from plugp100.components.energy import EnergyComponent
from plugp100.components.on_off import OnOffComponent
from plugp100.components.socket_children import SocketChildrenComponent
from plugp100.devices.base import C, TapoDevice
from plugp100.devices.types import DeviceType
from plugp100.devices.children.strip_socket import TapoStripSocket
from plugp100.models.components import Components


class TapoPlug(TapoDevice):
    def __init__(self, host: str, port: Optional[int], client: TapoClient):
        super().__init__(host, port, client, DeviceType.Plug)

    async def turn_on(self):
        return await self.get_component(OnOffComponent).turn_on()

    async def turn_off(self):
        return await self.get_component(OnOffComponent).turn_off()

    @property
    def is_on(self) -> bool:
        return self.get_component(OnOffComponent).device_on

    @property
    def is_strip(self) -> bool:
        return self.get_component(SocketChildrenComponent) is not None

    @property
    def sockets(self) -> List[TapoStripSocket]:
        if component := self.get_component(SocketChildrenComponent):
            return component.sockets
        return []

    def _get_components_to_activate(self, components: Components) -> list[C]:
        active_components = [OnOffComponent(self.client)]
        if components.has("energy_monitoring"):
            active_components.append(EnergyComponent(self.client))
        if components.has("control_child"):
            active_components.append(SocketChildrenComponent(self, self.client))
        return active_components
