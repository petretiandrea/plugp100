import abc
from typing import Optional, Any

from plugp100.common.functional.tri import Try
from plugp100.requests.tapo_request import TapoRequest
from plugp100.responses.tapo_response import TapoResponse


class TapoProtocol(abc.ABC):
    def __init__(
        self,
        host: str,
        port: Optional[int] = 80,
    ):
        self._host = host
        self._port = port

    @abc.abstractmethod
    async def send_request(
        self, request: TapoRequest, retry: int = 3
    ) -> Try[TapoResponse[dict[str, Any]]]:
        pass

    @abc.abstractmethod
    async def close(self):
        pass
