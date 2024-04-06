import asyncio
import base64
import json
import logging
import socket
import time
from typing import Optional, Generator

import select

from plugp100.discovery.discovered_device import DiscoveredDevice
from plugp100.discovery.rsa_session import (
    RSASession,
    _build_packet_for_payload_json,
    _extract_payload_from_package_json,
)
from plugp100.encryption.tp_link_cipher import TpLinkCipherCryptography

logger = logging.getLogger(__name__)

PKT_ONBOARD_REQUEST = b"\x11\x00"
PKT_ONBOARD_RESPONSE = b'"\x01'


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
    async def scan(
        timeout: Optional[int] = 5,
        broadcast: Optional[str] = "255.255.255.255",
        port: int = 20002,
    ) -> list[DiscoveredDevice]:
        loop = asyncio.get_event_loop()
        devices_found = await loop.run_in_executor(
            None,
            lambda: list(TapoDiscovery(broadcast, port, timeout)._scan()),
        )
        return [DiscoveredDevice.from_dict(x) for x in devices_found]

    @staticmethod
    async def single_scan(
        ip: str,
        timeout: Optional[int] = 5,
        port: int = 20002,
    ) -> Optional[DiscoveredDevice]:
        devices_found = await TapoDiscovery.scan(timeout, ip, port)
        return devices_found[0] if len(devices_found) > 0 else None
