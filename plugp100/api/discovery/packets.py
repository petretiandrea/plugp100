import json
import struct
import zlib


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
    return skeleton[0:12] + calculated_crc32_bytes + skeleton[16:]


def build_packet_for_payload_json(payload, pkt_type, pkt_id=b"\x01\x02\x03\x04"):
    return build_packet_for_payload(json.dumps(payload).encode(), pkt_type, pkt_id)


def extract_payload_from_package_json(packet):
    return json.loads(packet[16:])


__all__ = [
    "build_packet_for_payload",
    "build_packet_for_payload_json",
    "extract_payload_from_package_json",
]
