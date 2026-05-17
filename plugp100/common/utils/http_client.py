from typing import Any

import aiohttp


class AsyncHttp:
    def __init__(self, session: aiohttp.ClientSession, verify_ssl: bool = True):
        self.session = session
        self.session.connector._force_close = True
        self.common_headers = {
            "Content-Type": "application/json",
            "requestByApp": "true",
            "Accept": "application/json",
        }
        # aiohttp expects None (default validation) or False to disable.
        self._ssl = None if verify_ssl else False

    async def async_make_post(self, url, json: Any) -> aiohttp.ClientResponse:
        self.session.cookie_jar.clear()
        async with self.session.post(
            url, json=json, headers=self.common_headers, ssl=self._ssl
        ) as response:
            return await self._force_read_release(response)

    async def async_make_post_cookie(self, url, json, cookie) -> aiohttp.ClientResponse:
        self.session.cookie_jar.clear()
        async with self.session.post(
            url,
            json=json,
            cookies=cookie,
            headers=self.common_headers,
            ssl=self._ssl,
        ) as response:
            return await self._force_read_release(response)

    async def close(self):
        await self.session.close()

    async def _force_read_release(self, response):
        await response.read()
        await response.release()
        return response
