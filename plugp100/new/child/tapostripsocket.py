from typing import Optional

from plugp100.api.tapo_client import TapoClient
from plugp100.new.components.on_off_component import OnOffComponent
from plugp100.new.device_type import DeviceType
from plugp100.new.tapodevice import TapoDevice, C
from plugp100.responses.components import Components
from plugp100.responses.device_state import DeviceInfo


class TapoStripSocket(TapoDevice):
    def __init__(
        self,
        host: str,
        port: Optional[int],
        client: TapoClient,
        child_id: str,
        parent_device: DeviceInfo,
    ):
        super().__init__(host, port, client, DeviceType.Plug, child_id)
        self._parent_info = parent_device

    async def turn_on(self):
        return await self.get_component(OnOffComponent).turn_on()

    async def turn_off(self):
        return await self.get_component(OnOffComponent).turn_off()

    @property
    def is_on(self) -> bool:
        return self.get_component(OnOffComponent).device_on

    @property
    def parent_device_id(self) -> str:
        return self._parent_info.device_id

    def _get_components_to_activate(self, components: Components) -> list[C]:
        return [OnOffComponent(self.client, self._child_id)]
