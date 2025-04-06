import secrets
from http.cookies import SimpleCookie
from unittest.mock import patch

import aiohttp
import pytest

from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.api.tapo_client import TapoClient
from plugp100.common.credentials import AuthCredential
from plugp100.common.functional.tri import Success
from plugp100.protocol.klap import (
    KlapHandshakeRevision,
    klap_handshake_v2,
    klap_handshake_v1,
)
from plugp100.protocol.klap.klap_protocol import KlapProtocol, KlapChiper


@pytest.mark.parametrize(
    "klap_revision",
    [
        pytest.param(klap_handshake_v1(), id="KLAPv1"),
        pytest.param(klap_handshake_v2(), id="KLAPv2"),
    ],
)
async def test_query(klap_revision: KlapHandshakeRevision):
    client_credentials = AuthCredential("username", "password")
    with patch.object(aiohttp.ClientSession, "post") as mock_post:
        protocol = KlapProtocol(
            client_credentials, "http://localhost", klap_strategy=klap_revision
        )
        mocked_behaviour = _mock_klap_server(client_credentials, klap_revision, protocol)
        mock_post.side_effect = mocked_behaviour

        client = TapoClient(
            auth_credential=client_credentials, url="http://localhost", protocol=protocol
        )

        expected_sequence = None
        for _ in range(10):
            resp = await client.execute_raw_request(
                TapoRequest(method="none", params="{}")
            )
            assert resp.get_or_raise() == Success([]).get_or_raise()
            assert (
                expected_sequence is None
                or expected_sequence == protocol._klap_session.chiper._seq
            )
            expected_sequence = protocol._klap_session.chiper._seq + 1


def _mock_klap_server(
    client_credentials: AuthCredential,
    klap_revision: KlapHandshakeRevision,
    protocol: KlapProtocol,
):
    server_seed = secrets.token_bytes(16)
    device_auth_hash = klap_revision.generate_auth_hash(client_credentials)

    async def _return_response(url: str, params=None, data=None, *_, **__):
        if "/handshake1" in url:
            client_seed = data
            client_seed_auth = klap_revision.handshake1_seed_auth_hash(
                client_seed, server_seed, device_auth_hash
            )
            return _mock_aiohttp_response(200, server_seed + client_seed_auth)
        elif "/handshake2" in url:
            return _mock_aiohttp_response(200, b"")
        elif "/request" in url:
            current_sequence = params.get("seq")
            chiper = KlapChiper(
                protocol._klap_session.chiper.local_seed,
                protocol._klap_session.chiper.remote_seed,
                protocol._klap_session.chiper.user_hash,
            )
            chiper._seq = current_sequence - 1
            response_data, seq = chiper.encrypt('{"error_code": 0, "result": []}')
            return _mock_aiohttp_response(200, response_data)

    return _return_response


def _mock_aiohttp_response(status_code: int, data: bytes, cookies={}):
    simple_cookie = SimpleCookie()
    if cookies:
        for key, value in cookies.items():
            simple_cookie[key] = value
    return MockResponse(status_code, data, simple_cookie)


class MockResponse:
    def __init__(self, status, data, cookies: SimpleCookie[str]):
        self.content = data
        self.status = status
        self.cookies = cookies

    async def read(self):
        return self.content

    async def release(self):
        pass

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self
