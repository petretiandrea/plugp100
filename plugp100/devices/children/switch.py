from plugp100.components.on_off import OnOffComponent
from plugp100.devices.children.base import TapoHubChildDevice


class SwitchChildDevice(TapoHubChildDevice):
    def _get_components_to_activate(self, components):
        return super()._get_components_to_activate(components) + [
            OnOffComponent(self.client, self._child_id)
        ]

    async def on(self):
        return await self.get_component(OnOffComponent).turn_on()

    async def off(self):
        return await self.get_component(OnOffComponent).turn_off()

    @property
    def is_on(self) -> bool:
        return self.get_component(OnOffComponent).device_on


__all__ = ["SwitchChildDevice"]
