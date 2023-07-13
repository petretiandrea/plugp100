from dataclasses import dataclass
from typing import TypeVar, Generic, Optional, Any

from plugp100.common.utils.json_utils import Json
from plugp100.responses.tapo_exception import TapoException
from plugp100.common.functional.either import Either, Right, Left

T = TypeVar("T")


@dataclass
class TapoResponse(Generic[T]):
    error_code: int
    result: Optional[T]
    msg: Optional[str]

    @staticmethod
    def try_from_json(json: dict[str, Any]) -> Either['TapoResponse[Json]', Exception]:
        response = TapoResponse(
            json.get('error_code', -1),
            json.get('result', {}),
            json.get('msg', 'No message')
        )
        if response.error_code == 0:
            return Right(response)
        else:
            return Left(TapoException.from_error_code(response.error_code, response.msg))
