import logging

import aiohttp
import jsons

from plugp100.common.utils.http_client import AsyncHttp
from plugp100.encryption.key_pair import KeyPair

logger = logging.getLogger(__name__)


class TapoApiDiscover:
    @staticmethod
    async def is_tapo_device(address: str, session: aiohttp.ClientSession = None) -> bool:
        url = f"http://{address}/app"
        http = AsyncHttp(aiohttp.ClientSession() if session is None else session)
        key_pair = KeyPair.create_key_pair()

        return False
