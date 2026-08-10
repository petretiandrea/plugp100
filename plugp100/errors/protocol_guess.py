from typing import Optional, Sequence, Tuple

ProtocolFailure = Tuple[str, Exception]


class ProtocolGuessError(Exception):
    """Base error raised when automatic protocol detection fails."""

    def __init__(
        self,
        message: str,
        host: str,
        device_type: Optional[str],
        failures: Sequence[ProtocolFailure] = (),
    ):
        target = host if device_type is None else f"{host} ({device_type})"
        super().__init__(f"{message} for {target}")
        self.host = host
        self.device_type = device_type
        self.failures = tuple(failures)


class HostUnreachableError(ProtocolGuessError):
    """No protocol candidate could connect to the device."""

    def __init__(
        self,
        host: str,
        device_type: Optional[str],
        failures: Sequence[ProtocolFailure] = (),
    ):
        super().__init__("Unable to reach device", host, device_type, failures)


class ProtocolDetectionTimeoutError(ProtocolGuessError):
    """Every protocol candidate timed out."""

    def __init__(
        self,
        host: str,
        device_type: Optional[str],
        failures: Sequence[ProtocolFailure] = (),
    ):
        super().__init__("Protocol detection timed out", host, device_type, failures)


class UnsupportedProtocolError(ProtocolGuessError):
    """The device responded, but none of the supported protocols worked."""

    def __init__(
        self,
        host: str,
        device_type: Optional[str],
        failures: Sequence[ProtocolFailure] = (),
    ):
        super().__init__("No supported protocol found", host, device_type, failures)
