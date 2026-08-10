from typing import Optional, Sequence

from .protocol_guess import ProtocolFailure, ProtocolGuessError


class InvalidAuthentication(ProtocolGuessError):
    def __init__(
        self,
        host: str,
        device_type: Optional[str],
        failures: Sequence[ProtocolFailure] = (),
    ):
        super().__init__("Unable to authenticate", host, device_type, failures)
