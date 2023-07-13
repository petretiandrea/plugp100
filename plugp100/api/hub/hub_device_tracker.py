from dataclasses import dataclass
from logging import Logger
from typing import Union, List, Set, Optional

from plugp100.common.state_tracker import StateTracker


@dataclass
class DeviceAdded:
    device_id: str


@dataclass
class DeviceRemoved:
    device_id: str


HubDeviceEvent = Union[DeviceAdded, DeviceRemoved]


class HubConnectedDeviceTracker(StateTracker[Set[str], HubDeviceEvent]):

    def __init__(self, logger: Logger = None):
        super().__init__(logger)

    def _compute_state_changes(self, new_state: Set[str], last_state: Optional[Set[str]]) -> List[HubDeviceEvent]:
        normalized_last_state = set() if last_state is None else last_state
        remove_device_ids = normalized_last_state.difference(new_state)
        new_device_ids = new_state.difference(normalized_last_state)
        return [
            *[DeviceAdded(device_id) for device_id in new_device_ids],
            *[DeviceRemoved(device_id) for device_id in remove_device_ids]
        ]
