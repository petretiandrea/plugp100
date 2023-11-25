import logging
from time import time
from typing import Optional, Any

import aiohttp

from plugp100.common.credentials import AuthCredential
from plugp100.common.functional.tri import Try
from plugp100.protocol.securepassthrough_transport import (
    Session,
    SecurePassthroughTransport,
)
from plugp100.common.utils.http_client import AsyncHttp
from plugp100.protocol.tapo_protocol import TapoProtocol
from plugp100.requests.tapo_request import TapoRequest
from plugp100.responses.tapo_exception import TapoException, TapoError
from plugp100.responses.tapo_response import TapoResponse

logger = logging.getLogger(__name__)


class PassthroughProtocol(TapoProtocol):
    def __init__(
        self,
        auth_credential: AuthCredential,
        url: str,
        http_session: Optional[aiohttp.ClientSession] = None,
    ):
        super().__init__()
        self._url = url
        self._http = AsyncHttp(
            aiohttp.ClientSession() if http_session is None else http_session
        )
        self._passthrough = SecurePassthroughTransport(self._http)
        self._session: Optional[Session] = None
        self._credential = auth_credential

    async def send_request(
        self, request: TapoRequest, retry: int = 3
    ) -> Try[TapoResponse[dict[str, Any]]]:
        response = await self._send_request(request)
        if retry > 0 and isinstance(response.error(), TapoException):
            if response.error().error_code == TapoError.ERR_SESSION_TIMEOUT.value:
                self._session.invalidate()
                logger.warning(
                    "Session timeout, invalidate it, retrying with new session"
                )
                return await self.send_request(request, retry - 1)
            elif response.error().error_code == TapoError.ERR_DEVICE.value:
                self._session.invalidate()
                logger.warning(
                    "Error device, probably exceeding rate limit, retrying with new session"
                )
                return await self.send_request(request, retry - 1)
        return response

    async def _send_request(
        self, request: TapoRequest
    ) -> Try[TapoResponse[dict[str, Any]]]:
        login_session = (
            await self._login_with_version(self._credential)
            if self._session is None or self._session.token is None
            else Try.of(self._session)
        )
        if login_session.is_success():
            self._session = login_session.get()
            request.with_terminal_uuid(
                self._session.terminal_uuid
            ).with_request_time_millis(round(time() * 1000))
            return await self._passthrough.send(request, self._session)
        return login_session

    async def close(self):
        await self._http.close()
        self._session = None

    async def _login_with_version(
        self, credential: AuthCredential, is_trying_v2: bool = False
    ) -> Try[Session]:
        session_or_error = await self._passthrough.handshake(self._url)
        if session_or_error.is_failure():
            return session_or_error
        else:
            session = session_or_error.get()
            if not session.is_handshake_session_expired():
                login_request = TapoRequest.login(credential, v2=is_trying_v2)
                token_or_error = (
                    await self._passthrough.send(login_request, session)
                ).map(lambda x: x.result["token"])
                if token_or_error.is_success():
                    session.token = token_or_error.get()
                    return Try.of(session)
                elif is_trying_v2 is False:
                    return await self._login_with_version(credential, is_trying_v2=True)
                else:  # already try with v2, so propagate error and stop retry
                    return token_or_error
            else:
                Try.of(
                    TapoException(
                        TapoError.ERR_SESSION_TIMEOUT,
                        "Detected handshake session timeout",
                    )
                )
