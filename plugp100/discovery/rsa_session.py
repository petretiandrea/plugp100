import json
import logging
import struct
import zlib

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

logger = logging.getLogger(__name__)

PKT_ONBOARD_REQUEST = b"\x11\x00"
PKT_ONBOARD_RESPONSE = b'"\x01'


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


def _build_packet_for_payload(payload, pkt_type, pkt_id=b"\x01\x02\x03\x04"):
    len_bytes = struct.pack(">h", len(payload))
    skeleton = (
        b"\x02\x00\x00\x01"
        + len_bytes
        + pkt_type
        + pkt_id
        + b"\x5A\x6B\x7C\x8D"
        + payload
    )
    calculated_crc32 = zlib.crc32(skeleton) & 0xFFFFFFFF
    calculated_crc32_bytes = struct.pack(">I", calculated_crc32)
    re = skeleton[0:12] + calculated_crc32_bytes + skeleton[16:]
    return re


def _build_packet_for_payload_json(payload, pkt_type, pkt_id=b"\x01\x02\x03\x04"):
    return _build_packet_for_payload(json.dumps(payload).encode(), pkt_type, pkt_id)


def _extract_payload_from_package_json(packet):
    return json.loads(packet[16:])
