import base64
import json
import struct
from unittest.mock import AsyncMock

import aiohttp
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.common.credentials import AuthCredential
from plugp100.new.device_factory import (
    DeviceConnectConfiguration,
    _get_or_guess_protocol,
)
from plugp100.protocol.tpap_protocol import TpapEncryptionSession, TpapProtocol


def test_tpap_cipher_roundtrip():
    key, nonce = TpapEncryptionSession.key_nonce_from_shared(
        b"shared secret", "aes_128_ccm"
    )
    ciphertext, tag = TpapEncryptionSession.sec_encrypt(
        "aes_128_ccm", key, nonce, b"hello", seq=3
    )

    assert (
        TpapEncryptionSession.sec_decrypt(
            "aes_128_ccm", key, nonce, ciphertext, tag, seq=3
        )
        == b"hello"
    )


async def test_tpap_handshake_and_request():
    async with aiohttp.ClientSession() as http_session:
        protocol = TpapProtocol(
            AuthCredential("user@example.com", "password"),
            "http://tpap-device:80/app",
            http_session,
        )
        encryption_session = protocol._encryption_session
        device_private_key = ec.derive_private_key(7, ec.SECP256R1())
        device_share = device_private_key.public_key().public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.UncompressedPoint,
        )

        async def post(url, *, json=None, data=None, headers=None, ssl=None):
            del url, headers, ssl
            if json is not None:
                sub_method = json["params"]["sub_method"]
                if sub_method == "discover":
                    return 200, {
                        "error_code": 0,
                        "result": {
                            "mac": "AA:BB:CC:DD:EE:FF",
                            "tpap": {
                                "tls": 0,
                                "port": 80,
                                "dac": False,
                                "pake": [0],
                            },
                        },
                    }
                if sub_method == "pake_register":
                    return 200, {
                        "error_code": 0,
                        "result": {
                            "dev_random": base64.b64encode(b"r" * 16).decode(),
                            "dev_salt": base64.b64encode(b"s" * 16).decode(),
                            "dev_share": base64.b64encode(device_share).decode(),
                            "cipher_suites": 2,
                            "iterations": 100,
                            "encryption": "aes_128_ccm",
                        },
                    }
                assert sub_method == "pake_share"
                return 200, {
                    "error_code": 0,
                    "result": {
                        "dev_confirm": encryption_session._expected_dev_confirm,
                        "sessionId": "test-session",
                        "start_seq": 4,
                    },
                }

            assert data is not None
            request_seq = struct.unpack(">I", data[:4])[0]
            plaintext = encryption_session._decrypt_payload(
                encryption_session._cipher_id,
                encryption_session._key,
                encryption_session._base_nonce,
                data[4:],
                request_seq,
            )
            assert json_module.loads(plaintext)["method"] == "get_device_info"
            response = json_module.dumps(
                {"error_code": 0, "result": {"model": "P100"}}
            ).encode()
            encrypted = encryption_session._encrypt_payload(
                encryption_session._cipher_id,
                encryption_session._key,
                encryption_session._base_nonce,
                response,
                request_seq,
            )
            return 200, struct.pack(">I", request_seq) + encrypted

        json_module = json
        protocol._post = AsyncMock(side_effect=post)

        response = await protocol.send_request(TapoRequest.get_device_info())

        assert response.is_success()
        assert response.get().result == {"model": "P100"}
        assert protocol.name == "TPAP"


async def test_factory_selects_tpap_protocol():
    async with aiohttp.ClientSession() as http_session:
        config = DeviceConnectConfiguration(
            host="tpap-device",
            port=4433,
            credentials=AuthCredential("user", "password"),
            encryption_type="TPAP",
            is_support_https=True,
        )

        protocol = await _get_or_guess_protocol(config, http_session)

        assert isinstance(protocol, TpapProtocol)
        assert config.url == "https://tpap-device:4433/app"
