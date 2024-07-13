import base64
import hashlib

from cryptography.hazmat.primitives import hashes
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

Base64str = str


def base64encode(to_encode: str) -> Base64str:
    return base64.b64encode(to_encode.encode("UTF-8")).decode("UTF-8")


def sha1_from_str(to_sha: str) -> str:
    sha1_algo = hashlib.sha1()
    sha1_algo.update(to_sha.encode("UTF-8"))
    return sha1_algo.hexdigest()


def sha1(payload: bytes) -> bytes:
    digest = hashes.Hash(hashes.SHA1())
    digest.update(payload)
    return digest.finalize()


def md5(payload: bytes) -> bytes:
    digest = hashes.Hash(hashes.MD5())
    digest.update(payload)
    return digest.finalize()


def sha256(payload: bytes) -> bytes:
    return hashlib.sha256(payload).digest()

def sha256_digest(bytes):
    utf8 = bytes.encode("utf8")
    return hashlib.sha256( utf8 ).hexdigest().upper()

def md5_digest(bytes):
    utf8 = bytes.encode("utf8")
    return hashlib.md5( utf8 ).hexdigest().upper()

def aes_encrypt_request(request, lsk, ivb):
    cipher = AES.new(lsk, AES.MODE_CBC, ivb)
    ct_bytes = cipher.encrypt(pad(request, AES.block_size))
    return ct_bytes

def aes_decrypt_response(response, lsk, ivb):
    cipher = AES.new(lsk, AES.MODE_CBC, ivb)
    pt = cipher.decrypt(response)
    return unpad(pt, AES.block_size)