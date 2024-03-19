from dataclasses import dataclass
from typing import Optional


@dataclass
class LightDeviceInfoParams(object):
    device_on: Optional[bool] = None
    brightness: Optional[int] = None
