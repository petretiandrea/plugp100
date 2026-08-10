"""TPAP session cipher primitives."""

import struct

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESCCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from plugp100.api.transport.exceptions import TapoProtocolError


class TpapCryptoMixin:
    """Key derivation and authenticated encryption used by TPAP sessions."""

    TAG_LEN = 16
    NONCE_LEN = 12
    CIPHER_PARAMETERS = {
        "aes_128_ccm": (
            b"tp-kdf-salt-aes128-key",
            b"tp-kdf-info-aes128-key",
            b"tp-kdf-salt-aes128-iv",
            b"tp-kdf-info-aes128-iv",
            16,
        ),
        "aes_256_ccm": (
            b"tp-kdf-salt-aes256-key",
            b"tp-kdf-info-aes256-key",
            b"tp-kdf-salt-aes256-iv",
            b"tp-kdf-info-aes256-iv",
            32,
        ),
        "chacha20_poly1305": (
            b"tp-kdf-salt-chacha20-key",
            b"tp-kdf-info-chacha20-key",
            b"tp-kdf-salt-chacha20-iv",
            b"tp-kdf-info-chacha20-iv",
            32,
        ),
    }

    @classmethod
    def _normalize_cipher_id(cls, cipher_id: str) -> str:
        return cipher_id.lower().replace("-", "_")

    @classmethod
    def _cipher_parameters(cls, cipher_id: str) -> tuple[bytes, bytes, bytes, bytes, int]:
        normalized = cls._normalize_cipher_id(cipher_id)
        try:
            return cls.CIPHER_PARAMETERS[normalized]
        except KeyError as exc:
            raise TapoProtocolError(
                f"Unsupported TPAP session cipher: {cipher_id}"
            ) from exc

    @staticmethod
    def _hkdf(
        master: bytes, *, salt: bytes, info: bytes, length: int, algo: str = "SHA256"
    ) -> bytes:
        algorithm = hashes.SHA256() if algo.upper() == "SHA256" else hashes.SHA512()
        return HKDF(algorithm=algorithm, length=length, salt=salt, info=info).derive(
            master
        )

    @staticmethod
    def _nonce_from_base(base_nonce: bytes, seq: int) -> bytes:
        if len(base_nonce) < 4:
            raise ValueError("base nonce too short")
        return base_nonce[:-4] + struct.pack(">I", seq)

    @classmethod
    def key_nonce_from_shared(
        cls, shared_key: bytes, cipher_id: str, hkdf_hash: str = "SHA256"
    ) -> tuple[bytes, bytes]:
        """Derive the session key and base nonce."""
        key_salt, key_info, nonce_salt, nonce_info, key_len = cls._cipher_parameters(
            cipher_id
        )
        return (
            cls._hkdf(
                shared_key,
                salt=key_salt,
                info=key_info,
                length=key_len,
                algo=hkdf_hash,
            ),
            cls._hkdf(
                shared_key,
                salt=nonce_salt,
                info=nonce_info,
                length=cls.NONCE_LEN,
                algo=hkdf_hash,
            ),
        )

    @classmethod
    def _encrypt_payload(
        cls, cipher_id: str, key: bytes, base_nonce: bytes, plaintext: bytes, seq: int
    ) -> bytes:
        nonce = cls._nonce_from_base(base_nonce, seq)
        normalized = cls._normalize_cipher_id(cipher_id)
        if normalized.startswith("aes_"):
            return AESCCM(key, tag_length=cls.TAG_LEN).encrypt(nonce, plaintext, None)
        return ChaCha20Poly1305(key).encrypt(nonce, plaintext, None)

    @classmethod
    def _decrypt_payload(
        cls,
        cipher_id: str,
        key: bytes,
        base_nonce: bytes,
        ciphertext_and_tag: bytes,
        seq: int,
    ) -> bytes:
        nonce = cls._nonce_from_base(base_nonce, seq)
        normalized = cls._normalize_cipher_id(cipher_id)
        if normalized.startswith("aes_"):
            return AESCCM(key, tag_length=cls.TAG_LEN).decrypt(
                nonce, ciphertext_and_tag, None
            )
        return ChaCha20Poly1305(key).decrypt(nonce, ciphertext_and_tag, None)

    @classmethod
    def sec_encrypt(
        cls,
        cipher_id: str,
        key: bytes,
        base_nonce: bytes,
        plaintext: bytes,
        seq: int = 1,
    ) -> tuple[bytes, bytes]:
        """Encrypt the message."""
        combined = cls._encrypt_payload(cipher_id, key, base_nonce, plaintext, seq)
        return combined[: -cls.TAG_LEN], combined[-cls.TAG_LEN :]

    @classmethod
    def sec_decrypt(
        cls,
        cipher_id: str,
        key: bytes,
        base_nonce: bytes,
        ciphertext: bytes,
        tag: bytes,
        seq: int = 1,
    ) -> bytes:
        """Decrypt the message."""
        return cls._decrypt_payload(cipher_id, key, base_nonce, ciphertext + tag, seq)
