from dataclasses import dataclass
from typing import Optional


@dataclass
class LightColorDeviceInfoParams(object):
    device_on: Optional[bool] = None
    brightness: Optional[int] = None
    hue: Optional[int] = None
    saturation: Optional[int] = None
    color_temp: Optional[int] = None
