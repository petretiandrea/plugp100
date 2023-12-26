import base64
import io
import json
import logging
import socket
import struct
import time
import zlib
from typing import Optional, Generator

import select
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from plugp100.discovery.discovered_device import DiscoveredDevice
from plugp100.encryption.tp_link_cipher import TpLinkCipherCryptography

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


class TapoDiscovery:
    def __init__(self, broadcast, port, timeout):
        self.broadcast = broadcast
        self.port = port
        self.timeout = timeout

    def _scan(self) -> Generator[dict[str, any], None, None]:
        rsa_session = RSASession()
        packet = _build_packet_for_payload_json(
            {"params": {"rsa_key": rsa_session.public_key}}, PKT_ONBOARD_REQUEST
        )
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, 5)
        sock.sendto(packet, (self.broadcast, self.port))
        start = now = time.time()
        while now - start <= self.timeout:
            rlist, _, _ = select.select(
                [sock], [], [], 0.1
            )  # Check for readability without blocking
            if sock in rlist:
                try:
                    handshake_packet, addr = sock.recvfrom(2048)
                    handshake_json = _extract_payload_from_package_json(handshake_packet)
                    if handshake_json["error_code"]:
                        continue
                    result = handshake_json["result"]
                    # some devices (e.g. cams for sure) have this obfuscated block of json data under the encrypt_info node:
                    encrypt_info = result.get("encrypt_info")
                    if encrypt_info:
                        encrypted_session_key_bytes = base64.b64decode(
                            encrypt_info["key"]
                        )
                        decrypted_session_key_bytes = rsa_session.decrypt(
                            encrypted_session_key_bytes
                        )
                        cipher = TpLinkCipherCryptography(
                            decrypted_session_key_bytes[0:16],
                            decrypted_session_key_bytes[16:32],
                        )
                        clear = cipher.decrypt(encrypt_info["data"])
                        result["encrypt_info_clear"] = json.loads(clear)
                    yield result
                except:
                    pass
            now = time.time()
        sock.close()

    @staticmethod
    def scan(
        timeout: Optional[int] = 5,
        broadcast: Optional[str] = "255.255.255.255",
        port: int = 20002,
    ) -> Generator[DiscoveredDevice, None, None]:
        for x in TapoDiscovery(broadcast, port, timeout)._scan():
            yield DiscoveredDevice.from_dict(x)
