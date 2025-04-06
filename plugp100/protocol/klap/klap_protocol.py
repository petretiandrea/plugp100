import asyncio
import dataclasses
import hashlib
import logging
import secrets
import struct
import time
from typing import Any, Optional, Tuple, Union

import aiohttp
import jsons
from aiohttp import ClientResponse
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from yarl import URL

from plugp100.common.credentials import AuthCredential
from plugp100.common.functional.tri import Try, Failure
from plugp100.protocol.tapo_protocol import TapoProtocol
from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.responses.tapo_response import TapoResponse

from .klap_handshake_revision import KlapHandshakeRevision, KlapHandshakeRevisionV2

logger = logging.getLogger(__name__)


class KlapProtocol(TapoProtocol):
    TP_SESSION_COOKIE_NAME = "TP_SESSIONID"
    TP_TIMEOUT_COOKIE_NAME = "TIMEOUT"
    TP_TEST_USER = "test@tp-link.net"
    TP_TEST_PASSWORD = "test"

    def __init__(
        self,
        auth_credential: AuthCredential,
        url: str,
        klap_strategy: KlapHandshakeRevision,
        http_session: Optional[aiohttp.ClientSession] = None,
    ):
        super().__init__()
        self._base_url = url
        self._auth_credential = auth_credential
        self._klap_strategy = klap_strategy
        self.local_auth_hash = self._klap_strategy.generate_auth_hash(
            self._auth_credential
        )
        self._klap_session: Optional[KlapSession] = None
        self._last_request_url = None
        self._request_lock = asyncio.Lock()  # to protect cypher
        self._http_session = (
            aiohttp.ClientSession(
                cookie_jar=aiohttp.CookieJar(unsafe=True, quote_cookie=False)
            )
            if http_session is None
            else http_session
        )

    @property
    def name(self) -> str:
        if isinstance(self._klap_strategy, KlapHandshakeRevisionV2):
            return "Klap V2"
        else:
            return "Klap V1"

    async def send_request(
        self, request: TapoRequest, retry: int = 3
    ) -> Try[TapoResponse[dict[str, Any]]]:
        try:
            async with self._request_lock:
                if response := await self._send_request(request, retry):
                    return TapoResponse.try_from_json(response)
        except Exception as e:
            if retry > 0:
                return await self.send_request(request, retry - 1)
            return Failure(e)

    async def _send_request(self, request: TapoRequest, retry: int = 1) -> dict[str, Any]:
        if (
            self._klap_session is None
            or self._klap_session.is_handshake_session_expired()
        ):
            self._klap_session = None
            self._klap_session = await self.perform_handshake()

        raw_request = jsons.dumps(request)
        payload, seq = self._klap_session.chiper.encrypt(raw_request)
        url = f"{self._base_url}/request"
        cookies = (
            {KlapProtocol.TP_SESSION_COOKIE_NAME: self._klap_session.session_cookie}
            if self._klap_session.session_cookie
            else None
        )
        response, response_data = await self.session_post(
            url,
            params={"seq": seq},
            data=payload,
            cookies=cookies,
        )
        if response.status != 200:
            logger.error(
                f"Query failed after successful authentication. Remaining attempts count is {retry}"
            )
            if response.status == 403:
                raise Exception("Forbidden error after completing handshake")
            else:
                raise Exception(
                    "Device {} error code {} with seq {}",
                    self._base_url,
                    response.status,
                    seq,
                )
        else:
            return jsons.loads(self._klap_session.chiper.decrypt(response_data))

    async def close(self):
        self._klap_session = None
        await self._http_session.close()

    async def perform_handshake(self) -> "KlapSession":
        logger.debug("[KLAP] Starting handshake with %s", self._base_url)
        if seeds := await self.perform_handshake1():
            local_seed, remote_seed, auth_hash = seeds
            session_cookie = self._get_cookies_last_request(
                self._last_request_url, KlapProtocol.TP_SESSION_COOKIE_NAME
            )
            timeout = int(
                self._get_cookies_last_request(
                    self._last_request_url, KlapProtocol.TP_TIMEOUT_COOKIE_NAME
                )
                or 86400
            )

            if chiper := await self.perform_handshake2(
                local_seed, remote_seed, auth_hash, session_cookie
            ):
                logger.debug("[KLAP] Handshake with %s complete", self._base_url)
                return KlapSession(
                    chiper=chiper,
                    expire_at=time.time() + timeout,
                    session_cookie=session_cookie,
                )

    async def perform_handshake1(self) -> Tuple[bytes, bytes, bytes]:
        """Perform handshake1.  Resets authentication_failed to False at the start."""
        local_seed = secrets.token_bytes(16)
        url = f"{self._base_url}/handshake1"
        response, response_data = await self.session_post(url, data=local_seed)
        if response.status != 200:
            raise Exception(
                "Device fail to respond to handshake1 with %d" % response.status
            )

        remote_seed = response_data[0:16]
        server_hash = response_data[16:]
        logger.debug(
            "Handshake1, server remote_seed is: %s, server hash is: %s",
            remote_seed.hex(),
            server_hash.hex(),
        )

        local_seed_auth_hash = self._klap_strategy.handshake1_seed_auth_hash(
            local_seed=local_seed, remote_seed=remote_seed, auth_hash=self.local_auth_hash
        )

        if local_seed_auth_hash == server_hash:
            logger.debug("handshake1 hashes match")
            return local_seed, remote_seed, self.local_auth_hash
        else:
            logger.debug(
                "Expected %s got %s in handshake1.  Checking if blank auth is a match",
                local_seed_auth_hash.hex(),
                server_hash.hex(),
            )
            blank_auth = AuthCredential(username="", password="")
            blank_auth_hash = self._klap_strategy.generate_auth_hash(blank_auth)
            blank_seed_auth_hash = self._klap_strategy.handshake1_seed_auth_hash(
                local_seed=local_seed, remote_seed=remote_seed, auth_hash=blank_auth_hash
            )
            if blank_seed_auth_hash == server_hash:
                logger.debug(
                    f"Server response doesn't match our expected hash on url {self._base_url} but an authentication with blank credentials matched"
                )
                return local_seed, remote_seed, blank_auth_hash
            else:
                kasa_setup_auth = AuthCredential(
                    KlapProtocol.TP_TEST_USER, KlapProtocol.TP_TEST_PASSWORD
                )
                kasa_setup_auth_hash = self._klap_strategy.generate_auth_hash(
                    kasa_setup_auth
                )
                kasa_setup_seed_auth_hash = self._klap_strategy.handshake1_seed_auth_hash(
                    local_seed=local_seed,
                    remote_seed=remote_seed,
                    auth_hash=kasa_setup_auth_hash,
                )
                if kasa_setup_seed_auth_hash == server_hash:
                    self.local_auth_hash = kasa_setup_auth_hash
                    logger.debug(
                        f"Server response doesn't match our expected hash on url {self._base_url} but an authentication with kasa setup credentials matched"
                    )
                    return local_seed, remote_seed, kasa_setup_auth_hash
                else:
                    logger.debug(
                        f"Server response doesn't match our challenge on url {self._base_url}"
                    )
                    raise Exception(
                        f"Server response doesn't match our challenge on url {self._base_url}"
                    )

    async def perform_handshake2(
        self,
        local_seed: bytes,
        remote_seed: bytes,
        auth_hash: bytes,
        session_cookie: Optional[str],
    ) -> "KlapChiper":
        url = f"{self._base_url}/handshake2"
        payload = self._klap_strategy.handshake2_seed_auth_hash(
            local_seed=local_seed, remote_seed=remote_seed, auth_hash=auth_hash
        )
        cookies = (
            {KlapProtocol.TP_SESSION_COOKIE_NAME: session_cookie}
            if session_cookie
            else None
        )
        response, response_data = await self.session_post(
            url, data=payload, cookies=cookies
        )
        logger.debug(
            f"Handshake2 posted {time.time()}. Url is {self._base_url}, Response status is {response.status}"
        )
        if response.status != 200:
            raise Exception("Device responded with %d to handshake2" % response.status)
        else:
            return KlapChiper(
                local_seed=local_seed, remote_seed=remote_seed, user_hash=auth_hash
            )

    def _get_cookies_last_request(self, url: str, cookie_name: str) -> Optional[str]:
        if cookie := self._http_session.cookie_jar.filter_cookies(URL(url)).get(
            cookie_name
        ):
            return cookie.value
        return None

    async def session_post(
        self, url: str, cookies=None, params=None, data=None
    ) -> Tuple[ClientResponse, bytes]:
        """Send an http post request to the device."""
        response_data = None
        self._http_session.cookie_jar.clear()
        resp = await self._http_session.post(
            url, params=params, data=data, cookies=cookies
        )
        self._last_request_url = url
        async with resp:
            if resp.status == 200:
                response_data = await resp.read()
                await resp.release()
            else:
                try:
                    response_data = await resp.read()
                    await resp.release()
                except Exception:
                    pass

        return resp, response_data


@dataclasses.dataclass
class KlapSession:
    chiper: "KlapChiper"
    expire_at: float
    session_cookie: str

    def is_handshake_session_expired(self) -> bool:
        return (self.expire_at - (time.time() * 1000)) <= 40 * 1000


# The chiper is not thread safe and use sequence number to encrypt and decrypt data.
# So given the same instance of chiper you cannot encrypt and decrypt requests concurrently
class KlapChiper:
    PACK_LONG = struct.Struct(">l").pack

    def __init__(self, local_seed: bytes, remote_seed: bytes, user_hash: bytes):
        self.local_seed = local_seed
        self.remote_seed = remote_seed
        self.user_hash = user_hash
        self._key = self._key_derive(local_seed, remote_seed, user_hash)
        (self._iv, self._seq) = self._iv_derive(local_seed, remote_seed, user_hash)
        self._sig = self._sig_derive(local_seed, remote_seed, user_hash)
        self._aes_chiper = algorithms.AES(self._key)

    def encrypt(self, msg: Union[str, bytes]):
        """Encrypt the data and increment the sequence number."""
        self._seq = self._seq + 1
        if type(msg) == str:
            msg = msg.encode("utf-8")
        assert type(msg) == bytes

        cipher = Cipher(self._aes_chiper, modes.CBC(self._cbc()))
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(msg) + padder.finalize()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        digest = hashes.Hash(hashes.SHA256())
        digest.update(self._sig + self._seq.to_bytes(4, "big", signed=True) + ciphertext)
        signature = digest.finalize()

        return signature + ciphertext, self._seq

    def decrypt(self, msg: bytes):
        """Decrypt the data."""
        cipher = Cipher(self._aes_chiper, modes.CBC(self._cbc()))
        decryptor = cipher.decryptor()
        dp = decryptor.update(msg[32:]) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        plaintextbytes = unpadder.update(dp) + unpadder.finalize()

        return plaintextbytes.decode()

    def _key_derive(self, local_seed, remote_seed, user_hash):
        payload = b"lsk" + local_seed + remote_seed + user_hash
        return hashlib.sha256(payload).digest()[:16]

    def _iv_derive(self, local_seed, remote_seed, user_hash):
        # iv is first 16 bytes of sha256, where the last 4 bytes forms the
        # sequence number used in requests and is incremented on each request
        payload = b"iv" + local_seed + remote_seed + user_hash
        fulliv = hashlib.sha256(payload).digest()
        seq = int.from_bytes(fulliv[-4:], "big", signed=True)
        return fulliv[:12], seq

    def _sig_derive(self, local_seed, remote_seed, user_hash):
        # used to create a hash with which to prefix each request
        payload = b"ldk" + local_seed + remote_seed + user_hash
        return hashlib.sha256(payload).digest()[:28]

    def _cbc(self):
        return self._iv + KlapChiper.PACK_LONG(self._seq)
