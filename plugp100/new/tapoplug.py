from typing import Optional, List

from plugp100.api.tapo_client import TapoClient
from plugp100.new.child.tapostripsocket import TapoStripSocket
from plugp100.new.components.energy_component import EnergyComponent
from plugp100.new.components.on_off_component import OnOffComponent
from plugp100.new.components.socket_children_component import SocketChildrenComponent
from plugp100.new.device_type import DeviceType
from plugp100.new.tapodevice import TapoDevice, C
from plugp100.responses.components import Components


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
