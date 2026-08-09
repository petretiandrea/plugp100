"""TPAP error types and device error codes."""

from enum import IntEnum

import aiohttp


class SmartErrorCode(IntEnum):
    SUCCESS = 0
    UNSPECIFIC_ERROR = -1001
    AES_DECODE_FAIL_ERROR = -1005
    LOGIN_ERROR = -1501
    STAT_ACCESS_ERROR = -2203
    SESSION_EXPIRED = -40401
    INVALID_NONCE = -40413
    TRANSPORT_UNKNOWN_CREDENTIALS_ERROR = 1003
    TRANSPORT_NOT_AVAILABLE_ERROR = 1002
    HAND_SHAKE_FAILED_ERROR = 1100
    LOGIN_FAILED_ERROR = 1111
    HTTP_TRANSPORT_FAILED_ERROR = 1112
    SESSION_TIMEOUT_ERROR = 9999
    INTERNAL_UNKNOWN_ERROR = -100_000

    @staticmethod
    def from_int(value: int) -> "SmartErrorCode":
        return SmartErrorCode(value)


SMART_RETRYABLE_ERRORS = {
    SmartErrorCode.TRANSPORT_NOT_AVAILABLE_ERROR,
    SmartErrorCode.HTTP_TRANSPORT_FAILED_ERROR,
    SmartErrorCode.UNSPECIFIC_ERROR,
    SmartErrorCode.SESSION_TIMEOUT_ERROR,
    SmartErrorCode.SESSION_EXPIRED,
    SmartErrorCode.INVALID_NONCE,
    SmartErrorCode.STAT_ACCESS_ERROR,
}
SMART_AUTHENTICATION_ERRORS = {
    SmartErrorCode.LOGIN_ERROR,
    SmartErrorCode.LOGIN_FAILED_ERROR,
    SmartErrorCode.AES_DECODE_FAIL_ERROR,
    SmartErrorCode.HAND_SHAKE_FAILED_ERROR,
    SmartErrorCode.TRANSPORT_UNKNOWN_CREDENTIALS_ERROR,
}


class TpapError(Exception):
    def __init__(self, message: str, error_code: SmartErrorCode | None = None):
        super().__init__(message)
        self.error_code = error_code


class AuthenticationError(TpapError):
    pass


class DeviceError(TpapError):
    pass


class _RetryableError(TpapError):
    pass


KasaException = TpapError
_ConnectionError = aiohttp.ClientError
