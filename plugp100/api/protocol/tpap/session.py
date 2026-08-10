"""TPAP handshake and encrypted-session state."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import logging
import secrets
import struct
from typing import TYPE_CHECKING, Any

import aiohttp
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.primitives.cmac import CMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from ecdsa import NIST256p, NIST384p, NIST521p, ellipticcurve
from ecdsa.curves import Curve
from ecdsa.ellipticcurve import CurveFp, PointJacobi
from passlib.hash import md5_crypt, sha256_crypt
from yarl import URL

from plugp100.api.transport.exceptions import (
    TapoAuthenticationError,
    TapoException,
    TapoProtocolError,
    TapoRetryableError,
)

from .crypto import TpapCryptoMixin

if TYPE_CHECKING:
    from .protocol import TpapProtocol

_LOGGER = logging.getLogger(__name__)


class TpapEncryptionSession(TpapCryptoMixin):
    """Class for a TPAP encryption session."""

    PAKE_CONTEXT_TAG = b"PAKE V1"

    def __init__(self, transport: "TpapProtocol") -> None:
        self._transport = transport
        self._handshake_lock = asyncio.Lock()
        self._device_mac: str = ""
        self._tpap_tls: int | None = None
        self._tpap_port: int | None = None
        self._tpap_dac: bool = False
        self._tpap_pake: list[int] = []
        self._tpap_user_hash_type: int | None = None
        self._session_id: str | None = None
        self._sequence: int | None = None
        self._ds_url: URL | None = None
        self._cipher_id: str = "aes_128_ccm"
        self._hkdf_hash: str = "SHA256"
        self._key: bytes | None = None
        self._base_nonce: bytes | None = None
        self._shared_key: bytes | None = None
        self._expected_dev_confirm: str | None = None
        self._dac_nonce_base64: str | None = None
        self._user_random: str | None = None
        self.reset()

    @property
    def _uses_camera_auth(self) -> bool:
        return False

    @property
    def _uses_robot_tpap_auth(self) -> bool:
        return False

    @property
    def tls_mode(self) -> int | None:
        """The discovered TLS mode."""
        return self._tpap_tls

    @property
    def ds_url(self) -> URL | None:
        """The secure DS endpoint for the current session."""
        return self._ds_url

    @property
    def device_mac(self) -> str:
        """The discovered device MAC."""
        return self._device_mac

    @property
    def is_established(self) -> bool:
        """Return true if the session is established."""
        return (
            self._session_id is not None
            and self._sequence is not None
            and self._ds_url is not None
            and self._key is not None
            and self._base_nonce is not None
        )

    def _invalidate_session(self) -> None:
        """Reset live session state while preserving discovered metadata."""
        self._session_id = None
        self._sequence = None
        self._ds_url = None
        self._cipher_id = "aes_128_ccm"
        self._hkdf_hash = "SHA256"
        self._key = None
        self._base_nonce = None
        self._shared_key = None
        self._expected_dev_confirm = None
        self._dac_nonce_base64 = None
        self._user_random = None

    def reset(self) -> None:
        """Reset discovered metadata and session state."""
        self._transport._ssl_context = None
        self._transport._app_url = self._transport._get_initial_app_url()
        self._device_mac = self._transport._known_device_mac
        self._tpap_tls = self._transport._known_tpap_tls
        self._tpap_port = self._transport._known_tpap_port
        self._tpap_dac = self._transport._known_tpap_dac
        self._tpap_pake = list(self._transport._known_tpap_pake)
        self._tpap_user_hash_type = self._transport._known_tpap_user_hash_type
        self._invalidate_session()

    @staticmethod
    def _parse_optional_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _require_result_dict(response: dict[str, Any]) -> dict[str, Any]:
        result = response.get("result")
        if not isinstance(result, dict):
            raise TapoProtocolError("TPAP response missing result object")
        return result

    async def perform_handshake(self) -> None:
        """Perform the handshake."""
        async with self._handshake_lock:
            if self.is_established:
                return

            self.reset()
            _LOGGER.debug(
                "TPAP: starting handshake with %s",
                self._transport._host,
            )

            await self._discover()
            await self._perform_auth_handshake()

            _LOGGER.debug("TPAP: handshake complete with %s", self._transport._host)

    async def _discover(self) -> None:
        body = {"method": "login", "params": {"sub_method": "discover"}}
        status, data = await self._transport._post(
            self._transport._app_url.with_path("/"),
            json=body,
            headers=self._transport.COMMON_HEADERS,
            ssl=await self._transport.get_ssl_context(),
        )
        if status != 200 or not isinstance(data, dict):
            error_type = TapoRetryableError if status >= 500 else TapoProtocolError
            raise error_type(
                f"TPAP discover failed for {self._transport._host}: "
                f"{status} {type(data)}"
            )

        self._handle_response_error_code(data, "discover")
        result = self._require_result_dict(data)
        tpap = result.get("tpap")
        if not isinstance(tpap, dict):
            raise TapoProtocolError("TPAP discover response missing tpap object")

        self._device_mac = str(result.get("mac") or "")
        self._tpap_tls = self._parse_optional_int(tpap.get("tls"))
        self._tpap_port = self._parse_optional_int(tpap.get("port"))
        self._tpap_dac = bool(tpap.get("dac"))
        self._tpap_pake = list(tpap.get("pake") or [])
        self._tpap_user_hash_type = self._parse_optional_int(tpap.get("user_hash_type"))

        self._transport._known_device_mac = self._device_mac
        self._transport._known_tpap_tls = self._tpap_tls
        self._transport._known_tpap_port = self._tpap_port
        self._transport._known_tpap_dac = self._tpap_dac
        self._transport._known_tpap_pake = list(self._tpap_pake)
        self._transport._known_tpap_user_hash_type = self._tpap_user_hash_type
        self._update_transport_url()

        # Discover runs before we know the real TLS mode, so rebuild for auth.
        self._transport._ssl_context = None

    async def _login(self, params: dict[str, Any], *, step_name: str) -> dict[str, Any]:
        body = {"method": "login", "params": params}
        ssl_context = await self._transport.get_ssl_context()
        status, data = await self._transport._post(
            self._transport._app_url.with_path("/"),
            json=body,
            headers=self._transport.COMMON_HEADERS,
            ssl=ssl_context,
        )
        if status != 200 or not isinstance(data, dict):
            error_type = TapoRetryableError if status >= 500 else TapoProtocolError
            raise error_type(
                f"TPAP {step_name} failed for {self._transport._host}: "
                f"{status} {type(data)}"
            )

        self._handle_response_error_code(data, step_name)
        return self._require_result_dict(data)

    def _update_transport_url(self) -> None:
        self._transport._app_url = self._transport._build_app_url(
            tls_mode=self._tpap_tls,
            port=self._tpap_port,
        )

    def _handle_response_error_code(self, response: dict[str, Any], action: str) -> None:
        """Handle response errors to request reauth etc."""
        error_code_raw = response.get("error_code")
        if error_code_raw == 0:
            return

        error = TapoException.from_error_code(
            error_code_raw,
            f"TPAP {action} failed for {self._transport._host}",
        )
        if error.tapo_error is None:
            _LOGGER.warning(
                "Device %s received unknown error code: %s",
                self._transport._host,
                error_code_raw,
            )

        if isinstance(error, TapoAuthenticationError):
            self._invalidate_session()
        raise error

    async def _perform_auth_handshake(self) -> None:
        passcode_type = self._get_passcode_type()
        if passcode_type is None:
            raise TapoAuthenticationError(
                f"TPAP: no supported passcode type for {self._transport._host}"
            )

        candidate_secrets = self._get_candidate_secrets()
        if not candidate_secrets:
            raise TapoAuthenticationError(
                f"TPAP: no credential candidates available for {self._transport._host}"
            )

        register_username = self._get_register_username()
        candidate_count = len(candidate_secrets)
        last_error: TapoProtocolError | None = None

        for attempt, candidate_secret in enumerate(candidate_secrets, start=1):
            self._shared_key = None
            self._expected_dev_confirm = None
            self._dac_nonce_base64 = None
            self._user_random = None
            self._user_random = self._base64(secrets.token_bytes(32))
            register_params = {
                "sub_method": "pake_register",
                "username": register_username,
                "user_random": self._user_random,
                "cipher_suites": [1],
                "encryption": ["aes_128_ccm"],
                "passcode_type": passcode_type,
                "stok": None,
            }

            try:
                register_result = await self._login(
                    register_params, step_name="pake_register"
                )
                credentials_string = self._resolve_credentials(
                    register_result,
                    candidate_secret,
                    passcode_type=passcode_type,
                )
                share_params = self._build_share_params_from_register(
                    register_result, credentials_string
                )
                if self._use_dac_certification():
                    self._dac_nonce_base64 = self._base64(secrets.token_bytes(32))
                    share_params["dac_nonce"] = self._dac_nonce_base64

                share_result = await self._login(share_params, step_name="pake_share")
                self._establish_session_from_share_result(share_result)
                return
            except (TapoRetryableError, aiohttp.ClientError):
                raise
            except TapoProtocolError as exc:
                last_error = exc
                if attempt < candidate_count:
                    _LOGGER.debug(
                        "TPAP: credential candidate %d/%d failed for %s: %s",
                        attempt,
                        candidate_count,
                        self._transport._host,
                        exc,
                    )

        if last_error is not None:
            if self._uses_camera_auth and 2 in self._tpap_pake:
                _LOGGER.debug(
                    "TPAP: all password-based camera candidates failed for %s",
                    self._transport._host,
                )
            raise last_error

        raise TapoProtocolError(  # pragma: no cover
            "TPAP: handshake did not produce a session"
        )

    @staticmethod
    def _md5_hex(value: str) -> str:
        return hashlib.md5(value.encode()).hexdigest()  # noqa: S324

    @staticmethod
    def _sha256_hex_upper(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest().upper()  # noqa: S324

    def _get_register_username(self) -> str:
        return (
            self._sha256_hex_upper("admin")
            if self._tpap_user_hash_type == 1
            else self._md5_hex("admin")
        )

    @staticmethod
    def _base64(value: bytes) -> str:
        return base64.b64encode(value).decode()

    @staticmethod
    def _unbase64(value: str) -> bytes:
        return base64.b64decode(value)

    @staticmethod
    def _sec1_to_xy(sec1: bytes, curve: ec.EllipticCurve) -> tuple[int, int]:
        public_key = ec.EllipticCurvePublicKey.from_encoded_point(curve, sec1)
        numbers = public_key.public_numbers()
        return numbers.x, numbers.y

    @staticmethod
    def _xy_to_uncompressed(x: int, y: int, curve: ec.EllipticCurve) -> bytes:
        numbers = ec.EllipticCurvePublicNumbers(x, y, curve)
        public_key = numbers.public_key()
        return public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )

    @staticmethod
    def _len8le(value: bytes) -> bytes:
        return len(value).to_bytes(8, "little") + value

    @staticmethod
    def _encode_w(value: int) -> bytes:
        minimal_length = 1 if value == 0 else (value.bit_length() + 7) // 8
        unsigned = value.to_bytes(minimal_length, "big", signed=False)
        if minimal_length % 2 == 0:
            return unsigned
        if unsigned[0] & 0x80:
            return b"\x00" + unsigned
        return unsigned

    @staticmethod
    def _hash(algorithm: str, data: bytes) -> bytes:
        if algorithm.upper() == "SHA512":
            return hashlib.sha512(data).digest()
        return hashlib.sha256(data).digest()

    @staticmethod
    def _hkdf_expand(label: str, prk: bytes, digest_len: int, algorithm: str) -> bytes:
        hkdf_algorithm = (
            hashes.SHA512() if algorithm.upper() == "SHA512" else hashes.SHA256()
        )
        zero_salt = b"\x00" * digest_len
        return HKDF(
            algorithm=hkdf_algorithm,
            length=digest_len,
            salt=zero_salt,
            info=label.encode(),
        ).derive(prk)

    @staticmethod
    def _hmac(algorithm: str, key: bytes, data: bytes) -> bytes:
        digest = hashlib.sha512 if algorithm.upper() == "SHA512" else hashlib.sha256
        return hmac.new(key, data, digest).digest()

    @staticmethod
    def _cmac_aes(key: bytes, data: bytes) -> bytes:
        cmac = CMAC(algorithms.AES(key))
        cmac.update(data)
        return cmac.finalize()

    @staticmethod
    def _pbkdf2_sha256(
        password: bytes, salt: bytes, iterations: int, length: int
    ) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password, salt, iterations, length)

    @classmethod
    def _derive_ab(
        cls, credentials: bytes, salt: bytes, iterations: int, hash_len: int = 32
    ) -> tuple[int, int]:
        i_d = hash_len + 8
        derived = cls._pbkdf2_sha256(credentials, salt, iterations, 2 * i_d)
        return (
            int.from_bytes(derived[:i_d], "big"),
            int.from_bytes(derived[i_d:], "big"),
        )

    @staticmethod
    def _sha1_hex(value: str) -> str:
        return hashlib.sha1(value.encode()).hexdigest()  # noqa: S324

    @classmethod
    def _authkey_mask(cls, passcode: str, tmpkey: str, dictionary: str) -> str:
        masked = []
        max_length = max(len(tmpkey), len(passcode))
        for index in range(max_length):
            lhs = ord(passcode[index]) if index < len(passcode) else 0xBB
            rhs = ord(tmpkey[index]) if index < len(tmpkey) else 0xBB
            masked.append(dictionary[(lhs ^ rhs) % len(dictionary)])
        return "".join(masked)

    @classmethod
    def _sha1_username_mac_shadow(
        cls, username: str, mac12hex: str, password: str
    ) -> str:
        if (
            not username
            or len(mac12hex) != 12
            or not all(char in "0123456789abcdefABCDEF" for char in mac12hex)
        ):
            return password

        mac = ":".join(mac12hex[index : index + 2] for index in range(0, 12, 2)).upper()
        return cls._sha1_hex(cls._md5_hex(username) + "_" + mac)

    @classmethod
    def _md5_crypt(cls, password: str, prefix: str) -> str | None:
        if not prefix or not prefix.startswith("$1$") or len(password) > 30000:
            return None

        spec = prefix[3:]
        if "$" in spec:
            spec = spec.split("$", 1)[0]
        return md5_crypt.using(salt=spec[:8]).hash(password)

    @classmethod
    def _sha256_crypt(
        cls, password: str, prefix: str, rounds_from_params: int | None = None
    ) -> str | None:
        if not prefix:
            return None

        default_rounds = 5000
        min_rounds = 1000
        max_rounds = 999_999_999

        spec = prefix[3:] if prefix.startswith("$5$") else prefix
        rounds: int | None = None

        if spec.startswith("rounds="):
            rounds_part, _, salt_part = spec.partition("$")
            try:
                rounds = int(rounds_part.split("=", 1)[1])
            except ValueError:
                rounds = default_rounds
            rounds = max(min_rounds, min(max_rounds, rounds))
            salt = salt_part
        else:
            salt = spec.split("$", 1)[0] if "$" in spec else spec

        if rounds_from_params is not None:
            try:
                parsed_rounds = int(rounds_from_params)
            except (TypeError, ValueError):
                parsed_rounds = default_rounds
            rounds = max(min_rounds, min(max_rounds, parsed_rounds))

        salt = salt[:16]
        if rounds is not None:
            return sha256_crypt.using(rounds=rounds, salt=salt).hash(password)
        return sha256_crypt.using(salt=salt).hash(password)

    @classmethod
    def _build_credentials(
        cls, extra_crypt: dict | None, username: str, passcode: str, mac_no_colon: str
    ) -> str:
        if not extra_crypt:
            return f"{username}/{passcode}" if username else passcode

        crypt_type = (extra_crypt.get("type") or "").lower()
        params = extra_crypt.get("params")
        if not isinstance(params, dict):
            params = {}

        if crypt_type == "password_shadow":
            try:
                passwd_id = int(params.get("passwd_id", 0))
            except (TypeError, ValueError):
                _LOGGER.debug("TPAP: invalid passwd_id, using passcode")
                return passcode
            prefix = str(params.get("passwd_prefix", "") or "")
            if passwd_id == 1:
                return cls._md5_crypt(passcode, prefix) or passcode
            if passwd_id == 2:
                return cls._sha1_hex(passcode)
            if passwd_id == 3:
                return cls._sha1_username_mac_shadow(username, mac_no_colon, passcode)
            if passwd_id == 5:
                return (
                    cls._sha256_crypt(
                        passcode,
                        prefix,
                        rounds_from_params=params.get("passwd_rounds"),
                    )
                    or passcode
                )
            return passcode

        if crypt_type == "password_authkey":
            tmpkey = str(params.get("authkey_tmpkey", "") or "")
            dictionary = str(params.get("authkey_dictionary", "") or "")
            if tmpkey and dictionary:
                return cls._authkey_mask(passcode, tmpkey, dictionary)
            return passcode

        if crypt_type == "password_sha_with_salt":
            try:
                sha_name = int(params.get("sha_name", -1))
            except (TypeError, ValueError):
                _LOGGER.debug("TPAP: invalid sha_name, using passcode")
                return passcode
            sha_salt_b64 = str(params.get("sha_salt", "") or "")
            username_hint = "admin" if sha_name == 0 else "user"
            try:
                decoded_salt = base64.b64decode(sha_salt_b64).decode()
            except Exception:
                _LOGGER.debug("TPAP: invalid base64 salt, using passcode")
                return passcode
            return hashlib.sha256(
                (username_hint + decoded_salt + passcode).encode()
            ).hexdigest()

        return f"{username}/{passcode}" if username else passcode

    def _suite_hash_name(self, suite_type: int) -> str:
        return "SHA512" if suite_type in (2, 4, 5, 7, 9) else "SHA256"

    def _suite_mac_is_cmac(self, suite_type: int) -> bool:
        return suite_type in (8, 9)

    def _use_dac_certification(self) -> bool:
        return self._tpap_tls == 0 and self._tpap_dac

    @staticmethod
    def _mac_pass_from_device_mac(mac_colon: str) -> str:
        mac_hex = mac_colon.replace(":", "").replace("-", "")
        try:
            mac_bytes = bytes.fromhex(mac_hex)
        except ValueError as exc:
            raise TapoProtocolError(
                "Invalid device MAC for TPAP default passcode derivation"
            ) from exc
        if len(mac_bytes) < 6:
            raise TapoProtocolError(
                "Device MAC is too short for TPAP default passcode derivation"
            )
        seed = b"GqY5o136oa4i6VprTlMW2DpVXxmfW8"
        ikm = seed + mac_bytes[3:6] + mac_bytes[0:3]
        return (
            HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"tp-kdf-salt-default-passcode",
                info=b"tp-kdf-info-default-passcode",
            )
            .derive(ikm)
            .hex()
            .upper()
        )

    def _get_passcode_type(self) -> str | None:
        passcode_type_order: tuple[tuple[tuple[int, ...], str], ...]
        default_passcode_type: str | None

        if self._uses_camera_auth:
            passcode_type_order = (
                ((2, 1), "userpw"),
                ((0,), "default_userpw"),
                ((3,), "shared_token"),
            )
            default_passcode_type = None
        elif self._uses_robot_tpap_auth:
            passcode_type_order = (
                ((0,), "default_userpw"),
                ((2,), "userpw"),
                ((3,), "shared_token"),
            )
            default_passcode_type = "default_userpw"
        else:
            passcode_type_order = (
                ((0,), "default_userpw"),
                ((2, 5), "userpw"),
                ((3,), "shared_token"),
            )
            default_passcode_type = "default_userpw"

        pake = set(self._tpap_pake)
        for pake_values, passcode_type in passcode_type_order:
            if pake.intersection(pake_values):
                return passcode_type
        return default_passcode_type

    def _get_candidate_secrets(self, passcode_type: str | None = None) -> list[str]:
        passcode_type = passcode_type or self._get_passcode_type()
        if passcode_type is None:
            return []
        if passcode_type == "default_userpw":
            return (
                [self._mac_pass_from_device_mac(self._device_mac)]
                if self._device_mac
                else []
            )
        creds = self._transport._credential
        password = (creds.password if creds else "") or ""
        if not self._uses_camera_auth:
            return [password]
        if passcode_type == "shared_token":
            return [self._md5_hex(password)]
        if 2 not in self._tpap_pake:
            return [password]
        return list(
            dict.fromkeys(
                [
                    self._md5_hex(password),
                    self._sha256_hex_upper(password),
                ]
            )
        )

    def _resolve_credentials(
        self,
        register_result: dict[str, Any],
        candidate_secret: str,
        *,
        passcode_type: str | None = None,
    ) -> str:
        if (passcode_type or self._get_passcode_type()) == "default_userpw":
            return candidate_secret
        extra_crypt_value = register_result.get("extra_crypt")
        extra_crypt = extra_crypt_value if isinstance(extra_crypt_value, dict) else {}
        if self._uses_camera_auth and not extra_crypt:
            return candidate_secret
        creds = self._transport._credential
        username = (
            "" if self._uses_camera_auth else (creds.username if creds else "") or ""
        )
        mac_no_colon = self._device_mac.replace(":", "").replace("-", "")
        return self._build_credentials(
            extra_crypt,
            username,
            candidate_secret,
            mac_no_colon,
        )

    @staticmethod
    def _suite_parameters(
        suite_type: int,
    ) -> tuple[bytes, bytes, Curve, ec.EllipticCurve]:
        if suite_type in (1, 2, 8, 9):
            return (
                bytes.fromhex(
                    "02886e2f97ace46e55ba9dd7242579f2993b64e16ef3dcab95afd497333d8fa12f"
                ),
                bytes.fromhex(
                    "03d8bbd6c639c62937b04d997f38c3770719c629d7014d49a24b4f98baa1292b49"
                ),
                NIST256p,
                ec.SECP256R1(),
            )
        if suite_type in (3, 4):
            return (
                bytes.fromhex(
                    "030ff0895ae5ebf6187080a82d82b42e2765e3b2f8749c7e05eba366434b363d3dc36f15314739074d2eb8613fceec2853"
                ),
                bytes.fromhex(
                    "02c72cf2e390853a1c1c4ad816a62fd15824f56078918f43f922ca21518f9c543bb252c5490214cf9aa3f0baab4b665c10"
                ),
                NIST384p,
                ec.SECP384R1(),
            )
        if suite_type == 5:
            return (
                bytes.fromhex(
                    "02003f06f38131b2ba2600791e82488e8d20ab889af753a41806c5db18d37d85608cfae06b82e4a72cd744c719193562a653ea1f119eef9356907edc9b56979962d7aa"
                ),
                bytes.fromhex(
                    "0200c7924b9ec017f3094562894336a53c50167ba8c5963876880542bc669e494b2532d76c5b53dfb349fdf69154b9e0048c58a42e8ed04cef052a3bc349d95575cd25"
                ),
                NIST521p,
                ec.SECP521R1(),
            )
        raise TapoProtocolError(f"Unsupported TPAP suite type: {suite_type}")

    def _build_share_params_from_register(
        self, register_result: dict[str, Any], credentials_string: str
    ) -> dict[str, Any]:
        if self._user_random is None:
            raise TapoProtocolError("TPAP user random not initialized")

        dev_random = str(register_result.get("dev_random") or "")
        dev_salt = str(register_result.get("dev_salt") or "")
        dev_share = str(register_result.get("dev_share") or "")
        for field, value in (
            ("dev_random", dev_random),
            ("dev_salt", dev_salt),
            ("dev_share", dev_share),
        ):
            if not value:
                raise TapoProtocolError(f"TPAP register response missing {field}")

        suite_type_value = register_result.get("cipher_suites")
        if suite_type_value is None:
            raise TapoProtocolError("TPAP register response has invalid cipher_suites")
        try:
            suite_type = int(suite_type_value)
        except (TypeError, ValueError) as exc:
            raise TapoProtocolError(
                "TPAP register response has invalid cipher_suites"
            ) from exc

        iterations_value = register_result.get("iterations")
        if iterations_value is None:
            raise TapoProtocolError("TPAP register response has invalid iterations")
        try:
            iterations = int(iterations_value)
        except (TypeError, ValueError) as exc:
            raise TapoProtocolError(
                "TPAP register response has invalid iterations"
            ) from exc

        if iterations <= 0:
            raise TapoProtocolError("TPAP register response has invalid iterations")

        encryption = str(register_result.get("encryption") or "")
        if not encryption:
            raise TapoProtocolError("TPAP register response missing encryption")
        chosen_cipher = self._normalize_cipher_id(encryption)
        if chosen_cipher not in self.CIPHER_PARAMETERS:
            raise TapoProtocolError(f"Unsupported TPAP session cipher: {encryption}")

        self._cipher_id = chosen_cipher
        self._hkdf_hash = self._suite_hash_name(suite_type)

        m_comp, n_comp, nist, crypto_curve = self._suite_parameters(suite_type)
        curve: CurveFp = nist.curve
        generator: PointJacobi = nist.generator
        order = generator.order()
        g_point = generator

        m_x, m_y = self._sec1_to_xy(m_comp, crypto_curve)
        n_x, n_y = self._sec1_to_xy(n_comp, crypto_curve)
        m_point = ellipticcurve.Point(curve, m_x, m_y, order)
        n_point = ellipticcurve.Point(curve, n_x, n_y, order)

        credential_bytes = credentials_string.encode()
        a_value, b_value = self._derive_ab(
            credential_bytes, self._unbase64(dev_salt), iterations, 32
        )
        w_value = a_value % order
        h_value = b_value % order
        x_value = secrets.randbelow(order - 1) + 1

        l_point = x_value * g_point + w_value * m_point
        l_encoded = self._xy_to_uncompressed(l_point.x(), l_point.y(), crypto_curve)

        device_share_bytes = self._unbase64(dev_share)
        r_x, r_y = self._sec1_to_xy(device_share_bytes, crypto_curve)
        r_point = ellipticcurve.Point(curve, r_x, r_y, order)
        r_encoded = self._xy_to_uncompressed(r_point.x(), r_point.y(), crypto_curve)

        r_prime = r_point + (-(w_value * n_point))
        z_point = x_value * r_prime
        v_point = (h_value % order) * r_prime

        z_encoded = self._xy_to_uncompressed(z_point.x(), z_point.y(), crypto_curve)
        v_encoded = self._xy_to_uncompressed(v_point.x(), v_point.y(), crypto_curve)
        m_encoded = self._xy_to_uncompressed(m_point.x(), m_point.y(), crypto_curve)
        n_encoded = self._xy_to_uncompressed(n_point.x(), n_point.y(), crypto_curve)

        context_hash = self._hash(
            self._hkdf_hash,
            self.PAKE_CONTEXT_TAG
            + self._unbase64(self._user_random)
            + self._unbase64(dev_random),
        )
        w_encoded = self._encode_w(w_value)

        transcript = (
            self._len8le(context_hash)
            + self._len8le(b"")
            + self._len8le(b"")
            + self._len8le(m_encoded)
            + self._len8le(n_encoded)
            + self._len8le(l_encoded)
            + self._len8le(r_encoded)
            + self._len8le(z_encoded)
            + self._len8le(v_encoded)
            + self._len8le(w_encoded)
        )

        transcript_hash = self._hash(self._hkdf_hash, transcript)
        digest_len = 64 if self._hkdf_hash.upper() == "SHA512" else 32
        mac_len = 16 if self._suite_mac_is_cmac(suite_type) else 32
        confirmation_keys = self._hkdf_expand(
            "ConfirmationKeys", transcript_hash, mac_len * 2, self._hkdf_hash
        )
        key_confirm_a = confirmation_keys[:mac_len]
        key_confirm_b = confirmation_keys[mac_len : mac_len * 2]
        self._shared_key = self._hkdf_expand(
            "SharedKey", transcript_hash, digest_len, self._hkdf_hash
        )

        if self._suite_mac_is_cmac(suite_type):
            user_confirm = self._cmac_aes(key_confirm_a, r_encoded)
            expected_dev_confirm = self._cmac_aes(key_confirm_b, l_encoded)
        else:
            user_confirm = self._hmac(self._hkdf_hash, key_confirm_a, r_encoded)
            expected_dev_confirm = self._hmac(self._hkdf_hash, key_confirm_b, l_encoded)

        self._expected_dev_confirm = self._base64(expected_dev_confirm)
        return {
            "sub_method": "pake_share",
            "user_share": self._base64(l_encoded),
            "user_confirm": self._base64(user_confirm),
        }

    def _verify_dac_proof(self, share_result: dict[str, Any]) -> None:
        """Verify DAC certificate chain and proof signature."""
        try:
            dac_ca = str(share_result.get("dac_ca") or "")
            dac_ica = str(share_result.get("dac_ica") or "")
            dac_proof = share_result.get("dac_proof")
            if not (dac_ca and dac_proof and self._shared_key and self._dac_nonce_base64):
                return
            if not isinstance(dac_proof, str):
                raise TapoProtocolError("Invalid DAC proof type")

            ca_cert = self._transport._load_certificate_value(dac_ca)
            ica_cert = (
                self._transport._load_certificate_value(dac_ica) if dac_ica else None
            )
            self._transport._verify_dac_certificate_chain(ca_cert, ica_cert)
            message = self._shared_key + self._unbase64(self._dac_nonce_base64)
            signature = self._unbase64(dac_proof)
            public_key = ca_cert.public_key()
            if not isinstance(public_key, ec.EllipticCurvePublicKey):
                raise TapoProtocolError(
                    "Unsupported DAC proof public key type: "
                    f"{type(public_key).__name__}"
                )
            public_key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        except InvalidSignature as exc:
            _LOGGER.error("TPAP: invalid DAC proof signature")
            raise TapoProtocolError("Invalid DAC proof signature") from exc
        except Exception as exc:
            _LOGGER.error("TPAP: DAC verification failed: %s", exc)
            raise TapoProtocolError(f"DAC verification failed: {exc}") from exc

    def _establish_session_from_share_result(self, share_result: dict[str, Any]) -> None:
        dev_confirm = str(share_result.get("dev_confirm") or "").lower()
        if not dev_confirm:
            raise TapoProtocolError("TPAP share response missing dev_confirm")
        if dev_confirm != (self._expected_dev_confirm or "").lower():
            raise TapoProtocolError("TPAP confirmation mismatch")

        if self._use_dac_certification():
            self._verify_dac_proof(share_result)

        session_id = str(share_result.get("sessionId") or share_result.get("stok") or "")
        if not session_id:
            _LOGGER.error("TPAP: missing session ID from device")
            raise TapoProtocolError("Missing session fields from device")
        if self._shared_key is None:
            raise TapoProtocolError("TPAP shared key was not derived")
        start_seq = share_result.get("start_seq")
        if start_seq is None:
            raise TapoProtocolError("Missing session fields from device")
        try:
            sequence = int(start_seq)
        except (TypeError, ValueError) as exc:
            raise TapoProtocolError("Invalid session fields from device") from exc

        self._key, self._base_nonce = self.key_nonce_from_shared(
            self._shared_key, self._cipher_id, hkdf_hash=self._hkdf_hash
        )
        self._session_id = session_id
        self._sequence = sequence
        self._ds_url = URL(f"{self._transport._app_url}/stok={self._session_id}/ds")

    def _require_established_session(self) -> tuple[str, int, URL, bytes, bytes]:
        if not self.is_established:
            raise TapoProtocolError("TPAP transport is not established")
        if TYPE_CHECKING:
            assert self._sequence is not None
            assert self._ds_url is not None
            assert self._key is not None
            assert self._base_nonce is not None

        return (
            self._cipher_id,
            self._sequence,
            self._ds_url,
            self._key,
            self._base_nonce,
        )

    def encrypt(self, payload: bytes | str) -> tuple[bytes, int]:
        """Encrypt the message."""
        cipher_id, seq, _, key, base_nonce = self._require_established_session()
        plaintext = payload.encode() if isinstance(payload, str) else payload
        encrypted = self._encrypt_payload(cipher_id, key, base_nonce, plaintext, seq)
        self._sequence = seq + 1
        return struct.pack(">I", seq) + encrypted, seq

    def advance(self, seq: int) -> None:
        """Advance the request sequence."""
        if self._sequence == seq:
            self._sequence = seq + 1

    def decrypt(self, payload: bytes, request_seq: int) -> bytes:
        """Decrypt the message."""
        cipher_id, _, _, key, base_nonce = self._require_established_session()
        if len(payload) < 4 + self.TAG_LEN:
            raise TapoProtocolError("TPAP response too short")

        response_seq = struct.unpack(">I", payload[:4])[0]
        if response_seq != request_seq:
            _LOGGER.debug(
                "Device returned unexpected rseq %d (expected %d)",
                response_seq,
                request_seq,
            )
        return self._decrypt_payload(
            cipher_id, key, base_nonce, payload[4:], response_seq
        )
