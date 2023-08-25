import base64
import logging
import time
import uuid
from dataclasses import dataclass
from hashlib import md5
from typing import Optional, Any

import jsons

from plugp100.common.functional.tri import Try
from plugp100.common.utils.http_client import AsyncHttp
from plugp100.common.utils.json_utils import Json
from plugp100.encryption.key_pair import KeyPair
from plugp100.encryption.tp_link_cipher import TpLinkCipher, TpLinkCipherCryptography
from plugp100.requests.handshake_params import HandshakeParams
from plugp100.requests.internal.snowflake_id import SnowflakeId
from plugp100.requests.secure_passthrough_params import SecurePassthroughParams
from plugp100.requests.tapo_request import TapoRequest
from plugp100.responses.tapo_response import TapoResponse


@dataclass
class Session:
    url: str
    key_pair: KeyPair
    chiper: TpLinkCipher
    session_id: str
    expire_at: float
    token: Optional[str]
    terminal_uuid: str
    _handshake_invalid: bool = False

    def get_cookies(self) -> dict[str, Any]:
        return {"TP_SESSIONID": self.session_id}

    def is_handshake_session_expired(self) -> bool:
        return (
            self._handshake_invalid
            or (self.expire_at - (time.time() * 1000)) <= 40 * 1000
        )

    def invalidate(self):
        self._handshake_invalid = True
        self.token = None


logger = logging.getLogger(__name__)


class SecurePassthroughTransport:
    def __init__(self, http: AsyncHttp):
        self._http = http
        self._request_id_generator = SnowflakeId(1, 1)

    async def handshake(self, url: str) -> Try[Session]:
        logger.debug("Will perform handshaking...")
        logger.debug("Generating keypair")

        key_pair = KeyPair.create_key_pair()

        handshake_params = HandshakeParams(key_pair.get_public_key())
        logger.debug(f"Handshake params: {jsons.dumps(handshake_params)}")

        request = TapoRequest.handshake(handshake_params)

        request_body = jsons.loads(jsons.dumps(request))
        logger.debug(f"Request {request_body}")

        response = await self._http.async_make_post(url, json=request_body)
        resp_dict = await response.json(content_type=None)
        logger.debug(f"Device responded with: {resp_dict}")
        response_or_error = TapoResponse.try_from_json(resp_dict).map(lambda _: True)

        if response_or_error.is_success():
            handshake_cookies = {
                cookie.key: cookie.value for cookie in response.cookies.values()
            }
            logger.debug(f"Got Handshake cookies: ...{handshake_cookies}")
            session_id = [
                value for key, value in handshake_cookies.items() if "SESSIONID" in key
            ][0]
            timeout = int(
                [value for key, value in handshake_cookies.items() if "TIMEOUT" in key][0]
            )

            logger.debug("Decoding handshake key...")
            handshake_key = resp_dict["result"]["key"]
            tp_link_cipher = TpLinkCipherCryptography.create_from_keypair(
                handshake_key, key_pair
            )

            terminal_uuid = base64.b64encode(md5(uuid.uuid4().bytes).digest()).decode(
                "UTF-8"
            )
            return Try.of(
                Session(
                    url=url,
                    key_pair=key_pair,
                    chiper=tp_link_cipher,
                    session_id=session_id,
                    expire_at=(time.time() * 1000) + (timeout * 1000),
                    token=None,
                    terminal_uuid=terminal_uuid,
                )
            )
        else:
            return response_or_error

    async def send(
        self, request: TapoRequest, session: Session
    ) -> Try[TapoResponse[Json]]:
        request.with_request_id(
            self._request_id_generator.generate_id()
        ).with_request_time_millis(round(time.time() * 1000)).with_terminal_uuid(
            session.terminal_uuid
        )
        raw_request = jsons.dumps(request)
        logger.debug(f"Raw request: {raw_request}")

        encrypted_request = session.chiper.encrypt(raw_request)
        passthrough_request = TapoRequest.secure_passthrough(
            SecurePassthroughParams(encrypted_request)
        )
        request_body = jsons.loads(jsons.dumps(passthrough_request))
        logger.debug(f"Request body: {request_body}")

        response_encrypted = await self._http.async_make_post_cookie(
            session.url
            if session.token is None
            else f"{session.url}?token={session.token}",
            request_body,
            session.get_cookies(),
        )
        response_as_dict: dict = await response_encrypted.json(content_type=None)
        logger.debug(f"Device responded with: {response_as_dict}")

        response_json = (
            TapoResponse.try_from_json(response_as_dict)
            .map(
                lambda response: jsons.loads(
                    session.chiper.decrypt(response.result["response"])
                )
            )
            .flat_map(
                lambda decrypted_response: TapoResponse.try_from_json(decrypted_response)
            )
        )
        logger.debug(f"Decrypted response: {response_json}")

        return response_json
