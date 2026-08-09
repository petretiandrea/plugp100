"""Backward-compatible imports for the TPAP protocol."""

from .tpap import (
    SMART_AUTHENTICATION_ERRORS,
    SMART_RETRYABLE_ERRORS,
    AuthenticationError,
    DeviceError,
    KasaException,
    SmartErrorCode,
    TpapEncryptionSession,
    TpapError,
    TpapProtocol,
    _ConnectionError,
    _RetryableError,
)

__all__ = [
    "AuthenticationError",
    "DeviceError",
    "KasaException",
    "SMART_AUTHENTICATION_ERRORS",
    "SMART_RETRYABLE_ERRORS",
    "SmartErrorCode",
    "TpapEncryptionSession",
    "TpapError",
    "TpapProtocol",
    "_ConnectionError",
    "_RetryableError",
]
