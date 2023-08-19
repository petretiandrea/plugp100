from dataclasses import dataclass


@dataclass
class HandshakeParams:
    key: str

    def __init__(self, key: str):
        self.key: str = f"-----BEGIN PUBLIC KEY-----\n{key}\n-----END PUBLIC KEY-----\n"
