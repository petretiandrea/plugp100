from dataclasses import dataclass
from typing import Any

from plugp100.common.functional.tri import Try
from plugp100.responses.hub_childs.hub_child_base_info import HubChildBaseInfo


@dataclass
class SwitchChildDeviceState:
    base_info: HubChildBaseInfo
    device_on: bool
    led_off: int

    @staticmethod
    def try_from_json(kwargs: dict[str, Any]) -> Try["SwitchChildDeviceState"]:
        return HubChildBaseInfo.from_json(kwargs).flat_map(
            lambda base_info: Try.of(
                lambda: SwitchChildDeviceState(
                    base_info=base_info,
                    device_on=kwargs["device_on"],
                    led_off=kwargs.get("led_off", 0),
                )
            )
        )
