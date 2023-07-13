from dataclasses import dataclass
from typing import Any, Set


@dataclass
class ChildDeviceList(object):
    child_device_list: list[dict[str, Any]]
    start_index: int
    sum: int

    @staticmethod
    def try_from_json(**kwargs):
        return ChildDeviceList(
            kwargs.get('child_device_list', []),
            kwargs.get('start_index', 0),
            kwargs.get('sum', 0)
        )

    def get_device_ids(self) -> Set[str]:
        return {child.get('device_id') for child in self.child_device_list if child.get('device_id', None) is not None}
