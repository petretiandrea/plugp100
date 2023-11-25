import dataclasses
import hashlib
import logging
import secrets
import time
from typing import Any, Optional, Tuple, Union

import aiohttp
import jsons
import urllib3
from aiohttp import ClientResponse
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from plugp100.common.credentials import AuthCredential
from plugp100.common.functional.tri import Try, Failure
from plugp100.protocol.tapo_protocol import TapoProtocol
from plugp100.requests.tapo_request import TapoRequest
from plugp100.responses.tapo_response import TapoResponse

logger = logging.getLogger(__name__)


class KlapProtocol(TapoProtocol):
    TP_SESSION_COOKIE_NAME = "TP_SESSIONID"
    TP_TEST_USER = "test@tp-link.net"
    TP_TEST_PASSWORD = "test"

    def __init__(
        self,
        auth_credential: AuthCredential,
        url: str,
        http_session: Optional[aiohttp.ClientSession] = None,
    ):
        super().__init__()
        self._base_url = url
        self._auth_credential = auth_credential
        self._local_seed: Optional[bytes] = None
        self.local_auth_hash = self.generate_auth_hash(self._auth_credential)
        self._http_session = (
            aiohttp.ClientSession() if http_session is None else http_session
        )
        self._klap_session: Optional[KlapSession] = None
        self._host = urllib3.get_host(self._base_url)

    async def send_request(
        self, request: TapoRequest, retry: int = 3
    ) -> Try[TapoResponse[dict[str, Any]]]:
        response = await self._send_request(request, retry)
        if response.is_failure() and retry > 0:
            return await self.send_request(request, retry - 1)
        else:
            return response

    async def _send_request(
        self, request: TapoRequest, retry: int = 1
    ) -> Try[TapoResponse[dict[str, Any]]]:
        if self._klap_session is None or not self._klap_session.handshake_complete:
            new_session = await self.perform_handshake()
            if new_session.is_success():
                self._klap_session = new_session.get()
            else:
                return Failure(new_session.error())

        raw_request = jsons.dumps(request)
        payload, seq = self._klap_session.chiper.encrypt(raw_request)
        url = f"{self._base_url}/request"
        response, response_data = await self.session_post(
            url,
            params={"seq": seq},
            data=payload,
            cookies=self._klap_session.get_cookies(),
        )
        if response.status != 200:
            logger.error(
                f"Query failed after succesful authentication at {time.time()}.  Host is {self._host}, Available attempts count is {retry}, Sequence is {seq}, Response status is {response.status}, Request was {request}"
            )
            if response.status == 403:
                self._klap_session.invalidate()
                return Failure(Exception("Forbidden error after completing handshake"))
            else:
                return Failure(
                    Exception(
                        "Device %s error code %d with seq %d"
                        % (self._host, response.status, seq)
                    )
                )
        else:
            decrypted_response = jsons.loads(
                self._klap_session.chiper.decrypt(response_data)
            )
            return TapoResponse.try_from_json(decrypted_response)

    async def close(self):
        self._klap_session.invalidate()
        await self._http_session.close()

    async def perform_handshake(
        self, new_local_seed: Optional[bytes] = None
    ) -> Try["KlapSession"]:
        logger.debug("[KLAP] Starting handshake with %s", self._host)
        seeds = await self.perform_handshake1(new_local_seed)
        if seeds.is_success():
            remote_seed, auth_hash = seeds.get()
            session = await self.perform_handshake2(
                self._local_seed, remote_seed, auth_hash
            )
            if session.is_success():
                logger.debug("[KLAP] Handshake with %s complete", self._host)
            return session
        return Failure(seeds.error())

    async def perform_handshake1(
        self, new_local_seed: Optional[bytes] = None
    ) -> Try[Tuple[bytes, bytes]]:
        """Perform handshake1.  Resets authentication_failed to False at the start."""
        self._local_seed = (
            secrets.token_bytes(16) if new_local_seed is None else new_local_seed
        )

        # Handshake 1 has a payload of local_seed
        # and a response of 16 bytes, followed by sha256(clientBytes | authenticator)
        self._klap_session = None

        url = f"{self._base_url}/handshake1"

        response, response_data = await self.session_post(url, data=self._local_seed)

        if response.status != 200:
            return Failure(
                Exception(
                    "Device fail to respond to handshake1 with %d" % response.status
                )
            )

        self._klap_session = KlapSession(
            chiper=None,
            handshake_complete=False,
            session_id=response.cookies.get(KlapProtocol.TP_SESSION_COOKIE_NAME).value,
            expire_at=(time.time() * 1000)
            + (int(response.cookies.get("TIMEOUT").value) * 1000),
        )
        remote_seed = response_data[0:16]
        server_hash = response_data[16:]
        logger.debug(
            f"Handshake1 posted at {time.time()}.  Host is {self._host}, Session cookie is {self._klap_session.session_id}, Response status is {response.status}, Request was {self.local_auth_hash.hex()}"
        )
        logger.debug(
            "Server remote_seed is: %s, server hash is: %s",
            remote_seed.hex(),
            server_hash.hex(),
        )

        local_seed_auth_hash = KlapProtocol._sha256(
            self._local_seed + remote_seed + self.local_auth_hash
        )

        if local_seed_auth_hash == server_hash:
            logger.debug("handshake1 hashes match")
            return Try.of((remote_seed, self.local_auth_hash))
        else:
            logger.debug(
                "Expected %s got %s in handshake1.  Checking if blank auth is a match",
                local_seed_auth_hash.hex(),
                server_hash.hex(),
            )
            blank_auth = AuthCredential(username="", password="")
            blank_auth_hash = self.generate_auth_hash(blank_auth)
            blank_seed_auth_hash = KlapProtocol._sha256(
                self._local_seed + remote_seed + blank_auth_hash
            )
            if blank_seed_auth_hash == server_hash:
                logger.debug(
                    "Server response doesn't match our expected hash on ip %s but an authentication with blank credentials matched"
                    % self._host
                )
                return Try.of((remote_seed, blank_auth_hash))
            else:
                kasa_setup_auth = AuthCredential(
                    KlapProtocol.TP_TEST_USER, KlapProtocol.TP_TEST_PASSWORD
                )
                kasa_setup_auth_hash = self.generate_auth_hash(kasa_setup_auth)
                kasa_setup_seed_auth_hash = KlapProtocol._sha256(
                    self._local_seed + remote_seed + kasa_setup_auth_hash
                )
                if kasa_setup_seed_auth_hash == server_hash:
                    self.local_auth_hash = kasa_setup_auth_hash
                    logger.debug(
                        "Server response doesn't match our expected hash on ip %s but an authentication with kasa setup credentials matched",
                        self._host,
                    )
                    return Try.of((remote_seed, kasa_setup_auth_hash))
                else:
                    self._klap_session = None
                    logger.debug(
                        "Server response doesn't match our challenge on ip %s"
                        % self._host
                    )
                    return Failure(
                        Exception(
                            "Server response doesn't match our challenge on ip %s"
                            % self._host
                        )
                    )

    async def perform_handshake2(
        self, local_seed: bytes, remote_seed: bytes, auth_hash: bytes
    ) -> Try["KlapSession"]:
        url = f"{self._base_url}/handshake2"
        payload = self._sha256(remote_seed + local_seed + auth_hash)
        response, response_data = await self.session_post(
            url, data=payload, cookies=self._klap_session.get_cookies()
        )
        logger.debug(
            f"Handshake2 posted {time.time()}. Host is {self._host}, Response status is {response.status}, Request was {payload!r}"
        )
        if response.status != 200:
            self._klap_session.invalidate()
            return Failure(
                Exception("Device responded with %d to handshake2" % response.status)
            )
        else:
            chiper = KlapChiper(
                local_seed=local_seed, remote_seed=remote_seed, user_hash=auth_hash
            )
            return Try.of(self._klap_session.complete_handshake(chiper))

    @staticmethod
    def generate_auth_hash(auth: AuthCredential):
        return KlapProtocol._sha256(
            KlapProtocol._sha1(auth.username.encode())
            + KlapProtocol._sha1(auth.password.encode())
        )

    @staticmethod
    def _sha1(payload: bytes) -> bytes:
        digest = hashes.Hash(hashes.SHA1())
        digest.update(payload)
        return digest.finalize()

    @staticmethod
    def _sha256(payload: bytes) -> bytes:
        return hashlib.sha256(payload).digest()

    async def session_post(
        self, url: str, cookies=None, params=None, data=None
    ) -> Tuple[ClientResponse, bytes]:
        """Send an http post request to the device."""
        response_data = None
        self._http_session.cookie_jar.clear()
        resp = await self._http_session.post(
            url, params=params, data=data, cookies=cookies
        )
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
    chiper: Optional["KlapChiper"]
    session_id: Optional[str]
    expire_at: float
    handshake_complete: bool

    def get_cookies(self) -> dict[str, Any]:
        return {"TP_SESSIONID": self.session_id}

    def is_handshake_session_expired(self) -> bool:
        return (self.expire_at - (time.time() * 1000)) <= 40 * 1000

    def invalidate(self):
        self.session_id = None
        self.handshake_complete = False

    def complete_handshake(self, chiper: "KlapChiper") -> "KlapSession":
        return KlapSession(
            handshake_complete=True,
            session_id=self.session_id,
            expire_at=self.expire_at,
            chiper=chiper,
        )


class KlapChiper:
    def __init__(self, local_seed: bytes, remote_seed: bytes, user_hash: bytes):
        self._key = self._key_derive(local_seed, remote_seed, user_hash)
        (self._iv, self._seq) = self._iv_derive(local_seed, remote_seed, user_hash)
        self._sig = self._sig_derive(local_seed, remote_seed, user_hash)

    def encrypt(self, msg: Union[str, bytes]):
        """Encrypt the data and increment the sequence number."""
        self._seq = self._seq + 1
        if type(msg) == str:
            msg = msg.encode("utf-8")
        assert type(msg) == bytes

        cipher = Cipher(algorithms.AES(self._key), modes.CBC(self._iv_seq()))
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

        cipher = Cipher(algorithms.AES(self._key), modes.CBC(self._iv_seq()))
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

    def _iv_seq(self):
        seq = self._seq.to_bytes(4, "big", signed=True)
        iv = self._iv + seq
        assert len(iv) == 16
        return iv
