import logging

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

logger = logging.getLogger(__name__)


class RSASession:
    def __init__(self):
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = (
            self.private_key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode()
        )

    def decrypt(self, cipher_text: bytes) -> bytes:
        return self.private_key.decrypt(
            cipher_text,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None,
            ),
        )


__all__ = ["RSASession"]
