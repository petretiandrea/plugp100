import base64
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from plugp100.encryption.helpers import Base64str


class KeyPair(object):
    @staticmethod
    def create_key_pair(key_size: int = 1024) -> "KeyPair":
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
        public_key = private_key.public_key()

        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return KeyPair(
            private_key=base64.b64encode(private_key_bytes).decode("UTF-8"),
            public_key=base64.b64encode(public_key_bytes).decode("UTF-8"),
        )

    def __init__(self, private_key: str, public_key: str):
        self.private_key = private_key
        self.public_key = public_key

    def get_private_key(self) -> Base64str:
        return self.private_key

    def get_public_key(self) -> Base64str:
        return self.public_key
