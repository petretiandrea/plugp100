import dataclasses
from typing import Any

Json = dict[str, Any]

def dataclass_encode_json(obj):
    return {k: v for k, v in dataclasses.asdict(obj).items() if v is not None}
