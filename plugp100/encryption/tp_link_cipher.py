import base64

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding as asymmetric_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .key_pair import KeyPair


class TpLinkCipher:
    def encrypt(self, data) -> str:
        pass

    def decrypt(self, data) -> str:
        pass


class TpLinkCipherCryptography(TpLinkCipher):
    @staticmethod
    def create_from_keypair(handshake_key: str, keypair: KeyPair) -> "TpLinkCipher":
        handshake_key: bytes = base64.b64decode(handshake_key.encode("UTF-8"))
        private_key_data = base64.b64decode(keypair.get_private_key().encode("UTF-8"))

        private_key = serialization.load_der_private_key(private_key_data, None, None)
        key_and_iv = private_key.decrypt(handshake_key, asymmetric_padding.PKCS1v15())
        if key_and_iv is None:
            raise ValueError("Decryption failed!")

        return TpLinkCipherCryptography(key_and_iv[:16], key_and_iv[16:])

    def __init__(self, key, iv):
        self.cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        self.padding_strategy = padding.PKCS7(algorithms.AES.block_size)

    def encrypt(self, data) -> str:
        encryptor = self.cipher.encryptor()
        padder = self.padding_strategy.padder()
        padded_data = padder.update(data.encode("UTF-8")) + padder.finalize()
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(encrypted).decode("UTF-8")

    def decrypt(self, data) -> str:
        decryptor = self.cipher.decryptor()
        unpadder = self.padding_strategy.unpadder()
        decrypted = (
            decryptor.update(base64.b64decode(data.encode("UTF-8")))
            + decryptor.finalize()
        )
        unpadded_data = unpadder.update(decrypted) + unpadder.finalize()
        return unpadded_data.decode("UTF-8")
