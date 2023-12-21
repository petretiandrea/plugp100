import base64
import dataclasses
import hashlib
import logging
import os
import ssl
from typing import Any, Optional, Tuple, Union

import aiohttp
import jsons
from aiohttp import ClientResponse
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from plugp100.common.credentials import AuthCredential
from plugp100.common.functional.tri import Try
from plugp100.protocol.tapo_protocol import TapoProtocol
from plugp100.requests.secure_passthrough_params import SecurePassthroughParams
from plugp100.requests.tapo_request import TapoRequest, MultipleRequestParams
from plugp100.responses.tapo_response import TapoResponse

ERROR_CODES = {
    "-40401": "Invalid stok value",
    "-40210": "Function not supported",
    "-64303": "Action cannot be done while camera is in patrol mode.",
    "-64324": "Privacy mode is ON, not able to execute",
    "-64302": "Preset ID not found",
    "-64321": "Preset ID was deleted so no longer exists",
    "-40106": "Parameter to get/do does not exist",
    "-40105": "Method does not exist",
    "-40101": "Parameter to set does not exist",
    "-40209": "Invalid login credentials",
    "-64304": "Maximum Pan/Tilt range reached",
    "-71103": "User ID is not authorized",
}

_LOGGER = logging.getLogger("CameraLikeProtocol")


@dataclasses.dataclass
class CameraLikeSession:
    is_connection_secure: bool
    chiper: "CameraLikeChiper"


class CameraLikeProtocol(TapoProtocol):
    def __init__(
        self,
        auth_credential: AuthCredential,
        host: str,
        port: int = 443,
        http_session: Optional[aiohttp.ClientSession] = None,
    ):
        self.host = host
        self.port = port
        self.control_url = f"https://{self.host}:{self.port}"
        self.username = auth_credential.username
        self.hashedPassword = (
            hashlib.md5(auth_credential.password.encode("utf8")).hexdigest().upper()
        )
        self.hashedSha256Password = (
            hashlib.sha256(auth_credential.password.encode("utf8")).hexdigest().upper()
        )
        # useful to get record but not handled by this library
        self.hashedCloudPassword = (
            hashlib.md5("password".encode("utf8")).hexdigest().upper()
        )
        self.ssl_context = (
            self._create_ssl_context()
        )  # camera like protocol works over https

        # session info
        self.stok = None
        self._http_session = http_session
        self._session: CameraLikeSession = None

    def _create_ssl_context(self) -> ssl.SSLContext:
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT")

        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    # CameraHubRequestGenerator qua ci sono le requests https://github.com/JurajNyiri/pytapo/blob/main/pytapo/__init__.py#L293
    async def send_request(
        self, request: TapoRequest, retry: int = 3
    ) -> Try[TapoResponse[dict[str, Any]]]:
        session = await self._create_session_or_get()
        request2 = TapoRequest.multiple_request(
            MultipleRequestParams(
                [
                    TapoRequest(
                        method="getDeviceInfo",
                        params={"device_info": {"name": ["basic_info"]}},
                    )
                ]
            )
        )
        raw_request = jsons.dumps(request2).encode("utf-8")
        encrypted_payload, seq = session.chiper.encrypt(raw_request)
        passthrough_envelope = self.wrap_to_passthrough(
            base64.b64encode(encrypted_payload).decode("utf-8")
        )
        passthrough_raw = jsons.dumps(passthrough_envelope)
        signature = self._generate_request_signature(
            session.chiper.hashed_password, session.chiper.c_nonce, seq, passthrough_raw
        )
        response, response_data = await self.session_post(
            url=f"{self.control_url}/stok={session.chiper.stok}/ds",
            headers={"Seq": str(seq), "Tapo_tag": signature},
            data=passthrough_raw,
        )
        if response.status == 200:
            print(response_data)
        pass

    async def close(self):
        pass

    def wrap_to_passthrough(self, encrypted_request: str) -> TapoRequest:
        return TapoRequest.secure_passthrough(SecurePassthroughParams(encrypted_request))

    async def _create_session_or_get(self) -> CameraLikeSession:
        if self._session is None:
            self._session = await self._create_session()
            assert self._session is not None, "Failed to create a new session"
        return self._session

    async def _create_session(self) -> CameraLikeSession:
        _LOGGER.info(f"Refreshing stock to {self.control_url}")
        cnonce = generate_nonce(8).decode().upper()
        require_secure_connection = await self.is_secure_connection_required()
        if require_secure_connection:
            request = TapoRequest(
                method="login",
                params={"cnonce": cnonce, "encrypt_type": 3, "username": self.username},
            )

        response, _ = await self.session_post(
            url=self.control_url, data=jsons.dumps(request)
        )
        _LOGGER.info(f"Response obtained {response.status}")
        if response.status == 200:
            response_json = await response.json(content_type=None)
            if require_secure_connection:
                chiper = await self._create_chiper_from_secure_connection(
                    cnonce, response_json
                )
                if chiper is not None:
                    return CameraLikeSession(True, chiper)
                else:
                    raise Exception(
                        "Invalid authentication data: failed to create chiper"
                    )

            else:
                stock = response_json["result"]["stok"]
        else:
            raise Exception("Invalid authentication data")

    async def _create_chiper_from_secure_connection(
        self, c_nonce: str, response_json: dict[str, any]
    ) -> Optional["CameraLikeChiper"]:
        if (
            "result" in response_json
            and "data" in response_json["result"]
            and "nonce" in response_json["result"]["data"]
            and "device_confirm" in response_json["result"]["data"]
        ):
            nonce = response_json["result"]["data"]["nonce"]
            device_confirm = response_json["result"]["data"]["device_confirm"]
            encryption = self._find_encryption_mode(c_nonce, nonce, device_confirm)
            hashed_password = (
                self.hashedPassword if encryption == "MD5" else self.hashedSha256Password
            )
            if encryption is not None:
                _LOGGER.info("computing digest password")
                digest_password = _digest_password_with_nonce(
                    hashed_password, c_nonce, nonce
                )
                request = TapoRequest(
                    method="login",
                    params={
                        "cnonce": c_nonce,
                        "encrypt_type": "3",
                        "digest_passwd": (
                            digest_password.encode("utf-8")
                            + c_nonce.encode("utf-8")
                            + nonce.encode("utf-8")
                        ).decode(),
                        "username": self.username,
                    },
                )
                response, _ = await self.session_post(
                    url=self.control_url, data=jsons.dumps(request)
                )
                if response.status == 200:
                    data = await response.json(content_type=None)
                    if "result" in data and "start_seq" in data["result"]:
                        if (
                            "user_group" in data["result"]
                            and data["result"]["user_group"] != "root"
                        ):
                            _LOGGER.debug(
                                "Incorrect user_group detected, raising Exception."
                            )
                            # encrypted control via 3rd party account does not seem to be supported
                            # see https://github.com/JurajNyiri/HomeAssistant-Tapo-Control/issues/456
                            raise Exception("Invalid authentication data")
                        _LOGGER.debug("Creating chiper")
                        seq = data["result"]["start_seq"]
                        return CameraLikeChiper.create(
                            seq, c_nonce, nonce, hashed_password, data["result"]["stok"]
                        )
        return None

    async def is_secure_connection_required(self) -> bool:
        if self._session is None:
            request = TapoRequest(
                method="login", params={"encrypt_type": "3", "username": self.username}
            )
            response, _ = await self.session_post(
                self.control_url, data=jsons.dumps(request)
            )
            if response.status == 200:
                json_data = await response.json(content_type=None)
                return (
                    "error_code" in json_data
                    and json_data["error_code"] == -40413
                    and "result" in json_data
                    and "data" in json_data["result"]
                    and "encrypt_type" in json_data["result"]["data"]
                    and "3" in json_data["result"]["data"]["encrypt_type"]
                )
            else:
                raise response.raise_for_status()
        return self._session.is_connection_secure

    async def session_post(
        self, url: str, cookies=None, headers=None, data=None, **kwargs
    ) -> Tuple[ClientResponse, bytes]:
        """Send an http post request to the device."""
        response_data = None
        self._http_session.cookie_jar.clear()
        resp = await self._http_session.post(
            url,
            headers=headers,
            data=data,
            cookies=cookies,
            ssl_context=self._create_ssl_context(),
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

    def _find_encryption_mode(self, cnonce, nonce, device_confirm: str) -> Optional[str]:
        hashed_nonces_with_sha256 = (
            hashlib.sha256(
                cnonce.encode("utf8")
                + self.hashedSha256Password.encode("utf8")
                + nonce.encode("utf8")
            )
            .hexdigest()
            .upper()
        )
        hashed_nonces_with_md5 = (
            hashlib.sha256(
                cnonce.encode("utf8")
                + self.hashedPassword.encode("utf8")
                + nonce.encode("utf8")
            )
            .hexdigest()
            .upper()
        )
        if device_confirm == (hashed_nonces_with_sha256 + nonce + cnonce):
            return "SHA256"
        elif device_confirm == (hashed_nonces_with_md5 + nonce + cnonce):
            return "MD5"
        return None

    def _generate_request_signature(
        self, hashed_password: str, cnonce: str, seq: int, raw_request: str
    ):
        tag = (
            hashlib.sha256(hashed_password.encode("utf8") + cnonce.encode("utf8"))
            .hexdigest()
            .upper()
        )
        return (
            hashlib.sha256(
                tag.encode("utf8") + raw_request.encode("utf8") + str(seq).encode("utf8")
            )
            .hexdigest()
            .upper()
        )


class CameraLikeChiper:
    @staticmethod
    def create(sequence, c_nonce, nonce, hashed_password, stok) -> "CameraLikeChiper":
        lsk = CameraLikeChiper._generate_token(c_nonce, nonce, hashed_password, "lsk")
        ivb = CameraLikeChiper._generate_token(c_nonce, nonce, hashed_password, "ivb")
        return CameraLikeChiper(lsk, ivb, sequence, hashed_password, c_nonce, stok)

    def __init__(self, lsk, ivb, seq, hashed_password, c_nonce, stok):
        self.seq = seq
        self.cipher = Cipher(algorithms.AES(lsk), modes.CBC(ivb))
        self.hashed_password = hashed_password
        self.c_nonce = c_nonce
        self.stok = stok

    def encrypt(self, msg: Union[str, bytes]):
        if type(msg) == str:
            msg = msg.encode("utf-8")
        assert type(msg) == bytes

        encryptor = self.cipher.encryptor()
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(msg) + padder.finalize()
        chiper_text = encryptor.update(padded_data) + encryptor.finalize()

        return chiper_text, self.seq

    def decrypt(self, msg: bytes) -> str:
        decryptor = self.cipher.decryptor()
        unpadder = padding.PKCS7(128).unpadder()
        decrypted_text = decryptor.update(msg) + decryptor.finalize()
        plain_text = unpadder.update(decrypted_text) + unpadder.finalize()

        return plain_text.decode()

    @staticmethod
    def _generate_token(c_nonce, nonce, hashed_password, token_type: str) -> int | bytes:
        hashed_key = (
            hashlib.sha256(
                c_nonce.encode("utf8")
                + hashed_password.encode("utf8")
                + nonce.encode("utf8")
            )
            .hexdigest()
            .upper()
        )
        return hashlib.sha256(
            (
                token_type.encode("utf8")
                + c_nonce.encode("utf8")
                + nonce.encode("utf8")
                + hashed_key.encode("utf8")
            )
        ).digest()[:16]


def _digest_password_with_nonce(hashed_password: str, c_nonce, nonce) -> str:
    payload = (
        hashed_password.encode("utf8") + c_nonce.encode("utf8") + nonce.encode("utf8")
    )
    return hashlib.sha256(payload).hexdigest().upper()


def generate_nonce(length: int) -> bytes:
    return os.urandom(length).hex().encode()
