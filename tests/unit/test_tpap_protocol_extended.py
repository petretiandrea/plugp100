import base64
import hashlib
import json
import ssl
import struct
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import NameOID
from yarl import URL

from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.common.credentials import AuthCredential
from plugp100.protocol.tpap_protocol import TpapEncryptionSession, TpapProtocol
from plugp100.responses.tapo_exception import (
    TapoAuthenticationError,
    TapoDeviceError,
    TapoError,
    TapoProtocolError,
    TapoRetryableError,
)


def _public_point() -> bytes:
    return (
        ec.derive_private_key(7, ec.SECP256R1())
        .public_key()
        .public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.UncompressedPoint,
        )
    )


def _register_result(**overrides):
    result = {
        "dev_random": base64.b64encode(b"r" * 16).decode(),
        "dev_salt": base64.b64encode(b"s" * 16).decode(),
        "dev_share": base64.b64encode(_public_point()).decode(),
        "cipher_suites": 2,
        "iterations": 100,
        "encryption": "aes_128_ccm",
    }
    result.update(overrides)
    return result


def _certificate(private_key, subject, issuer, issuer_key, *, is_ca=False):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject)]))
        .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, issuer)]))
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=is_ca, path_length=None), critical=True)
        .sign(issuer_key, hashes.SHA256())
    )


def test_hash_encoding_and_credential_helpers():
    session = TpapEncryptionSession
    assert session._encode_w(0) == b"\x00"
    assert session._encode_w(0x80) == b"\x00\x80"
    assert session._hash("SHA512", b"data") == hashlib.sha512(b"data").digest()
    assert len(session._cmac_aes(b"\0" * 16, b"data")) == 16
    assert len(session._hkdf_expand("label", b"key", 24, "SHA512")) == 24
    assert len(session._hmac("SHA512", b"key", b"data")) == 64
    assert session._pbkdf2_sha256(b"pw", b"salt", 2, 8)
    assert session._derive_ab(b"pw", b"salt", 2)[0] > 0
    assert len(session._authkey_mask("abc", "xy", "0123456789")) == 3
    assert session._sha1_username_mac_shadow("", "AABBCCDDEEFF", "pw") == "pw"
    shadow = session._sha1_username_mac_shadow("user", "AABBCCDDEEFF", "pw")
    assert shadow == session._sha1_hex(session._md5_hex("user") + "_AA:BB:CC:DD:EE:FF")
    assert session._md5_crypt("pw", "") is None
    assert session._md5_crypt("pw", "$1$salt$")
    assert session._md5_crypt("x" * 30001, "$1$salt$") is None
    assert session._sha256_crypt("pw", "") is None
    assert session._sha256_crypt("pw", "$5$rounds=bad$salt")
    assert session._sha256_crypt("pw", "$5$salt$", rounds_from_params=2000)
    assert session._sha256_crypt("pw", "$5$salt$", rounds_from_params="bad")


@pytest.mark.parametrize(
    ("extra", "expected"),
    [
        (None, "user/pw"),
        ({}, "user/pw"),
        ({"type": "password_shadow", "params": {"passwd_id": 2}}, "sha1"),
        ({"type": "password_shadow", "params": {"passwd_id": 3}}, "mac-shadow"),
        (
            {
                "type": "password_authkey",
                "params": {
                    "authkey_tmpkey": "xy",
                    "authkey_dictionary": "0123456789",
                },
            },
            "authkey",
        ),
        (
            {
                "type": "password_sha_with_salt",
                "params": {
                    "sha_name": 0,
                    "sha_salt": base64.b64encode(b"salt").decode(),
                },
            },
            "salted",
        ),
        ({"type": "unknown", "params": {}}, "user/pw"),
    ],
)
def test_build_credentials_variants(extra, expected):
    result = TpapEncryptionSession._build_credentials(extra, "user", "pw", "AABBCCDDEEFF")
    if expected == "sha1":
        assert result == TpapEncryptionSession._sha1_hex("pw")
    elif expected == "mac-shadow":
        assert result == TpapEncryptionSession._sha1_username_mac_shadow(
            "user", "AABBCCDDEEFF", "pw"
        )
    elif expected == "authkey":
        assert result == TpapEncryptionSession._authkey_mask("pw", "xy", "0123456789")
    elif expected == "salted":
        assert result == hashlib.sha256(b"adminsaltpw").hexdigest()
    else:
        assert result == expected


@pytest.mark.parametrize(
    "extra",
    [
        {
            "type": "password_shadow",
            "params": {"passwd_id": 1, "passwd_prefix": "$1$salt$"},
        },
        {
            "type": "password_shadow",
            "params": {"passwd_id": 5, "passwd_prefix": "$5$salt$"},
        },
        {"type": "password_shadow", "params": {"passwd_id": 99}},
        {"type": "password_shadow", "params": "invalid"},
        {"type": "password_shadow", "params": {"passwd_id": "invalid"}},
        {"type": "password_authkey", "params": {}},
        {"type": "password_sha_with_salt", "params": {"sha_name": "bad"}},
        {"type": "password_sha_with_salt", "params": {"sha_name": 0, "sha_salt": "bad"}},
    ],
)
def test_build_credentials_fallbacks(extra):
    assert TpapEncryptionSession._build_credentials(extra, "user", "pw", "AABBCCDDEEFF")


def test_mac_passcode_and_suite_validation():
    assert len(TpapEncryptionSession._mac_pass_from_device_mac("AA:BB:CC:DD:EE:FF")) == 64
    with pytest.raises(TapoProtocolError, match="Invalid device MAC"):
        TpapEncryptionSession._mac_pass_from_device_mac("not-a-mac")
    with pytest.raises(TapoProtocolError, match="too short"):
        TpapEncryptionSession._mac_pass_from_device_mac("AA:BB:CC:DD:EE")
    for suite, curve in ((1, "NIST256p"), (3, "NIST384p"), (5, "NIST521p")):
        assert TpapEncryptionSession._suite_parameters(suite)[2].name == curve
    with pytest.raises(TapoProtocolError, match="Unsupported TPAP suite type"):
        TpapEncryptionSession._suite_parameters(999)
    with pytest.raises(TapoProtocolError, match="Unsupported TPAP session cipher"):
        TpapEncryptionSession._cipher_parameters("unknown")
    with pytest.raises(ValueError, match="base nonce too short"):
        TpapEncryptionSession._nonce_from_base(b"123", 1)


async def test_register_validation_and_cmac_suite():
    async with aiohttp.ClientSession() as http_session:
        protocol = TpapProtocol(
            AuthCredential("user", "pw"), "http://device/app", http_session
        )
        session = protocol._encryption_session
        with pytest.raises(TapoProtocolError, match="user random not initialized"):
            session._build_share_params_from_register({}, "secret")
        session._user_random = base64.b64encode(b"u" * 16).decode()
        invalid = [
            ({"dev_random": ""}, "missing dev_random"),
            ({"dev_salt": ""}, "missing dev_salt"),
            ({"dev_share": ""}, "missing dev_share"),
            ({"cipher_suites": None}, "invalid cipher_suites"),
            ({"cipher_suites": "bad"}, "invalid cipher_suites"),
            ({"iterations": None}, "invalid iterations"),
            ({"iterations": "bad"}, "invalid iterations"),
            ({"iterations": 0}, "invalid iterations"),
            ({"encryption": ""}, "missing encryption"),
            ({"encryption": "unknown"}, "Unsupported TPAP session cipher"),
        ]
        for overrides, message in invalid:
            with pytest.raises(TapoProtocolError, match=message):
                session._build_share_params_from_register(
                    _register_result(**overrides), "secret"
                )
        share = session._build_share_params_from_register(
            _register_result(cipher_suites=8), "secret"
        )
        assert share["user_share"]
        assert share["user_confirm"]


async def test_error_codes_and_session_establishment():
    async with aiohttp.ClientSession() as http_session:
        protocol = TpapProtocol(
            AuthCredential("user", "pw"), "http://device/app", http_session
        )
        session = protocol._encryption_session
        session._handle_response_error_code({"error_code": 0}, "success")
        with pytest.raises(TapoRetryableError):
            session._handle_response_error_code(
                {"error_code": TapoError.ERR_SESSION_EXPIRED.value}, "retry"
            )
        with pytest.raises(TapoAuthenticationError):
            session._handle_response_error_code(
                {"error_code": TapoError.INVALID_CREDENTIAL.value}, "auth"
            )
        with pytest.raises(TapoDeviceError):
            session._handle_response_error_code({"error_code": "unknown"}, "device")

        session._expected_dev_confirm = "expected"
        with pytest.raises(TapoProtocolError, match="missing dev_confirm"):
            session._establish_session_from_share_result({})
        with pytest.raises(TapoProtocolError, match="confirmation mismatch"):
            session._establish_session_from_share_result({"dev_confirm": "wrong"})
        session._shared_key = None
        with pytest.raises(TapoProtocolError, match="shared key was not derived"):
            session._establish_session_from_share_result(
                {"dev_confirm": "expected", "sessionId": "SID", "start_seq": 1}
            )
        session._shared_key = b"shared"
        with pytest.raises(TapoProtocolError, match="Missing session fields"):
            session._establish_session_from_share_result(
                {"dev_confirm": "expected", "start_seq": 1}
            )
        with pytest.raises(TapoProtocolError, match="Missing session fields"):
            session._establish_session_from_share_result(
                {"dev_confirm": "expected", "sessionId": "SID"}
            )
        with pytest.raises(TapoProtocolError, match="Invalid session fields"):
            session._establish_session_from_share_result(
                {
                    "dev_confirm": "expected",
                    "sessionId": "SID",
                    "start_seq": "bad",
                }
            )
        session._establish_session_from_share_result(
            {"dev_confirm": "expected", "stok": "SID", "start_seq": 3}
        )
        assert session.is_established


async def test_payload_retry_and_ssl_helpers():
    async with aiohttp.ClientSession() as http_session:
        protocol = TpapProtocol(
            AuthCredential("user", "pw"), "http://device/app", http_session
        )
        session = protocol._encryption_session
        session._tpap_tls = 0
        assert protocol._create_ssl_context() is False
        session._tpap_tls = 1
        assert protocol._create_ssl_context().verify_mode == ssl.CERT_NONE
        session._tpap_tls = 2
        context = protocol._create_ssl_context()
        assert context.verify_mode == ssl.CERT_REQUIRED

        key, nonce = TpapEncryptionSession.key_nonce_from_shared(
            b"shared", "chacha20_poly1305", "SHA512"
        )
        encrypted, tag = TpapEncryptionSession.sec_encrypt(
            "chacha20_poly1305", key, nonce, b"hello", 5
        )
        assert (
            TpapEncryptionSession.sec_decrypt(
                "chacha20_poly1305", key, nonce, encrypted, tag, 5
            )
            == b"hello"
        )

        session._cipher_id = "chacha20_poly1305"
        session._key = key
        session._base_nonce = nonce
        session._session_id = "SID"
        session._sequence = 5
        session._ds_url = URL("http://device/stok=SID/ds")
        payload, sequence = session.encrypt("hello")
        assert sequence == 5 and payload[:4] == struct.pack(">I", 5)
        session._sequence = 5
        session.advance(5)
        session.advance(3)
        assert session._sequence == 6
        with pytest.raises(TapoProtocolError, match="response too short"):
            session.decrypt(b"short", 1)
        response = TpapEncryptionSession._encrypt_payload(
            "chacha20_poly1305", key, nonce, b"world", 8
        )
        assert session.decrypt(struct.pack(">I", 8) + response, 7) == b"world"

        assert protocol._should_retry_live_session(
            TapoRetryableError(TapoError.ERR_STAT_ACCESS, "retry")
        )
        assert protocol._should_retry_live_session(
            aiohttp.ClientConnectionError("disconnected")
        )
        assert not protocol._should_retry_live_session(TapoProtocolError("no"))

        retry_error = TapoRetryableError(TapoError.ERR_SESSION_EXPIRED, "retry")
        protocol._send_once = AsyncMock(side_effect=retry_error)
        protocol.reset = AsyncMock()
        with pytest.raises(TapoRetryableError):
            await protocol.send("{}")
        protocol.reset.assert_not_awaited()

        protocol._send_once = AsyncMock(
            side_effect=[
                retry_error,
                {"error_code": 0, "result": {}},
            ]
        )
        result = await protocol.send_request(TapoRequest.get_device_info())
        assert result.is_success()
        assert protocol._send_once.await_count == 2
        protocol.reset.assert_awaited_once()

        protocol._send_once = AsyncMock(side_effect=retry_error)
        protocol.reset.reset_mock()
        result = await protocol.send_request(TapoRequest.get_device_info(), retry=3)
        assert result.is_failure()
        assert protocol._send_once.await_count == 4
        assert protocol.reset.await_count == 3


def test_certificate_loading_validity_and_signatures():
    ec_root_key = ec.generate_private_key(ec.SECP256R1())
    ec_leaf_key = ec.generate_private_key(ec.SECP256R1())
    root = _certificate(ec_root_key, "root", "root", ec_root_key, is_ca=True)
    leaf = _certificate(ec_leaf_key, "leaf", "root", ec_root_key)
    pem = leaf.public_bytes(serialization.Encoding.PEM).decode()
    der = base64.b64encode(leaf.public_bytes(serialization.Encoding.DER)).decode()
    assert TpapProtocol._load_certificate_value(pem).subject == leaf.subject
    assert TpapProtocol._load_certificate_value(der).subject == leaf.subject
    with pytest.raises(TapoProtocolError, match="Empty certificate"):
        TpapProtocol._load_certificate_value(" ")
    with pytest.raises(TapoProtocolError, match="Invalid certificate"):
        TpapProtocol._load_certificate_value("invalid")
    TpapProtocol._verify_certificate_validity(leaf)
    TpapProtocol._verify_certificate_signature(leaf, root)

    rsa_root_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    rsa_leaf_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    rsa_root = _certificate(rsa_root_key, "root", "root", rsa_root_key, is_ca=True)
    rsa_leaf = _certificate(rsa_leaf_key, "leaf", "root", rsa_root_key)
    TpapProtocol._verify_certificate_signature(rsa_leaf, rsa_root)
    expired = SimpleNamespace(
        not_valid_before=datetime.now() - timedelta(days=2),
        not_valid_after=datetime.now() - timedelta(days=1),
    )
    with pytest.raises(TapoProtocolError, match="outside its validity period"):
        TpapProtocol._verify_certificate_validity(expired)
    no_hash = SimpleNamespace(signature_hash_algorithm=None)
    issuer = SimpleNamespace(public_key=lambda: ec_root_key.public_key())
    with pytest.raises(TapoProtocolError, match="hash algorithm is unavailable"):
        TpapProtocol._verify_certificate_signature(no_hash, issuer)
    with pytest.raises(TapoProtocolError, match="Unsupported DAC issuer"):
        TpapProtocol._verify_certificate_signature(
            leaf, SimpleNamespace(public_key=lambda: object())
        )
    with patch.object(TpapProtocol, "_load_root_ca_certificate", return_value=root):
        TpapProtocol._verify_dac_certificate_chain(leaf, None)


async def test_http_response_and_send_error_paths():
    async with aiohttp.ClientSession() as http_session:
        protocol = TpapProtocol(
            AuthCredential("user", "pw"), "http://device/app", http_session
        )
        assert protocol._load_json_dict(b'{"ok": true}') == {"ok": True}
        with pytest.raises(TapoProtocolError, match="JSON response body type"):
            protocol._load_json_dict(b"[]")

        protocol._send_once = AsyncMock(side_effect=TapoProtocolError("boom"))
        with pytest.raises(TapoProtocolError, match="boom"):
            await protocol.send("{}")
        protocol._send_once = TpapProtocol._send_once.__get__(protocol, TpapProtocol)

        session = protocol._encryption_session
        session.perform_handshake = AsyncMock()
        with pytest.raises(TapoProtocolError, match="not established"):
            await protocol._send_once("{}")

        key, nonce = TpapEncryptionSession.key_nonce_from_shared(b"shared", "aes_128_ccm")
        session._key = key
        session._base_nonce = nonce
        session._session_id = "SID"
        session._sequence = 1
        session._ds_url = URL("http://device/stok=SID/ds")
        protocol._post = AsyncMock(return_value=(500, b"error"))
        with pytest.raises(TapoRetryableError, match="status 500"):
            await protocol._send_once("{}")


async def test_encrypted_tpap_retryable_response_renews_session():
    async with aiohttp.ClientSession() as http_session:
        protocol = TpapProtocol(
            AuthCredential("user", "pw"), "http://device/app", http_session
        )
        session = protocol._encryption_session
        session._session_id = "SID"
        session._sequence = 1
        session._ds_url = URL("http://device/stok=SID/ds")
        session._key = b"key"
        session._base_nonce = b"nonce"
        session.encrypt = Mock(return_value=(b"request", 1))
        session.decrypt = Mock(
            side_effect=[
                json.dumps({"error_code": TapoError.ERR_SESSION_EXPIRED.value}).encode(),
                json.dumps({"error_code": 0, "result": {}}).encode(),
            ]
        )
        protocol._post = AsyncMock(return_value=(200, b"encrypted"))
        protocol.reset = AsyncMock()

        response = await protocol.send_request(TapoRequest.get_device_info(), retry=1)

        assert response.is_success()
        assert protocol._post.await_count == 2
        protocol.reset.assert_awaited_once()


def test_transport_url_and_parse_helpers():
    assert TpapEncryptionSession._parse_optional_int(None) is None
    assert TpapEncryptionSession._parse_optional_int("2") == 2
    assert TpapEncryptionSession._parse_optional_int("bad") is None
    assert TpapEncryptionSession._require_result_dict({"result": {}}) == {}
    with pytest.raises(TapoProtocolError, match="missing result"):
        TpapEncryptionSession._require_result_dict({})
