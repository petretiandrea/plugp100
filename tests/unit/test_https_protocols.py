import ssl
from http.cookies import SimpleCookie
from unittest.mock import AsyncMock, patch

import aiohttp

from plugp100.common.credentials import AuthCredential
from plugp100.common.utils.ssl_utils import ssl_context_for_url
from plugp100.protocol.klap import klap_handshake_v2
from plugp100.protocol.klap.klap_protocol import KlapProtocol
from plugp100.protocol.passthrough_protocol import PassthroughProtocol


class MockResponse:
    status = 200
    cookies = SimpleCookie()

    def __init__(self, payload: bytes = b"{}"):
        self.payload = payload

    async def read(self):
        return self.payload

    async def release(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        pass


def test_ssl_context_is_only_created_for_https():
    assert ssl_context_for_url("http://device/app") is None

    context = ssl_context_for_url("https://device/app")

    assert isinstance(context, ssl.SSLContext)
    assert context.check_hostname is False
    assert context.verify_mode == ssl.CERT_NONE


async def test_aes_https_passes_device_ssl_context_to_aiohttp():
    credentials = AuthCredential("user", "password")
    async with aiohttp.ClientSession() as session:
        protocol = PassthroughProtocol(
            credentials, "https://device:443/app", http_session=session
        )
        with patch.object(
            aiohttp.ClientSession, "post", return_value=MockResponse()
        ) as post:
            await protocol._http.async_make_post("https://device:443/app", {})

        context = post.call_args.kwargs["ssl"]
        assert context is protocol._ssl_context
        assert context.verify_mode == ssl.CERT_NONE


async def test_klap_https_passes_device_ssl_context_to_aiohttp():
    credentials = AuthCredential("user", "password")
    async with aiohttp.ClientSession() as session:
        protocol = KlapProtocol(
            credentials,
            "https://device:443/app",
            klap_handshake_v2(),
            http_session=session,
        )
        with patch.object(
            aiohttp.ClientSession,
            "post",
            new=AsyncMock(return_value=MockResponse(b"response")),
        ) as post:
            response, payload = await protocol.session_post(
                "https://device:443/app/handshake1", data=b"request"
            )

        assert response.status == 200
        assert payload == b"response"
        context = post.call_args.kwargs["ssl"]
        assert context is protocol._ssl_context
        assert context.verify_mode == ssl.CERT_NONE
