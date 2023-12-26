import json
import socket
import threading
import unittest

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

from plugp100.discovery.discovered_device import DiscoveredDevice, EncryptionScheme
from plugp100.discovery.tapo_discovery import (
    TapoDiscovery,
    _build_packet_for_payload_json,
    PKT_ONBOARD_RESPONSE,
)


def _prepare_fake_handshake_response(key, iv, rsa_key, result):
    clear_session_key_bytes = iv + key

    public_key = serialization.load_pem_public_key(rsa_key.encode())
    encrypted_session_key_bytes = public_key.encrypt(
        clear_session_key_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()), algorithm=hashes.SHA1(), label=None
        ),
    )
    result_copy = dict(result)
    response_json = {
        "error_code": 0,
        "result": result_copy,
    }
    return response_json


class TapoDiscoveryTest(unittest.TestCase):
    def _emulated_tapo_device(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setblocking(True)
            sock.settimeout(5)

            # we bind to loopback here since we dont want other devices on the LAN to interfere with the unit tests
            sock.bind(("127.0.0.1", 20002))
            handshake_packet, addr = sock.recvfrom(2048)

            request = json.loads(handshake_packet[16:])
            iv = b"1234567890123456"
            key = b"1234567890123456"
            rsa_key = request["params"]["rsa_key"].replace("\\n", "\n")
            result = {
                "device_id": "26d9887af76f0d5facf8febeb20f6ec9",
                "owner": "006EE6989D4F3A0F47715B4F1585CC27",
                "device_type": "SMART.TAPOPLUG",
                "device_model": "P105(IT)",
                "ip": "192.168.1.3",
                "mac": "9C-53-22-A7-C8-35",
                "is_support_iot_cloud": True,
                "obd_src": "tplink",
                "factory_default": False,
                "mgt_encrypt_schm": {
                    "is_support_https": False,
                    "encrypt_type": "KLAP",
                    "http_port": 80,
                    "lv": 2,
                },
            }
            response = _prepare_fake_handshake_response(key, iv, rsa_key, result)
            pkt_id = handshake_packet[8:12]
            to_send = _build_packet_for_payload_json(
                response, PKT_ONBOARD_RESPONSE, pkt_id
            )
            sock.sendto(to_send, addr)

    def test_end_to_end(self):
        t = threading.Thread(target=self._emulated_tapo_device)
        t.start()
        devices = list(TapoDiscovery.scan(broadcast="127.0.0.1", timeout=2))
        t.join(timeout=3)

        self.assertEqual(len(devices), 1)

        self.assertEqual(
            devices,
            [
                DiscoveredDevice(
                    device_type="SMART.TAPOPLUG",
                    device_model="P105(IT)",
                    ip="192.168.1.3",
                    mac="9C-53-22-A7-C8-35",
                    mgt_encrypt_schm=EncryptionScheme(
                        is_support_https=False, encrypt_type="KLAP", http_port=80, lv=2
                    ),
                    device_id="26d9887af76f0d5facf8febeb20f6ec9",
                    owner="006EE6989D4F3A0F47715B4F1585CC27",
                    hw_ver=None,
                    is_support_iot_cloud=True,
                    obd_src="tplink",
                    factory_default=False,
                )
            ],
        )
