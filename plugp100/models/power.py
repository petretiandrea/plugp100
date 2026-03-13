import dataclasses
from typing import Any, Dict, Optional


@dataclasses.dataclass
class PowerInfo:
    current_power: Optional[float] = property(lambda self: self.info.get("current_power"))

    def __init__(self, info: Dict[str, Any]):
        self.info = info

    def get_unmapped_state(self):
        return self.info
