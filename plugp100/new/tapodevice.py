import abc
import logging
from abc import abstractmethod
from typing import Optional

from plugp100.api.tapo_client import TapoClient
from plugp100.new.device_type import DeviceType
from plugp100.responses.components import Components
from plugp100.responses.device_state import DeviceInfo

_LOGGER = logging.getLogger("TapoDevice")


class TapoDevice(abc.ABC):
    @property
    @abstractmethod
    def device_info(self) -> DeviceInfo:
        pass

    @property
    @abstractmethod
    def components(self) -> Components:
        pass

    @property
    @abstractmethod
    def nickname(self) -> str:
        pass

    @property
    @abstractmethod
    def mac(self) -> str:
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        pass

    @property
    @abstractmethod
    def device_id(self) -> str:
        pass

    @property
    @abstractmethod
    def device_type(self) -> DeviceType:
        pass

    @property
    @abstractmethod
    def overheated(self) -> bool:
        pass

    @abstractmethod
    async def update(self):
        pass

    @abstractmethod
    async def rssi(self) -> int:
        pass

    @abstractmethod
    async def signal_level(self) -> int:
        pass

    @abstractmethod
    async def firmware_version(self) -> str:
        pass


class AbstractTapoDevice(TapoDevice):
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
        self._last_update = {}
        self._device_type = device_type
        self._additional_data = {}

    async def update(self):
        if "components" not in self._last_update:
            components = (await self.client.get_component_negotiation()).get_or_raise()
        else:
            components = self._last_update["components"]
        response = (await self.client.get_device_info()).get_or_raise()
        self._last_update = {
            "device_info": DeviceInfo(**response),
            "components": components,
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
        return self.device_info.nickname or self.device_info.friendly_name

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

    @property
    def rssi(self) -> int:
        return self.device_info.rssi

    @property
    def firmware_version(self) -> str:
        return self.device_info.get_semantic_firmware_version().__str__()

    @property
    def signal_level(self) -> int:
        return self.device_info.signal_level

    def __repr__(self):
        if self._last_update == {}:
            return f"<{self.device_type} at {self.host} - update() needed>"
        return (
            f"<{self._device_type} model {self.model} at {self.host}"
            f" ({self.nickname})"
            f" - dev specific: {self._last_update['state']}>"
        )
