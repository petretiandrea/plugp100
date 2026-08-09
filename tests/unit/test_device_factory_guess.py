import asyncio
from unittest.mock import patch

import aiohttp
import pytest

from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.common.credentials import AuthCredential
from plugp100.common.functional.tri import Failure, Success, Try
from plugp100.new.device_factory import (
    DeviceConnectConfiguration,
    _ProtocolCandidate,
    _build_protocol_candidates,
    _guess_protocol,
)
from plugp100.new.errors.invalid_authentication import InvalidAuthentication
from plugp100.new.errors.protocol_guess import (
    HostUnreachableError,
    ProtocolDetectionTimeoutError,
    UnsupportedProtocolError,
)
from plugp100.protocol.klap.klap_protocol import KlapAuthenticationError
from plugp100.protocol.tapo_protocol import TapoProtocol
from plugp100.protocol.tpap_protocol import AuthenticationError
from plugp100.responses.tapo_response import TapoResponse


class FakeCandidateProtocol(TapoProtocol):
    def __init__(self, response=None, delay: float = 0):
        self.response = response
        self.delay = delay
        self.closed = False
        self.retries = []

    @property
    def name(self) -> str:
        return "fake"

    async def send_request(
        self, request: TapoRequest, retry: int = 3
    ) -> Try[TapoResponse[dict]]:
        del request
        self.retries.append(retry)
        if self.delay:
            await asyncio.sleep(self.delay)
        return self.response

    async def close(self):
        self.closed = True


async def test_guess_protocol_closes_failures_and_continues_after_timeout():
    timed_out = FakeCandidateProtocol(delay=1)
    failed = FakeCandidateProtocol(Failure(Exception("not this protocol")))
    working = FakeCandidateProtocol(Success(TapoResponse(0, {"type": "plug"}, None)))
    candidates = [
        _ProtocolCandidate("timeout", lambda: timed_out),
        _ProtocolCandidate("failure", lambda: failed),
        _ProtocolCandidate("working", lambda: working),
    ]
    config = DeviceConnectConfiguration(
        host="device", credentials=AuthCredential("user", "password"), timeout=0.01
    )

    with patch(
        "plugp100.new.device_factory._build_protocol_candidates",
        return_value=candidates,
    ):
        selected = await _guess_protocol(config)

    assert selected is working
    assert timed_out.closed
    assert failed.closed
    assert not working.closed
    assert working.retries == [0]


async def test_protocol_candidates_cover_http_and_https():
    config = DeviceConnectConfiguration(
        host="device", credentials=AuthCredential("user", "password")
    )
    async with aiohttp.ClientSession() as session:
        candidates = _build_protocol_candidates(config, session)
        names = [candidate.name for candidate in candidates]

        assert names == [
            "TPAP HTTP:80",
            "AES HTTP:80",
            "KLAP v1 HTTP:80",
            "KLAP v2 HTTP:80",
            "TPAP HTTPS:4433",
            "AES HTTPS:443",
            "KLAP v1 HTTPS:443",
            "KLAP v2 HTTPS:443",
        ]

        protocols = [candidate.factory() for candidate in candidates]
        try:
            assert [protocol.name for protocol in protocols] == [
                "TPAP",
                "Passthrough",
                "Klap V1",
                "Klap V2",
                "TPAP",
                "Passthrough",
                "Klap V1",
                "Klap V2",
            ]
        finally:
            for protocol in protocols:
                await protocol.close()


@pytest.mark.parametrize(
    "failure",
    [AuthenticationError("invalid password"), KlapAuthenticationError("bad challenge")],
)
async def test_guess_protocol_raises_invalid_authentication_after_all_failures(failure):
    failed = FakeCandidateProtocol(Failure(failure))
    config = DeviceConnectConfiguration(
        host="device", credentials=AuthCredential("user", "password")
    )
    with patch(
        "plugp100.new.device_factory._build_protocol_candidates",
        return_value=[_ProtocolCandidate("failure", lambda: failed)],
    ):
        with pytest.raises(InvalidAuthentication) as raised:
            await _guess_protocol(config)

    assert str(raised.value) == "Unable to authenticate for device"
    assert raised.value.failures == (("failure", failed.response.error()),)
    assert failed.closed


@pytest.mark.parametrize(
    ("failure", "expected_error", "message"),
    [
        (
            asyncio.TimeoutError(),
            ProtocolDetectionTimeoutError,
            "Protocol detection timed out for device",
        ),
        (
            aiohttp.ClientConnectionError("unreachable"),
            HostUnreachableError,
            "Unable to reach device for device",
        ),
        (
            Exception("unexpected response"),
            UnsupportedProtocolError,
            "No supported protocol found for device",
        ),
    ],
)
async def test_guess_protocol_reports_specific_final_error(
    failure, expected_error, message
):
    failed = FakeCandidateProtocol(Failure(failure))
    config = DeviceConnectConfiguration(
        host="device", credentials=AuthCredential("user", "password")
    )

    with patch(
        "plugp100.new.device_factory._build_protocol_candidates",
        return_value=[_ProtocolCandidate("failure", lambda: failed)],
    ):
        with pytest.raises(expected_error) as raised:
            await _guess_protocol(config)

    assert str(raised.value) == message
    assert raised.value.failures == (("failure", failure),)
    assert failed.closed


async def test_guess_protocol_enforces_global_timeout_and_closes_candidate():
    slow = FakeCandidateProtocol(delay=1)
    config = DeviceConnectConfiguration(
        host="device",
        credentials=AuthCredential("user", "password"),
        timeout=None,
        guess_timeout=0.01,
    )

    with patch(
        "plugp100.new.device_factory._build_protocol_candidates",
        return_value=[_ProtocolCandidate("slow", lambda: slow)],
    ):
        with pytest.raises(ProtocolDetectionTimeoutError) as raised:
            await _guess_protocol(config)

    assert raised.value.failures[-1][0] == "global timeout"
    assert slow.closed


async def test_guess_protocol_skips_candidates_on_unavailable_endpoint():
    refused = FakeCandidateProtocol(Failure(ConnectionRefusedError("closed")))
    skipped = FakeCandidateProtocol(Success(TapoResponse(0, {}, None)))
    working = FakeCandidateProtocol(Success(TapoResponse(0, {"type": "plug"}, None)))
    candidates = [
        _ProtocolCandidate("refused", lambda: refused, "http://device:80/app"),
        _ProtocolCandidate("skipped", lambda: skipped, "http://device:80/app"),
        _ProtocolCandidate("working", lambda: working, "https://device:443/app"),
    ]
    config = DeviceConnectConfiguration(
        host="device", credentials=AuthCredential("user", "password")
    )

    with patch(
        "plugp100.new.device_factory._build_protocol_candidates",
        return_value=candidates,
    ):
        selected = await _guess_protocol(config)

    assert selected is working
    assert refused.closed
    assert not skipped.closed
    assert skipped.retries == []
