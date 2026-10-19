import base64
import os
import time
from http.cookies import SimpleCookie
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import aiohttp
from aiohttp import web
from aiohttp.test_utils import TestServer
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from multidict import CIMultiDict
import pytest

from plugp100.api.protocol.securepassthrough_transport import SecurePassthroughTransport
from plugp100.common.utils.http_client import AsyncHttp


async def _handshake(request: web.Request) -> web.Response:
    body = await request.json()
    public_key = serialization.load_pem_public_key(body["params"]["key"].encode())
    key = public_key.encrypt(os.urandom(32), padding.PKCS1v15())
    response = web.json_response(
        {"error_code": 0, "result": {"key": base64.b64encode(key).decode()}}
    )
    response.headers["Set-Cookie"] = "TP_SESSIONID=ABCDEF;TIMEOUT=1440"
    return response


async def test_handshake_reads_session_timeout_from_set_cookie():
    app = web.Application()
    app.router.add_post("/app", _handshake)
    async with TestServer(app) as server, aiohttp.ClientSession() as session:
        transport = SecurePassthroughTransport(AsyncHttp(session))
        result = await transport.handshake(str(server.make_url("/app")))

    handshake_session = result.get_or_raise()
    assert handshake_session.session_id == "ABCDEF"
    assert not handshake_session.is_handshake_session_expired()


@pytest.mark.parametrize(
    ("parsed_timeout", "set_cookie_headers", "expected_timeout"),
    [
        ("300", ["TP_SESSIONID=session;TIMEOUT=1440"], 300),
        (None, ["TP_SESSIONID=session"], 1440),
        (
            None,
            ["OTHER=value;TIMEOUT=300", "TP_SESSIONID=session;Path=/;TIMEOUT=1440"],
            1440,
        ),
    ],
)
async def test_handshake_timeout_fallbacks(
    parsed_timeout, set_cookie_headers, expected_timeout
):
    cookies = SimpleCookie()
    cookies["TP_SESSIONID"] = "session"
    if parsed_timeout is not None:
        cookies["TIMEOUT"] = parsed_timeout
    response = SimpleNamespace(
        cookies=cookies,
        headers=CIMultiDict([("Set-Cookie", header) for header in set_cookie_headers]),
        json=AsyncMock(return_value={"error_code": 0, "result": {"key": "encrypted"}}),
    )
    http = SimpleNamespace(async_make_post=AsyncMock(return_value=response))

    with patch(
        "plugp100.api.protocol.securepassthrough_transport.TpLinkCipherCryptography.create_from_keypair",
        return_value=object(),
    ):
        session = (
            await SecurePassthroughTransport(http).handshake("http://device/app")
        ).get()

    assert session.session_id == "session"
    assert abs(session.expire_at - time.time() * 1000 - expected_timeout * 1000) < 1_000
