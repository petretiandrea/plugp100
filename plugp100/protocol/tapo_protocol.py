import abc
from typing import Any

from plugp100.common.functional.tri import Try
from plugp100.requests.tapo_request import TapoRequest
from plugp100.responses.tapo_response import TapoResponse


class TapoProtocol(abc.ABC):
    @abc.abstractmethod
    async def send_request(
        self, request: TapoRequest, retry: int = 3
    ) -> Try[TapoResponse[dict[str, Any]]]:
        pass

    @abc.abstractmethod
    async def close(self):
        pass
