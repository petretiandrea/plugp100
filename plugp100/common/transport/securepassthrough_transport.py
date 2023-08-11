import base64
import logging
import uuid
from dataclasses import dataclass
from hashlib import md5
from typing import Optional, cast

import jsons

from plugp100.common.functional.either import Either, Right, Left
from plugp100.common.utils.http_client import AsyncHttp
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
    cookie_token: Optional[str]
    token: Optional[str]
    terminal_uuid: str


logger = logging.getLogger(__name__)


class SecurePassthroughTransport:

    def __init__(self, http: AsyncHttp):
        self._http = http
        self._request_id_generator = SnowflakeId(1, 1)

    async def handshake(self, url: str) -> Either[Session, Exception]:
        logger.debug("Will perform handshaking...")
        logger.debug("Generating keypair")

        url = f"http://{url}/app"
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

        if isinstance(response_or_error, Right):
            cookie_token = response.cookies.get('TP_SESSIONID').value
            logger.debug(f"Got TP_SESSIONID token: ...{cookie_token[5:]}")

            logger.debug("Decoding handshake key...")
            handshake_key = resp_dict['result']['key']
            tp_link_cipher = TpLinkCipherCryptography.create_from_keypair(handshake_key, key_pair)

            terminal_uuid = base64.b64encode(md5(uuid.uuid4().bytes).digest()).decode("UTF-8")
            return Right(Session(url, key_pair, tp_link_cipher, cookie_token, token=None,
                                 terminal_uuid=terminal_uuid))
        else:
            return Left(cast(Left, response_or_error).error)

    async def send(self, request: TapoRequest, session: Session):
        assert session is not None
        request.with_request_id(self._request_id_generator.generate_id()) \
            .with_terminal_uuid(session.terminal_uuid)
        encrypted_request = session.chiper.encrypt(jsons.dumps(request))
        passthrough_request = TapoRequest.secure_passthrough(SecurePassthroughParams(encrypted_request))
        request_body = jsons.loads(jsons.dumps(passthrough_request))

        logger.debug(f"Request body: {request_body}")

        response_encrypted = await self._http.async_make_post_cookie(
            session.url if session.token is None else f"{session.url}?token={session.token}",
            request_body,
            {'TP_SESSIONID': session.cookie_token}
        )
        response_as_dict: dict = await response_encrypted.json(content_type=None)
        logger.debug(f"Device responded with: {response_as_dict}")

        return TapoResponse.try_from_json(response_as_dict) \
            .map(lambda response: jsons.loads(session.chiper.decrypt(response.result['response']))) \
            .bind(lambda decrypted_response: TapoResponse.try_from_json(decrypted_response))
