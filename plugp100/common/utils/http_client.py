import ssl
from typing import Any

import aiohttp


class AsyncHttp:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        ssl_context: ssl.SSLContext | None = None,
    ):
        self.session = session
        self.ssl_context = ssl_context
        self.session.connector._force_close = True
        self.common_headers = {
            "Content-Type": "application/json",
            "requestByApp": "true",
            "Accept": "application/json",
        }

    async def async_make_post(self, url, json: Any) -> aiohttp.ClientResponse:
        self.session.cookie_jar.clear()
        async with self.session.post(
            url, json=json, headers=self.common_headers, ssl=self.ssl_context
        ) as response:
            return await self._force_read_release(response)

    async def async_make_post_cookie(self, url, json, cookie) -> aiohttp.ClientResponse:
        self.session.cookie_jar.clear()
        async with self.session.post(
            url,
            json=json,
            cookies=cookie,
            headers=self.common_headers,
            ssl=self.ssl_context,
        ) as response:
            return await self._force_read_release(response)

    async def close(self):
        await self.session.close()

    async def _force_read_release(self, response):
        await response.read()
        await response.release()
        return response
