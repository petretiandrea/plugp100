import logging
from typing import Optional, Type, Any

from plugp100.api.tapo_client import TapoClient
from plugp100.new.device_type import DeviceType
from plugp100.responses.components import Components
from plugp100.responses.device_state import DeviceInfo

_LOGGER = logging.getLogger("TapoDevice")


class TapoDevice:
    def __init__(
        self,
        host: str,
        port: Optional[int],
        client: TapoClient,
        device_type: DeviceType = DeviceType.Unknown,
    ):
        self.host = host
        self.port = port
        self.client = client
        self._last_update = None
        self._device_type = device_type
        self._additional_data = {}

    async def update(self):
        if self._last_update is None:
            _LOGGER.info("Getting first update")
            response = (await self.client.get_device_info()).get_or_raise()
            response_component = (
                await self.client.get_component_negotiation()
            ).get_or_raise()
            self._last_update = {
                "device_info": DeviceInfo(**response),
                "components": response_component,
                "state": response,
            }

        # update other modules

    @property
    def device_info(self) -> DeviceInfo:
        return self._last_update["device_info"]

    @property
    def components(self) -> Components:
        return self._last_update["components"]

    @property
    def nickname(self) -> str:
        return self.device_info.nickname

    @property
    def mac(self) -> str:
        return self.device_info.mac

    @property
    def model(self) -> str:
        return self.device_info.model

    @property
    def device_id(self) -> str:
        return self.device_info.device_id

    @property
    def device_type(self) -> DeviceType:
        """Return the device type."""
        return self._device_type

    @property
    def overheated(self) -> bool:
        return self.device_info.overheated

    def __repr__(self):
        if self._last_update is None:
            return f"<{self.device_type} at {self.host} - update() needed>"
        return (
            f"<{self._device_type} model {self.model} at {self.host}"
            f" ({self.nickname})"
            f" - dev specific: {self._last_update['state']}>"
        )
