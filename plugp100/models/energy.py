import dataclasses
from typing import Any, Dict, Optional


@dataclasses.dataclass
class EnergyInfo:
    today_runtime: Optional[float] = property(lambda self: self.info.get("today_runtime"))
    month_runtime: Optional[float] = property(lambda self: self.info.get("month_runtime"))
    today_energy: Optional[float] = property(lambda self: self.info.get("today_energy"))
    month_energy: Optional[float] = property(lambda self: self.info.get("month_energy"))
    current_power: Optional[float] = property(lambda self: self.info.get("current_power"))

    def __init__(self, info: Dict[str, Any]):
        self.info = info

    def get_unmapped_state(self):
        return self.info
