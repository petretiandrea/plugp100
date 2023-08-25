import dataclasses


@dataclasses.dataclass
class AuthCredential:
    username: str
    password: str
