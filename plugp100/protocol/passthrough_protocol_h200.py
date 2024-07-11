import logging
from typing import Optional, Any

import aiohttp
import os
import jsons
import base64

from plugp100.api.requests.secure_passthrough_params import SecurePassthroughParams
from plugp100.api.requests.tapo_request import TapoRequest, TapoRequestH200
from plugp100.common.credentials import AuthCredential
from plugp100.common.functional.tri import Try
from plugp100.common.utils.http_client import AsyncHttp
from plugp100.protocol.tapo_protocol import TapoProtocol
from plugp100.responses.tapo_response import TapoResponse
from plugp100.encryption import helpers

logger = logging.getLogger(__name__)


class EncryptionMethod:
    MD5 = "md5"
    SHA256 = "sha256"


# Some of this class is adapted from the pytapo project
# Used under the terms of the MIT license
# https://github.com/JurajNyiri/pytapo/blob/main/LICENSE
class PassthroughProtocolH200(TapoProtocol):
    def __init__(
        self,
        auth_credential: AuthCredential,  # Only auth_credential.password is actually used
        host: str,
        http_session: Optional[aiohttp.ClientSession] = None,
    ):
        super().__init__()
        self._url = "https://" + host
        self._http = AsyncHttp(
            # Always generate a new session. Not 100% sure why this is needed. Perhaps so we can override the
            # default user-agent properly.
            aiohttp.ClientSession()
        )
        self._hashed_password = helpers.md5_digest(auth_credential.password)
        self._hashed_sha256_password = helpers.sha256_digest(auth_credential.password)
        self._is_secure_connection_cached = None
        self._headers = {
            "Host": host + ":443",
            "Referer": self._url + ":443",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "Tapo CameraClient Android",
            "Connection": "close",
            "requestByApp": "true",
            "Content-Type": "application/json; charset=UTF-8",
        }
        self._password_encryption_method = None
        self._seq = None
        self._lsk = None
        self._cnonce = None
        self._ivb = None
        self._stok = False

    @property
    def name(self) -> str:
        return "PassthroughH200"

    @property
    def request(self):
        return TapoRequestH200

    async def send_request(
            self, request: TapoRequest, retry: int = 3
    ) -> Try[TapoResponse[dict[str, Any]]]:
        # Ensure we are authenticated
        if not self._stok:
            await self._refresh_stok()

        auth_is_valid = True
        logger.debug(f"Performing request: {jsons.dumps(request)}")
        if self._seq is not None and await self._is_secure_connection():
            request = TapoRequestH200.secure_passthrough(
                SecurePassthroughParams(
                    base64.b64encode(
                        helpers.aes_encrypt_request(jsons.dumps(request).encode("utf-8"), self._lsk, self._ivb)
                    ).decode("utf8")
                )
            )
            self._headers["Seq"] = str(self._seq)
            try:
                self._headers["Tapo_tag"] = self._get_tag(request)
            except Exception as err:
                if str(err) == "Failure detecting hashing algorithm.":
                    auth_is_valid = False
                    logger.debug(
                        "Failure detecting hashing algorithm during _get_tag, reauthenticating."
                    )
                else:
                    raise err
            self._seq += 1

        request = jsons.loads(jsons.dumps(request))
        res = await self._http.async_make_post(
            f"{self._url}/stok={self._stok}/ds", json=request, headers=self._headers
        )
        response_data = await res.json()
        if (
            await self._is_secure_connection()
            and "result" in response_data
            and "response" in response_data["result"]
        ):
            encrypted_response = base64.b64decode(response_data["result"]["response"])
            try:
                response_json = jsons.loads(helpers.aes_decrypt_response(encrypted_response, self._lsk, self._ivb))
            except Exception as err:
                if (
                    str(err) == "Padding is incorrect."
                    or str(err) == "PKCS#7 padding is incorrect."
                ):
                    logger.debug(
                        f"{str(err)} Reauthenticating."
                    )
                    auth_is_valid = False
                else:
                    raise err
        else:
            response_json = await res.json()
        if not auth_is_valid or not await self._response_is_ok(res, response_json):
            #  -40401: Invalid Stok
            if (
                not auth_is_valid
                or (
                    response_json
                    and "error_code" in response_json
                    and (
                        response_json["error_code"] == -40401
                        or response_json["error_code"] == -1
                    )
                )
            ) and retry > 0:
                logger.warning(
                    f"Failed to authenticate properly. Server response was {response_json}. Retrying..."
                )
                await self._refresh_stok()
                return await self.send_request(request, retry - 1)
            else:
                raise Exception(
                    f"Error: {response_json['error_code']}, Response: {jsons.dumps(response_json)}"
                )

        if await self._response_is_ok(res):
            logger.debug(f"Received response: {response_json}")
            if "device_info" in response_json["result"]:
                # Specifically on getDeviceInfo calls, fiddle with the JSON returned to ensure backwards compatibility
                response_json["result"] = response_json["result"]["device_info"]["info"]
            return TapoResponse.try_from_json(response_json)

    async def close(self):
        await self._http.close()

    def _get_hashed_password(self):
        if self._password_encryption_method == EncryptionMethod.MD5:
            return self._hashed_password
        elif self._password_encryption_method == EncryptionMethod.SHA256:
            return self._hashed_sha256_password
        else:
            raise Exception("Failure detecting hashing algorithm.")

    def _generate_encryption_token(self, token_type, nonce):
        hashed_key = helpers.sha256_digest(self._cnonce + self._get_hashed_password() + nonce)
        return helpers.sha256(token_type.encode("utf8")
                + self._cnonce.encode("utf8")
                + nonce.encode("utf8")
                + hashed_key.encode("utf8")
        )[:16]
                    
    def _validate_device_confirm(self, nonce, device_confirm):
        self._password_encryption_method = None
        hashed_nonces_with_sha256 = helpers.sha256_digest(self._cnonce + self._hashed_sha256_password + nonce)
        hashed_nonces_with_md5 = helpers.sha256_digest(self._cnonce + self._hashed_password + nonce)
        if device_confirm == (hashed_nonces_with_sha256 + nonce + self._cnonce):
            self._password_encryption_method = EncryptionMethod.SHA256
        elif device_confirm == (hashed_nonces_with_md5 + nonce + self._cnonce):
            self._password_encryption_method = EncryptionMethod.MD5
        return self._password_encryption_method is not None

    async def _is_secure_connection(self):
        if self._is_secure_connection_cached is None:
            logger.debug("Secure connection not cached. Getting new secure connection and caching it.")
            data = jsons.loads(jsons.dumps(TapoRequestH200.login()))
            logger.warning(f"Data: {data}")
            res = await self._http.async_make_post(self._url, data, headers=self._headers)
            response = await res.json()
            self._is_secure_connection_cached = (
                "error_code" in response
                and response["error_code"] == -40413  # -40401 is typical on failure
                and "result" in response
                and "data" in response["result"]
                and "encrypt_type" in response["result"]["data"]
                and "3" in response["result"]["data"]["encrypt_type"]
            )
        return self._is_secure_connection_cached

    async def _response_is_ok(self, res, data=None):
        if (res.status != 200 and not await self._is_secure_connection()) or (
            res.status != 200
            and await self._is_secure_connection()
            and res.status != 500  # secure connections which are communicating expiring session (500) are OK
        ):
            raise Exception(
                "Error communicating with Tapo Hub. Status code: "
                + str(res.status)
            )

        try:
            if data is None:
                data = await res.json()
            if "error_code" not in data or data["error_code"] == 0:
                return True
            return False
        except Exception as e:
            raise Exception("Unexpected response from Tapo Hub: " + str(e))

    async def _refresh_stok(self, retry: int = 3):
        logger.debug("Refreshing stok")
        self._cnonce = os.urandom(8).hex().encode().decode().upper()
        if await self._is_secure_connection():
            data = TapoRequestH200.login(cnonce=self._cnonce)
        else:
            data = TapoRequestH200.login(password=self._hashed_password, hashed=True)
        data = jsons.loads(jsons.dumps(data))
        res = await self._http.async_make_post(self._url, data, headers=self._headers)

        if res.status == 401:
            try:
                data = await res.json()
                if data["result"]["data"]["code"] == -40411:
                    logger.debug("Code is -40411, raising Exception.")
                    raise Exception("Invalid authentication data")
            except Exception as e:
                if str(e) == "Invalid authentication data":
                    raise e
                else:
                    pass

        response_data = await res.json()

        if await self._is_secure_connection():
            if (
                "result" in response_data
                and "data" in response_data["result"]
                and "nonce" in response_data["result"]["data"]
                and "device_confirm" in response_data["result"]["data"]
            ):
                nonce = response_data["result"]["data"]["nonce"]
                if self._validate_device_confirm(nonce, response_data["result"]["data"]["device_confirm"]):
                    # sets self._password_encryption_method, password verified on client, now request stok
                    digest_passwd = helpers.sha256_digest(self._get_hashed_password() + self._cnonce + nonce)
                    digest_passwd = (
                        digest_passwd.encode("utf8") + self._cnonce.encode("utf8") + nonce.encode("utf8")
                    ).decode()
                    data = TapoRequestH200.login(self._cnonce, digest_passwd=digest_passwd)
                    data = jsons.loads(jsons.dumps(data))
                    res = await self._http.async_make_post(
                        self._url, data, headers=self._headers
                    )
                    response_data = await res.json()
                    if (
                        "result" in response_data
                        and "start_seq" in response_data["result"]
                    ):
                        if (
                            "user_group" in response_data["result"]
                            and response_data["result"]["user_group"] != "root"
                        ):
                            logger.debug(
                                "Incorrect user_group detected, raising Exception."
                            )
                            # encrypted control via 3rd party account does not seem to be supported
                            # see https://github.com/JurajNyiri/HomeAssistant-Tapo-Control/issues/456
                            raise Exception("Invalid authentication data")

                        self._seq = response_data["result"]["start_seq"]
                        logger.debug(
                            f"Generating encryption tokens (nonce={nonce}, seq={self._seq})."
                        )
                        self._lsk = self._generate_encryption_token("lsk", nonce)
                        self._ivb = self._generate_encryption_token("ivb", nonce)

                else:
                    if (
                        "error_code" in response_data
                        and response_data["error_code"] == -40413
                        and retry > 0
                    ):
                        logger.debug(
                            f"Incorrect device_confirm value, retrying..."
                        )
                        return await self._refresh_stok(retry - 1)
                    else:
                        logger.debug(
                            "Incorrect device_confirm value, raising Exception."
                        )
                        raise Exception("Invalid authentication data")
        else:
            self._password_encryption_method = EncryptionMethod.MD5
        if (
            "result" in response_data
            and "data" in response_data["result"]
            and "time" in response_data["result"]["data"]
            and "max_time" in response_data["result"]["data"]
            and "sec_left" in response_data["result"]["data"]
            and response_data["result"]["data"]["sec_left"] > 0
        ):
            raise Exception(
                f"Temporary Suspension: Try again in {str(response_data['result']['data']['sec_left'])} seconds"
            )
        if (
            "data" in response_data
            and "code" in response_data["data"]
            and "sec_left" in response_data["data"]
            and response_data["data"]["code"] == -40404
            and response_data["data"]["sec_left"] > 0
        ):
            raise Exception(
                f"Temporary Suspension: Try again in {str(response_data['data']['sec_left'])} seconds"
            )

        if await self._response_is_ok(res):
            result = await res.json()
            self._stok = result["result"]["stok"]
            logger.debug(f"Saving stok {self._stok}.")
            return self._stok
        if (
            ("error_code" in response_data and response_data["error_code"] == -40413)
            and retry > 0
        ):
            logger.debug(
                f"Unexpected response, retrying..."
            )
            return self._refresh_stok(retry - 1)
        else:
            logger.debug("Unexpected response, raising Exception.")
            raise Exception("Invalid authentication data")

    def _get_tag(self, request):
        tag = helpers.sha256_digest(self._get_hashed_password() + self._cnonce)
        tag = helpers.sha256_digest(tag + jsons.dumps(request) + str(self._seq))
        return tag
