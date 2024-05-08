from typing import Any, Optional

from plugp100.api.light_effect import LightEffect
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.tri import Try
from plugp100.new.components.device_component import DeviceComponent
from plugp100.responses.device_state import LedStripDeviceState


class LightEffectComponent(DeviceComponent):
    def __init__(self, client: TapoClient):
        self._client = client
        self._state: LedStripDeviceState | None = None

    async def update(self, current_state: dict[str, Any] | None = None):
        self._state = LedStripDeviceState.try_from_json(current_state).get_or_raise()

    @property
    def state(self) -> LedStripDeviceState:
        return self._state

    @property
    def active_effect(self) -> Optional[LightEffect]:
        return self._state.lighting_effect

    @property
    def brightness(self) -> Optional[int]:
        if self.active_effect is not None and self.active_effect.enable:
            return self.active_effect.brightness
        return None

    async def set_light_effect(self, effect: LightEffect) -> Try[bool]:
        return await self._client.set_lighting_effect(effect)

    async def set_light_effect_brightness(
        self, effect: LightEffect, brightness: int
    ) -> Try[bool]:
        effect.brightness = brightness
        effect.bAdjusted = 1
        effect.enable = 1
        return await self._client.set_lighting_effect(effect)
