import dataclasses
import logging
from typing import Optional, TypeVar, Type, Dict, Any

from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.tri import Try
from plugp100.new.components.countdown import Countdown
from plugp100.new.components.device_component import DeviceComponent
from plugp100.new.components.overheat_component import OverheatComponent
from plugp100.new.device_type import DeviceType
from plugp100.responses.components import Components
from plugp100.responses.device_state import DeviceInfo
from plugp100.responses.firmware import LatestFirmware, FirmwareDownloadProgress

_LOGGER = logging.getLogger("TapoDevice")

C = TypeVar("C", bound=DeviceComponent)


@dataclasses.dataclass
class LastUpdate:
    components: Components
    device_info: DeviceInfo
    raw_state: dict[str, Any]


class TapoDevice:
    def __init__(
            self,
            host: str,
            port: Optional[int],
            client: TapoClient,
            device_type: DeviceType = DeviceType.Unknown,
            child_id: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.client = client
        self._child_id = child_id
        self._last_update: LastUpdate | None = None
        self._device_type = device_type
        self._active_components: Dict[Type[DeviceComponent], DeviceComponent] = {}

    @property
    def get_device_components(self) -> [DeviceComponent]:
        return self._active_components.values()

    @property
    def protocol_version(self) -> str:
        return self.client.protocol.name

    @property
    def raw_state(self) -> dict[str, Any]:
        return self._last_update.raw_state

    async def update(self):
        if self._last_update is None:
            _LOGGER.debug("Initializing device...")
            components = await self._negotiate_components()
            await self._setup_components(components)
        else:
            components = self._last_update.components

        if self._child_id:
            state = (
                await self.client.control_child(
                    child_id=self._child_id, request=TapoRequest.get_device_info()
                )
            ).get_or_raise()
        else:
            state = (await self.client.get_device_info()).get_or_raise()
        self._last_update = LastUpdate(
            device_info=DeviceInfo(**state), components=components, raw_state=state
        )
        await self._update_from_state(state)
        _LOGGER.debug("Fetching component updates...")
        for _, component in self._active_components.items():
            await component.update(state)

    async def _update_from_state(self, state: dict[str, Any]):
        pass

    async def _setup_components(self, components: Components):
        for feature in self._get_components_to_activate(components):
            self.add_component(feature)
        self.add_component(OverheatComponent())
        if components.has("countdown"):
            self.add_component(Countdown(self.client))

    def _get_components_to_activate(self, components: Components) -> list[C]:
        return []

    def add_component(self, component: C):
        self._active_components[type(component)] = component

    def get_component(self, component_type: Type[C]) -> Optional[C]:
        return self._active_components.get(component_type, None)

    def has_component(self, component_type: Type[C]) -> bool:
        return self.get_component(component_type) is not None

    @property
    def device_info(self) -> DeviceInfo:
        return self._last_update.device_info

    @property
    def components(self) -> Components:
        return self._last_update.components

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
    def firmware_version(self) -> str:
        return self.device_info.get_semantic_firmware_version().__str__()

    @property
    def hardware_version(self) -> str:
        return self.device_info.hardware_version

    @property
    def wifi_info(self) -> "WifiInfo":
        return WifiInfo(self.device_info.signal_level, self.device_info.rssi)

    @property
    def has_countdown(self) -> bool:
        return self.has_component(Countdown)

    async def get_latest_firmware(self) -> Try[LatestFirmware]:
        request = TapoRequest(method="get_latest_fw", params=None)
        if self._child_id:
            response = await self.client.control_child(self._child_id, request)
        else:
            response = await self.client.execute_raw_request(request)
        return response.map(lambda x: LatestFirmware.from_json(x))

    async def get_firmware_download_state(self) -> Try[FirmwareDownloadProgress]:
        request = TapoRequest(method="get_fw_download_state", params=None)
        if self._child_id:
            response = await self.client.control_child(self._child_id, request)
        else:
            response = await self.client.execute_raw_request(request)
        return response.map(lambda x: FirmwareDownloadProgress.from_json(x))

    async def start_firmware_upgrade(self) -> bool:
        request = TapoRequest(method="fw_download", params=None)
        if self._child_id:
            response = await self.client.control_child(self._child_id, request)
        else:
            response = await self.client.execute_raw_request(request)
        return response.map(lambda _: True) \
            .get_or_else(False)

    async def _negotiate_components(self) -> Components:
        if self._child_id:
            child_components = await self.client.control_child(
                self._child_id, TapoRequest.component_negotiation()
            )
            return Components.try_from_json(child_components.get_or_raise())
        return (await self.client.get_component_negotiation()).get_or_raise()

    def __repr__(self):
        if self._last_update == {}:
            return f"<{self.device_type} at {self.host} - update() needed>"
        return (
            f"<{self._device_type} model {self.model} at {self.host}"
            f" ({self.nickname})"
            f" - dev specific: {self._last_update.device_info}>"
        )


@dataclasses.dataclass
class WifiInfo:
    signal_level: int
    rssi: int
