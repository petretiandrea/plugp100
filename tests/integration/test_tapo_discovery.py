import unittest
import socket
import threading
import json
import base64
import select

from plugp100.discovery.tapo_discovery import (
    TapoDeviceFinder,
    eprint,
    extract_pkt_id,
    build_packet_for_payload_json,
    extract_payload_from_package_json,
    PKT_ONBOARD_RESPONSE,
    handle_incoming_handshake_request,
)


class TapoDiscoveryTest(unittest.TestCase):
    def _emulated_tapo_device(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # we bind to loopback here since we dont want other devices on the LAN to interfere with the unit tests
            sock.bind(("127.0.0.1", 20002))
            pollerObject = select.poll()
            pollerObject.register(sock, select.POLLIN)
            fdVsEvent = pollerObject.poll(1000)
            if not fdVsEvent:
                return

            packet, addr = sock.recvfrom(2048)
            request = extract_payload_from_package_json(packet)

            iv = b"1234567890123456"
            key = b"1234567890123456"
            data = {
                "device_id": "11111111111111111111CE6645443EAE20758575",
                "http_port": 50443,
                "connect_type": "wireless",
                "connect_ssid": "",
                "owner": "md5hashofowner",
                "sd_status": "offline",
            }
            rsa_key = request["params"]["rsa_key"].replace("\\n", "\n")
            result = {
                "device_id": "11111111111111111118A86DF4865F41",
                "device_name": "Tapo_Camera",
                "device_type": "SMART.IPCAMERA",
                "device_model": "C110",
                "ip": "1.2.3.4",
                "mac": "B8-27-EB-11-11-11",
                "hardware_version": "1.0",
                "firmware_version": "1.1.22 Build 220726 Rel.10212n(4555)",
                "factory_default": True,
                "mgt_encrypt_schm": {"is_support_https": True},
            }
            response = handle_incoming_handshake_request(key, iv, rsa_key, result, data)
            pkt_id = extract_pkt_id(packet)
            responsePacket = build_packet_for_payload_json(
                response, PKT_ONBOARD_RESPONSE, pkt_id
            )
            eprint("sending response", responsePacket)
            sock.sendto(responsePacket, addr)

    def test_end_to_end(self):
        t = threading.Thread(target=self._emulated_tapo_device)
        t.start()
        devices = list(TapoDeviceFinder.scan(broadcast="127.0.0.1", timeout=2))
        t.join(timeout=3)

        self.assertEqual(len(devices), 1)

        # optimal asymmetric encryption padding; this has some randomness and we verify the decrypted version anyway:
        del devices[0]["encrypt_info"]

        self.assertEqual(
            devices,
            [
                {
                    "device_id": "11111111111111111118A86DF4865F41",
                    "device_name": "Tapo_Camera",
                    "device_type": "SMART.IPCAMERA",
                    "device_model": "C110",
                    "ip": "1.2.3.4",
                    "mac": "B8-27-EB-11-11-11",
                    "hardware_version": "1.0",
                    "firmware_version": "1.1.22 Build 220726 Rel.10212n(4555)",
                    "factory_default": True,
                    "mgt_encrypt_schm": {"is_support_https": True},
                    "encrypt_info_clear": {
                        "device_id": "11111111111111111111CE6645443EAE20758575",
                        "http_port": 50443,
                        "connect_type": "wireless",
                        "connect_ssid": "",
                        "owner": "md5hashofowner",
                        "sd_status": "offline",
                    },
                }
            ],
        )

    def test_classify(self):
        dev1 = {"ip": "ip1", "mac": "mac1", "device_id": "did1"}
        dev2 = {"ip": "ip2", "mac": "mac2", "device_id": "did2"}
        cdevs = TapoDeviceFinder.classify([dev1, dev2])
        self.assertEqual(
            cdevs,
            {
                "ip": {"ip1": dev1, "ip2": dev2},
                "mac": {"mac1": dev1, "mac2": dev2},
                "device_id": {"did1": dev1, "did2": dev2},
            },
        )
