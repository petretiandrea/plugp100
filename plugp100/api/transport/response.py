from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

from plugp100.api.transport.exceptions import TapoException
from plugp100.common.functional.tri import Failure, Success, Try
from plugp100.common.utils.json_utils import Json

T = TypeVar("T")


@dataclass
class TapoResponse(Generic[T]):
    error_code: int
    result: Optional[T]
    msg: Optional[str]

    @staticmethod
    def try_from_json(json: dict[str, Any]) -> Try["TapoResponse[Json]"]:
        response = TapoResponse(
            json.get("error_code", -1),
            json.get("result", {}),
            json.get("msg", "No message"),
        )
        if response.error_code == 0:
            return Success(response)
        return Failure(TapoException.from_error_code(response.error_code, response.msg))
