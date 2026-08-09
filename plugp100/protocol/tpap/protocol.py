"""TPAP transport implementation."""

from __future__ import annotations

import asyncio
import json
import logging
import ssl
from typing import Any

import aiohttp
import jsons
from yarl import URL

from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.common.credentials import AuthCredential
from plugp100.common.functional.tri import Failure, Try
from plugp100.protocol.tapo_protocol import TapoProtocol
from plugp100.responses.tapo_exception import (
    TapoProtocolError,
    TapoRetryableError,
)
from plugp100.responses.tapo_response import TapoResponse

from .certificates import TpapCertificateVerifier
from .session import TpapEncryptionSession

_LOGGER = logging.getLogger(__name__)


class TpapProtocol(TpapCertificateVerifier, TapoProtocol):
    """TPAP protocol adapted from python-kasa PR #1592."""

    DEFAULT_PORT: int = 80
    DEFAULT_HTTPS_PORT: int = 4433
    CIPHERS = ":".join(
        [
            "ECDHE-ECDSA-AES256-GCM-SHA384",
            "ECDHE-ECDSA-AES256-SHA384",
            "ECDHE-ECDSA-AES256-SHA",
            "ECDHE-ECDSA-AES128-GCM-SHA256",
            "ECDHE-ECDSA-AES128-SHA256",
            "ECDHE-ECDSA-AES128-SHA",
            "ECDHE-RSA-AES256-GCM-SHA384",
            "ECDHE-RSA-AES256-SHA384",
            "ECDHE-RSA-AES256-SHA",
            "ECDHE-RSA-AES128-GCM-SHA256",
            "ECDHE-RSA-AES128-SHA256",
            "ECDHE-RSA-AES128-SHA",
        ]
    )
    COMMON_HEADERS = {"Content-Type": "application/json"}

    def __init__(
        self,
        auth_credential: AuthCredential,
        url: str,
        http_session: aiohttp.ClientSession | None = None,
    ) -> None:
        super().__init__()
        self._credential = auth_credential
        self._owns_http_session = http_session is None
        self._http_session = http_session or aiohttp.ClientSession()
        self._ssl_context: ssl.SSLContext | bool | None = None
        configured_url = URL(url)
        self._host = configured_url.host or ""
        self._port = configured_url.port or self.DEFAULT_PORT
        self._bootstrap_url = configured_url.with_path("").with_query(None)
        self._app_url = self._bootstrap_url
        self._known_device_mac = ""
        self._known_tpap_tls: int | None = None
        self._known_tpap_port: int | None = None
        self._known_tpap_dac = False
        self._known_tpap_pake: list[int] = []
        self._known_tpap_user_hash_type: int | None = None
        self._send_lock: asyncio.Lock = asyncio.Lock()
        self._encryption_session = TpapEncryptionSession(self)

    @property
    def default_port(self) -> int:
        return self._port

    @property
    def name(self) -> str:
        return "TPAP"

    def _build_app_url(self, *, tls_mode: int | None, port: int | None) -> URL:
        scheme = "https" if tls_mode in (1, 2) else "http"
        if port and port > 0:
            resolved_port = port
        elif scheme == "https":
            resolved_port = self.DEFAULT_HTTPS_PORT
        else:
            resolved_port = self._port
        return URL.build(
            scheme=scheme,
            host=self._host,
            port=resolved_port,
        )

    def _get_initial_app_url(self) -> URL:
        if not (self._known_tpap_port and self._known_tpap_port > 0) and (
            self._known_tpap_tls not in (1, 2)
        ):
            return self._bootstrap_url

        return self._build_app_url(
            tls_mode=self._known_tpap_tls,
            port=self._known_tpap_port,
        )

    @staticmethod
    def _load_json_dict(payload: bytes) -> dict[str, Any]:
        response_data = json.loads(payload.decode())
        if not isinstance(response_data, dict):
            raise TapoProtocolError("Unexpected TPAP JSON response body type")
        return response_data

    @staticmethod
    def _should_retry_live_session(exc: Exception) -> bool:
        return isinstance(
            exc,
            (
                TapoRetryableError,
                aiohttp.ClientConnectionError,
                aiohttp.ServerTimeoutError,
                TimeoutError,
            ),
        )

    async def get_ssl_context(self) -> ssl.SSLContext | bool:
        """Get or create the SSL context."""
        if self._ssl_context is None:
            loop = asyncio.get_running_loop()
            self._ssl_context = await loop.run_in_executor(None, self._create_ssl_context)
        return self._ssl_context

    def _create_ssl_context(self) -> ssl.SSLContext | bool:
        tls_mode = self._encryption_session.tls_mode
        if tls_mode == 0:
            return False

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.set_ciphers(self.CIPHERS)
        context.check_hostname = False

        if tls_mode in (None, 1):
            context.verify_mode = ssl.CERT_NONE
            return context

        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(cadata=self.TPAP_ROOT_CA_PEM)
        return context

    async def send(self, request: str) -> dict[str, Any]:
        """Send one request without applying retry policy."""
        return await self._send_once(request)

    async def send_request(
        self, request: TapoRequest, retry: int = 3
    ) -> Try[TapoResponse[dict[str, Any]]]:
        payload = jsons.dumps(request)
        attempts = max(retry, 0) + 1
        for attempt in range(attempts):
            try:
                response = await self.send(payload)
                return TapoResponse.try_from_json(response)
            except Exception as exc:
                if attempt == attempts - 1 or not self._should_retry_live_session(exc):
                    return Failure(exc)

                _LOGGER.debug(
                    "TPAP: resetting live session before retry %d/%d after error: %s",
                    attempt + 1,
                    attempts - 1,
                    exc,
                )
                await self.reset()

        raise AssertionError("TPAP retry loop completed without a result")

    async def _send_once(self, request: str) -> dict[str, Any]:
        """Send a single request."""
        if not self._encryption_session.is_established:
            await self._encryption_session.perform_handshake()

        ds_url = self._encryption_session.ds_url
        if ds_url is None:
            raise TapoProtocolError("TPAP transport is not established")

        async with self._send_lock:
            payload, seq = self._encryption_session.encrypt(request)
            headers = {"Content-Type": "application/octet-stream"}
            ssl_context = await self.get_ssl_context()
            status, data = await self._post(
                ds_url,
                data=payload,
                headers=headers,
                ssl=ssl_context,
            )
            if status != 200:
                error_type = TapoRetryableError if status >= 500 else TapoProtocolError
                raise error_type(
                    f"TPAP secure request failed for {self._host}: status {status}"
                )

        if isinstance(data, bytes | bytearray):
            plaintext = self._encryption_session.decrypt(bytes(data), seq)
            response = self._load_json_dict(plaintext)
        elif isinstance(data, dict):
            response = data
        else:
            raise TapoProtocolError("Unexpected TPAP response body type")

        self._encryption_session._handle_response_error_code(response, "request")
        return response

    async def _post(
        self,
        url: URL,
        *,
        json: dict[str, Any] | None = None,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        ssl: ssl.SSLContext | bool | None = None,
    ) -> tuple[int, dict[str, Any] | bytes]:
        async with self._http_session.post(
            url, json=json, data=data, headers=headers, ssl=ssl
        ) as response:
            payload = await response.read()
            content_type = response.headers.get("Content-Type", "").lower()
            if json is not None or "json" in content_type:
                try:
                    return response.status, self._load_json_dict(payload)
                except (UnicodeDecodeError, ValueError):
                    pass
            return response.status, payload

    async def close(self) -> None:
        """Close the owned HTTP session and reset internal state."""
        await self.reset()
        if self._owns_http_session:
            await self._http_session.close()

    async def reset(self) -> None:
        """Reset internal transport state."""
        self._encryption_session.reset()
