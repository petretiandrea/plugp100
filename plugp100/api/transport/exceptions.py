from enum import Enum
from typing import Any, Optional, Type


class TapoError(Enum):
    ERR_UNSPECIFIC = -1001
    ERR_AES_DECODE_FAIL = -1005
    ERR_REQUEST_LEN_ERROR = -1006
    ERR_CLOUD_FAILED = -1007
    ERR_PARAMS = -1008
    ERR_DEVICE = -1301
    ERR_SESSION_PARAM = -1101
    INVALID_PUBLIC_KEY = -1010
    INVALID_CREDENTIAL = -1501
    ERR_STAT_ACCESS = -2203
    ERR_SESSION_EXPIRED = -40401
    ERR_INVALID_NONCE = -40413
    INVALID_REQUEST = -1002
    INVALID_JSON = -1003
    ERR_NULL_TRANSPORT = 1000
    ERR_CMD_COMMAND_CANCEL = 1001
    ERR_TRANSPORT_NOT_AVAILABLE = 1002
    ERR_TRANSPORT_UNKNOWN_CREDENTIALS = 1003
    ERR_HAND_SHAKE_FAILED = 1100
    ERR_LOGIN_FAILED = 1111
    ERR_HTTP_TRANSPORT_FAILED = 1112
    ERR_MULTI_REQUEST_FAILED = 1200
    ERR_SESSION_TIMEOUT = 9999


TAPO_RETRYABLE_ERRORS = frozenset(
    {
        TapoError.ERR_UNSPECIFIC,
        TapoError.ERR_DEVICE,
        TapoError.ERR_STAT_ACCESS,
        TapoError.ERR_SESSION_EXPIRED,
        TapoError.ERR_INVALID_NONCE,
        TapoError.ERR_TRANSPORT_NOT_AVAILABLE,
        TapoError.ERR_HTTP_TRANSPORT_FAILED,
        TapoError.ERR_SESSION_TIMEOUT,
    }
)

TAPO_AUTHENTICATION_ERRORS = frozenset(
    {
        TapoError.ERR_AES_DECODE_FAIL,
        TapoError.INVALID_CREDENTIAL,
        TapoError.ERR_TRANSPORT_UNKNOWN_CREDENTIALS,
        TapoError.ERR_HAND_SHAKE_FAILED,
        TapoError.ERR_LOGIN_FAILED,
    }
)


_error_message = {
    TapoError.ERR_UNSPECIFIC: "Unspecified device error",
    TapoError.INVALID_PUBLIC_KEY: "Invalid Public Key Length",
    TapoError.INVALID_CREDENTIAL: "Invalid credentials",
    TapoError.INVALID_REQUEST: "Invalid request",
    TapoError.INVALID_JSON: "Malformed json request",
    TapoError.ERR_AES_DECODE_FAIL: "AES Decode Fail",
    TapoError.ERR_REQUEST_LEN_ERROR: "Request length error",
    TapoError.ERR_CLOUD_FAILED: "Cloud request failed",
    TapoError.ERR_PARAMS: "Request params error",
    TapoError.ERR_SESSION_PARAM: "Session params error",
    TapoError.ERR_STAT_ACCESS: "Session state access error",
    TapoError.ERR_SESSION_EXPIRED: "Session expired",
    TapoError.ERR_INVALID_NONCE: "Invalid session nonce",
    TapoError.ERR_NULL_TRANSPORT: "Null transport error",
    TapoError.ERR_CMD_COMMAND_CANCEL: "Command cancel error",
    TapoError.ERR_TRANSPORT_NOT_AVAILABLE: "Transport not available error",
    TapoError.ERR_TRANSPORT_UNKNOWN_CREDENTIALS: "Unknown transport credentials",
    TapoError.ERR_HAND_SHAKE_FAILED: "Handshake failed",
    TapoError.ERR_LOGIN_FAILED: "Login failed",
    TapoError.ERR_HTTP_TRANSPORT_FAILED: "Http transport error",
    TapoError.ERR_MULTI_REQUEST_FAILED: "Multirequest failed",
    TapoError.ERR_SESSION_TIMEOUT: "Session Timeout",
    TapoError.ERR_DEVICE: "Rate limit exceeded",
}


class TapoException(Exception):
    """Base exception for errors returned by or raised while talking to a device."""

    error_code: int | None
    tapo_error: TapoError | None
    raw_error_code: Any

    @staticmethod
    def from_error_code(error_code: Any, msg: Optional[str]) -> "TapoException":
        try:
            if isinstance(error_code, TapoError):
                normalized_code = error_code.value
            elif isinstance(error_code, int) and not isinstance(error_code, bool):
                normalized_code = error_code
            else:
                raise ValueError
        except (TypeError, ValueError):
            exception = TapoDeviceError(
                None,
                f"Returned unknown error_code: {error_code}  msg: {msg}",
            )
            exception.raw_error_code = error_code
            return exception

        try:
            tapo_error = TapoError(normalized_code)
        except ValueError:
            return TapoDeviceError(
                normalized_code,
                f"Returned unknown error_code: {error_code}  msg: {msg}",
            )

        exception_type: Type[TapoException]
        if tapo_error in TAPO_RETRYABLE_ERRORS:
            exception_type = TapoRetryableError
        elif tapo_error in TAPO_AUTHENTICATION_ERRORS:
            exception_type = TapoAuthenticationError
        else:
            exception_type = TapoDeviceError

        return exception_type(
            normalized_code,
            f"Returned error_code: {tapo_error}: {_error_message[tapo_error]}",
        )

    def __init__(
        self,
        error_code: int | TapoError | str | None,
        msg: Optional[str] = None,
    ):
        if msg is None and isinstance(error_code, str):
            msg = error_code
            error_code = None

        if isinstance(error_code, TapoError):
            self.tapo_error = error_code
            self.error_code = error_code.value
        else:
            self.error_code = error_code
            try:
                self.tapo_error = (
                    TapoError(error_code) if error_code is not None else None
                )
            except ValueError:
                self.tapo_error = None

        self.raw_error_code = self.error_code
        super().__init__(msg or "Tapo device error")


class TapoProtocolError(TapoException):
    """A protocol or response error with an optional device error code."""


class TapoAuthenticationError(TapoProtocolError):
    """Credentials were rejected; retrying the same credentials will not help."""


class TapoDeviceError(TapoProtocolError):
    """A definitive error returned by the device."""


class TapoRetryableError(TapoProtocolError):
    """A transient error for which the protocol may renew its session and retry."""
