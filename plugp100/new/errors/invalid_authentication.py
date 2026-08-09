from typing import Optional


class InvalidAuthentication(Exception):
    def __init__(self, host: str, device_type: Optional[str]):
        message = f"Unable to authenticate or determine protocol for {host}"
        if device_type:
            message += f" ({device_type})"
        super().__init__(message)
