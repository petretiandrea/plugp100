from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import aiohttp
import pytest

from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.common.credentials import AuthCredential
from plugp100.common.functional.tri import Failure, Success
from plugp100.protocol.passthrough_protocol import PassthroughProtocol
from plugp100.responses.tapo_exception import (
    TAPO_AUTHENTICATION_ERRORS,
    TAPO_RETRYABLE_ERRORS,
    TapoAuthenticationError,
    TapoDeviceError,
    TapoError,
    TapoException,
    TapoProtocolError,
    TapoRetryableError,
    _error_message,
)
from plugp100.responses.tapo_response import TapoResponse


@pytest.mark.parametrize("error", TAPO_RETRYABLE_ERRORS, ids=lambda error: error.name)
def test_retryable_error_codes_are_typed(error: TapoError):
    exception = TapoException.from_error_code(error.value, "device error")

    assert isinstance(exception, TapoRetryableError)
    assert exception.error_code == error.value
    assert exception.tapo_error is error


@pytest.mark.parametrize(
    "error", TAPO_AUTHENTICATION_ERRORS, ids=lambda error: error.name
)
def test_authentication_error_codes_are_typed(error: TapoError):
    exception = TapoException.from_error_code(error.value, "device error")

    assert isinstance(exception, TapoAuthenticationError)
    assert not isinstance(exception, TapoRetryableError)
    assert exception.error_code == error.value


def test_definitive_and_unknown_error_codes_are_device_errors():
    definitive = TapoException.from_error_code(TapoError.INVALID_REQUEST.value, None)
    unknown_numeric = TapoException.from_error_code(-99999, "bad response")
    malformed = TapoException.from_error_code("unexpected", "bad response")

    assert isinstance(definitive, TapoDeviceError)
    assert definitive.tapo_error is TapoError.INVALID_REQUEST
    assert isinstance(unknown_numeric, TapoDeviceError)
    assert unknown_numeric.error_code == -99999
    assert unknown_numeric.raw_error_code == -99999
    assert isinstance(malformed, TapoDeviceError)
    assert malformed.error_code is None
    assert malformed.raw_error_code == "unexpected"


def test_protocol_errors_can_be_created_without_an_error_code():
    exception = TapoProtocolError("malformed response")

    assert str(exception) == "malformed response"
    assert exception.error_code is None


def test_every_known_error_code_has_a_message():
    assert set(TapoError) == set(_error_message)


async def test_passthrough_retries_any_retryable_device_error():
    async with aiohttp.ClientSession() as http_session:
        protocol = PassthroughProtocol(
            AuthCredential("user", "password"),
            "http://device/app",
            http_session=http_session,
        )
        protocol._session = SimpleNamespace(invalidate=Mock())
        protocol._send_request = AsyncMock(
            side_effect=[
                Failure(
                    TapoRetryableError(
                        TapoError.ERR_HTTP_TRANSPORT_FAILED,
                        "temporary transport failure",
                    )
                ),
                Success(TapoResponse(0, {}, None)),
            ]
        )

        response = await protocol.send_request(TapoRequest.get_device_info(), retry=1)

        assert response.is_success()
        assert protocol._send_request.await_count == 2
        protocol._session.invalidate.assert_called_once()
