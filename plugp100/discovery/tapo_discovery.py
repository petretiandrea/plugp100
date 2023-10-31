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

from plugp100.encryption.tp_link_cipher import TpLinkCipherCryptography

logger = logging.getLogger(__name__)

PKT_ONBOARD_REQUEST = b"\x11\x00"
PKT_ONBOARD_RESPONSE = b'"\x01'

OUR_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OUR_PUBLIC_KEY_PEM = (
    OUR_PRIVATE_KEY.public_key()
    .public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    .decode()
)


def eprint(*args, **kwargs):
    sio = io.StringIO()
    print(*args, **kwargs, file=sio)
    logger.debug(sio.getvalue())


def handle_incoming_handshake_request(key, iv, rsa_key, result, data):
    tapo_cipher = TpLinkCipherCryptography(key, iv)
    clearSessionKeyBytes = iv + key

    encryptedDataB64 = tapo_cipher.encrypt(json.dumps(data))

    eprint("public key to be imported", rsa_key)
    public_key = serialization.load_pem_public_key(rsa_key.encode())
    encryptedSessionKeyBytes = public_key.encrypt(
        clearSessionKeyBytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()), algorithm=hashes.SHA1(), label=None
        ),
    )
    encryptedSessionKeyBytesB64 = base64.b64encode(encryptedSessionKeyBytes).decode()

    result_copy = dict(result)
    result_copy["encrypt_info"] = {
        "sym_schm": "AES",
        "key": encryptedSessionKeyBytesB64,
        "data": encryptedDataB64,
    }

    response_json = {
        "error_code": 0,
        "result": result_copy,
    }
    return response_json


def extract_pkt_id(packet):
    return packet[8:12]


def extract_payload_from_package(packet):
    return packet[16:]


def extract_payload_from_package_json(packet):
    return json.loads(packet[16:])


def build_packet_for_payload(payload, pkt_type, pkt_id=b"\x01\x02\x03\x04"):
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


def build_packet_for_payload_json(payload, pkt_type, pkt_id=b"\x01\x02\x03\x04"):
    return build_packet_for_payload(json.dumps(payload).encode(), pkt_type, pkt_id)


def oaep_decrypt(ciphertext):
    return OUR_PRIVATE_KEY.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()), algorithm=hashes.SHA1(), label=None
        ),
    )


def process_encrypted_handshake(response):
    encryptedSessionKey = response["result"]["encrypt_info"]["key"]
    encryptedSessionKeyBytes = base64.b64decode(encryptedSessionKey.encode())
    clearSessionKeyBytes = oaep_decrypt(encryptedSessionKeyBytes)
    if not clearSessionKeyBytes:
        raise ValueError("Decryption failed!")

    b_arr = bytearray()
    b_arr2 = bytearray()

    for i in range(0, 16):
        b_arr.insert(i, clearSessionKeyBytes[i])
    for i in range(0, 16):
        b_arr2.insert(i, clearSessionKeyBytes[i + 16])

    cipher = TpLinkCipherCryptography(b_arr, b_arr2)
    cleartextDataBytes = cipher.decrypt(response["result"]["encrypt_info"]["data"])
    eprint("handshake payload decrypted as", cleartextDataBytes)
    return json.loads(cleartextDataBytes)


class TapoDeviceFinder:
    @staticmethod
    def scan(
        timeout: Optional[int] = 5,
        broadcast: Optional[str] = "255.255.255.255",
    ) -> Generator[dict[str, any], None, None]:
        """
        Launch discovery packets on your default network in order to discover Tapo devices.
        Args:
            timeout: (Optional[int]): Timeout to wait for discovery response
            broadcast: (Optional[str]): The destination IP address to send the discovery to
        Returns:
            list[dict[str, any]]: A list of dictionaries, each containing information about a discovered device.
        Example:
            from plugp100.discovery.tapo_discovery import TapoDeviceFinder
            devices = TapoDeviceFinder.scan()
            for device in devices:
                print(f"IP: {device['ip']}, MAC: {device['mac']}")
        """
        packet = build_packet_for_payload_json(
            {"params": {"rsa_key": OUR_PUBLIC_KEY_PEM}}, PKT_ONBOARD_REQUEST
        )
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, 5)
        sock.sendto(packet, (broadcast, 20002))
        eprint("packet sent", packet)
        before = time.time()
        while True:
            rlist, _, _ = select.select(
                [sock], [], [], 0.1
            )  # Check for readability without blocking
            if sock in rlist:
                try:
                    handshake_packet, addr = sock.recvfrom(2048)
                    eprint("received", addr, handshake_packet)
                    handshake_json = extract_payload_from_package_json(handshake_packet)
                    if handshake_json["error_code"]:
                        continue
                    result = handshake_json["result"]
                    # some devices (e.g. cams for sure) have this obfuscated block of json data under the encrypt_info node:
                    encrypt_info = result.get("encrypt_info")
                    if encrypt_info:
                        encryptedSessionKeyBytes = base64.b64decode(encrypt_info["key"])
                        decryptedSessionKeyBytes = oaep_decrypt(encryptedSessionKeyBytes)
                        cipher = TpLinkCipherCryptography(
                            decryptedSessionKeyBytes[0:16],
                            decryptedSessionKeyBytes[16:32],
                        )
                        clear = cipher.decrypt(encrypt_info["data"])
                        result["encrypt_info_clear"] = json.loads(clear)
                    yield result
                except:
                    pass
            now = time.time()
            if now - before > timeout:
                break
        sock.close()

    @staticmethod
    def classify(
        devices: Generator[dict[str, any], None, None]
    ) -> Generator[dict[str, any], None, None]:
        """
        Classify devices returned by the scan method by IP, MAC address and device_id
        Args:
            devices: (Generator[dict[str, any], None, None]): devices returned by scan()
        Returns:
            dict[str, dict[str, any]]: A dictionary with ip, mac and device_id fields, where devices are indexed by the corresponding field
        Example:
            from plugp100.discovery.tapo_discovery import TapoDeviceFinder
            cdevs = TapoDeviceFinder.classify(TapoDeviceFinder.scan())

            # find the current IP address of a device based on their ID:
            print(cdevs["device_id"]["some-device-id"]["ip"])
        """
        re = {}
        for device in devices:
            for c in ["device_id", "ip", "mac"]:
                if not re.get(c):
                    re[c] = {}
                v = device[c]
                re[c][v] = device
        return re
