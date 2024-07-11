from typing import Any

import aiohttp
import logging
import ssl
logger = logging.getLogger(__name__)

class AsyncHttp:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.session.connector._force_close = True
        self.common_headers = {
            "Content-Type": "application/json",
            "requestByApp": "true",
            "Accept": "application/json",
        }

    async def async_make_post(self, url, json: Any, headers=None) -> aiohttp.ClientResponse:
        self.session.cookie_jar.clear()
        if headers is None:
            headers = self.common_headers
        try:
            async with self.session.post(
                url, json=json, headers=headers
            ) as response:
                return await self._force_read_release(response)
        except Exception as e:
            logger.warning(f"POST failed: {type(e).__name__} {e}")

    async def async_make_post_cookie(self, url, json, cookie) -> aiohttp.ClientResponse:
        self.session.cookie_jar.clear()
        async with self.session.post(
            url, json=json, cookies=cookie, headers=self.common_headers
        ) as response:
            return await self._force_read_release(response)

    async def close(self):
        await self.session.close()

    async def _force_read_release(self, response):
        await response.read()
        await response.release()
        return response
