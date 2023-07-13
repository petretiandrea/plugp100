from dataclasses import dataclass
from typing import Any


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
