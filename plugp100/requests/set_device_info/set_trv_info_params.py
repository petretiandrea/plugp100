from dataclasses import dataclass
from typing import Optional


@dataclass
class TRVDeviceInfoParams(object):
    target_temp: Optional[float] = None
    temp_offset: Optional[int] = None
    frost_protection_on: Optional[bool] = None
    child_protection: Optional[bool] = None
