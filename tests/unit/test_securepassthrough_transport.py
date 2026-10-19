import base64
import os

import aiohttp
from aiohttp import web
from aiohttp.test_utils import TestServer
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

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
