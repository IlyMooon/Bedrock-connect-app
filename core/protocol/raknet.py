"""RakNet Protocol implementation for Minecraft Bedrock Edition."""

import struct
import time
from typing import List, Tuple, Dict, Any, Optional

# Constants
RAKNET_MAGIC = b"\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd\x124Vx"
RAKNET_PROTOCOL_VERSION = 11

# Offline message IDs
ID_CONNECTED_PING = 0x00
ID_UNCONNECTED_PING = 0x01
ID_UNCONNECTED_PING_OPEN_CONNECTIONS = 0x02
ID_CONNECTED_PONG = 0x03
ID_OPEN_CONNECTION_REQUEST_1 = 0x05
ID_OPEN_CONNECTION_REPLY_1 = 0x06
ID_OPEN_CONNECTION_REQUEST_2 = 0x07
ID_OPEN_CONNECTION_REPLY_2 = 0x08
ID_CONNECTION_REQUEST = 0x09
ID_CONNECTION_REQUEST_ACCEPTED = 0x10
ID_NEW_INCOMING_CONNECTION = 0x13
ID_DISCONNECTION_NOTIFICATION = 0x15
ID_INCOMPATIBLE_PROTOCOL_VERSION = 0x19
ID_UNCONNECTED_PONG = 0x1C

# Bedrock batch game packet
ID_GAME_PACKET = 0xFE

# Datagram & ACK flags
BITFLAG_DATAGRAM = 0x80
BITFLAG_ACK = 0x40
BITFLAG_NACK = 0x20
BITFLAG_NEEDS_B_AND_AS = 0x04

# Reliability types
RELIABILITY_UNRELIABLE = 0
RELIABILITY_UNRELIABLE_SEQUENCED = 1
RELIABILITY_RELIABLE = 2
RELIABILITY_RELIABLE_ORDERED = 3
RELIABILITY_RELIABLE_SEQUENCED = 4

SPLIT_FLAG = 0x10


def encode_uint24_le(val: int) -> bytes:
    """Encode an unsigned 24-bit integer into 3 little-endian bytes."""
    return struct.pack("<I", val & 0xFFFFFF)[:3]


def decode_uint24_le(data: bytes, offset: int = 0) -> Tuple[int, int]:
    """Decode an unsigned 24-bit little-endian integer from bytes."""
    if offset + 3 > len(data):
        raise IndexError("Unexpected EOF reading uint24_le")
    b0, b1, b2 = data[offset], data[offset + 1], data[offset + 2]
    val = b0 | (b1 << 8) | (b2 << 16)
    return val, offset + 3


def encode_address(ip: str, port: int) -> bytes:
    """Encode an IPv4 address according to RakNet spec (bitwise inverted octets)."""
    try:
        parts = [int(p) for p in ip.split(".")]
        if len(parts) != 4:
            raise ValueError()
    except Exception:
        parts = [127, 0, 0, 1]

    inv_ip = bytes((~p) & 0xFF for p in parts)
    return b"\x04" + inv_ip + struct.pack(">H", port)


def decode_address(data: bytes, offset: int = 0) -> Tuple[Tuple[str, int], int]:
    """Decode an address from RakNet packet data."""
    if offset >= len(data):
        raise IndexError("Unexpected EOF reading address")

    addr_type = data[offset]
    if addr_type == 4:
        if offset + 7 > len(data):
            raise IndexError("Unexpected EOF reading IPv4 address")
        octets = [str((~b) & 0xFF) for b in data[offset + 1:offset + 5]]
        ip = ".".join(octets)
        port = struct.unpack(">H", data[offset + 5:offset + 7])[0]
        return (ip, port), offset + 7
    elif addr_type == 6:
        # IPv6: 1 (type) + 2 (family) + 2 (port) + 4 (flowinfo) + 16 (ip) + 4 (scope) = 29
        if offset + 29 > len(data):
            raise IndexError("Unexpected EOF reading IPv6 address")
        port = struct.unpack(">H", data[offset + 3:offset + 5])[0]
        return ("::1", port), offset + 29
    else:
        # Fallback
        return ("127.0.0.1", 19132), offset + 7


# --- Unconnected Ping / Pong ---

def build_unconnected_pong(ping_time: int, server_guid: int, motd: str) -> bytes:
    """Build a RakNet Unconnected Pong packet (0x1C)."""
    motd_bytes = motd.encode("utf-8")
    motd_len = len(motd_bytes)
    return (
        struct.pack(">B Q q 16s H", ID_UNCONNECTED_PONG, ping_time, server_guid, RAKNET_MAGIC, motd_len)
        + motd_bytes
    )


def parse_unconnected_pong(data: bytes) -> Optional[Dict[str, Any]]:
    """Parse an Unconnected Pong packet."""
    if len(data) < 35 or data[0] != ID_UNCONNECTED_PONG:
        return None
    ping_time, server_guid, magic, motd_len = struct.unpack(">Q q 16s H", data[1:35])
    if magic != RAKNET_MAGIC:
        return None
    motd = data[35:35 + motd_len].decode("utf-8", errors="replace")
    return {
        "ping_time": ping_time,
        "server_guid": server_guid,
        "motd": motd
    }


# --- Handshake Packets (Open Connection 1 & 2) ---

def parse_open_connection_request_1(data: bytes) -> Optional[Dict[str, Any]]:
    """Parse Open Connection Request 1 (0x05)."""
    if len(data) < 18 or data[0] != ID_OPEN_CONNECTION_REQUEST_1:
        return None
    magic = data[1:17]
    if magic != RAKNET_MAGIC:
        return None
    protocol_version = data[17]
    mtu = len(data) + 28  # Including UDP/IP headers typically
    return {
        "protocol_version": protocol_version,
        "mtu": min(mtu, 1492),
        "raw_mtu": len(data)
    }


def build_open_connection_reply_1(server_guid: int, mtu: int) -> bytes:
    """Build Open Connection Reply 1 (0x06)."""
    # 0x06 + magic (16) + guid (8) + security flag (1: 0x00) + mtu (2)
    return struct.pack(
        ">B 16s q B H",
        ID_OPEN_CONNECTION_REPLY_1,
        RAKNET_MAGIC,
        server_guid,
        0x00,
        mtu
    )


def parse_open_connection_request_2(data: bytes) -> Optional[Dict[str, Any]]:
    """Parse Open Connection Request 2 (0x07)."""
    if len(data) < 34 or data[0] != ID_OPEN_CONNECTION_REQUEST_2:
        return None
    magic = data[1:17]
    if magic != RAKNET_MAGIC:
        return None

    offset = 17
    server_addr, offset = decode_address(data, offset)
    if offset + 10 > len(data):
        return None

    mtu = struct.unpack(">H", data[offset:offset + 2])[0]
    client_guid = struct.unpack(">q", data[offset + 2:offset + 10])[0]

    return {
        "server_address": server_addr,
        "mtu": mtu,
        "client_guid": client_guid
    }


def build_open_connection_reply_2(server_guid: int, client_ip: str, client_port: int, mtu: int) -> bytes:
    """Build Open Connection Reply 2 (0x08)."""
    addr_bytes = encode_address(client_ip, client_port)
    # 0x08 + magic (16) + guid (8) + client_addr + mtu (2) + security (1: 0x00)
    return (
        struct.pack(">B 16s q", ID_OPEN_CONNECTION_REPLY_2, RAKNET_MAGIC, server_guid)
        + addr_bytes
        + struct.pack(">H B", mtu, 0x00)
    )


# --- Encapsulated Frame & Datagram Packets ---

class EncapsulatedPacket:
    """A RakNet frame encapsulated inside a Datagram."""

    def __init__(
        self,
        content: bytes,
        reliability: int = RELIABILITY_RELIABLE_ORDERED,
        message_index: int = 0,
        order_index: int = 0,
        order_channel: int = 0,
        split: bool = False,
        split_count: int = 0,
        split_id: int = 0,
        split_index: int = 0
    ):
        self.content = content
        self.reliability = reliability
        self.message_index = message_index
        self.order_index = order_index
        self.order_channel = order_channel
        self.split = split
        self.split_count = split_count
        self.split_id = split_id
        self.split_index = split_index

    def serialize(self) -> bytes:
        """Serialize the encapsulated frame to bytes."""
        header = (self.reliability & 0x07) << 5
        if self.split:
            header |= SPLIT_FLAG

        out = bytearray()
        out.append(header)
        out.extend(struct.pack(">H", len(self.content) << 3))

        # Reliable
        if self.reliability in (RELIABILITY_RELIABLE, RELIABILITY_RELIABLE_ORDERED, RELIABILITY_RELIABLE_SEQUENCED):
            out.extend(encode_uint24_le(self.message_index))

        # Sequenced
        if self.reliability in (RELIABILITY_UNRELIABLE_SEQUENCED, RELIABILITY_RELIABLE_SEQUENCED):
            out.extend(encode_uint24_le(0))

        # Ordered
        if self.reliability in (RELIABILITY_RELIABLE_ORDERED, RELIABILITY_RELIABLE_SEQUENCED):
            out.extend(encode_uint24_le(self.order_index))
            out.append(self.order_channel)

        # Split fragment info
        if self.split:
            out.extend(struct.pack(">I H I", self.split_count, self.split_id, self.split_index))

        out.extend(self.content)
        return bytes(out)

    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> Tuple["EncapsulatedPacket", int]:
        """Deserialize an encapsulated packet from bytes. Returns (packet, new_offset)."""
        if offset + 3 > len(data):
            raise IndexError("Unexpected EOF reading frame header")

        header = data[offset]
        reliability = (header >> 5) & 0x07
        is_split = bool(header & SPLIT_FLAG)

        content_len_bytes = struct.unpack(">H", data[offset + 1:offset + 3])[0] >> 3
        offset += 3

        message_index = 0
        if reliability in (RELIABILITY_RELIABLE, RELIABILITY_RELIABLE_ORDERED, RELIABILITY_RELIABLE_SEQUENCED):
            message_index, offset = decode_uint24_le(data, offset)

        if reliability in (RELIABILITY_UNRELIABLE_SEQUENCED, RELIABILITY_RELIABLE_SEQUENCED):
            _, offset = decode_uint24_le(data, offset)

        order_index = 0
        order_channel = 0
        if reliability in (RELIABILITY_RELIABLE_ORDERED, RELIABILITY_RELIABLE_SEQUENCED):
            order_index, offset = decode_uint24_le(data, offset)
            order_channel = data[offset]
            offset += 1

        split_count = 0
        split_id = 0
        split_index = 0
        if is_split:
            if offset + 10 > len(data):
                raise IndexError("Unexpected EOF reading split header")
            split_count, split_id, split_index = struct.unpack(">I H I", data[offset:offset + 10])
            offset += 10

        if offset + content_len_bytes > len(data):
            raise IndexError("Unexpected EOF reading frame payload")

        content = data[offset:offset + content_len_bytes]
        offset += content_len_bytes

        pk = cls(
            content=content,
            reliability=reliability,
            message_index=message_index,
            order_index=order_index,
            order_channel=order_channel,
            split=is_split,
            split_count=split_count,
            split_id=split_id,
            split_index=split_index
        )
        return pk, offset


def build_datagram(sequence_number: int, frames: List[EncapsulatedPacket]) -> bytes:
    """Build a RakNet Datagram (0x84) containing one or more frames."""
    header = BITFLAG_DATAGRAM | BITFLAG_NEEDS_B_AND_AS  # 0x84
    body = bytearray([header])
    body.extend(encode_uint24_le(sequence_number))
    for f in frames:
        body.extend(f.serialize())
    return bytes(body)


def parse_datagram(data: bytes) -> Optional[Tuple[int, List[EncapsulatedPacket]]]:
    """Parse a RakNet Datagram. Returns (sequence_number, list_of_frames)."""
    if len(data) < 4 or (data[0] & BITFLAG_DATAGRAM) == 0:
        return None

    seq_num, offset = decode_uint24_le(data, 1)
    frames = []

    while offset < len(data):
        try:
            frame, offset = EncapsulatedPacket.deserialize(data, offset)
            frames.append(frame)
        except Exception:
            break

    return seq_num, frames


# --- ACK / NACK Packets ---

def build_ack(sequence_numbers: List[int]) -> bytes:
    """Build an ACK packet (0xC0) acknowledging received sequence numbers."""
    if not sequence_numbers:
        return bytes([BITFLAG_ACK | BITFLAG_DATAGRAM, 0x00, 0x00])

    sorted_seqs = sorted(set(sequence_numbers))
    records = []
    
    start = sorted_seqs[0]
    end = start

    for seq in sorted_seqs[1:]:
        if seq == end + 1:
            end = seq
        else:
            records.append((start, end))
            start = seq
            end = seq
    records.append((start, end))

    out = bytearray([BITFLAG_ACK | BITFLAG_DATAGRAM])
    out.extend(struct.pack(">H", len(records)))

    for r_start, r_end in records:
        if r_start == r_end:
            out.append(0x01)  # Single packet
            out.extend(encode_uint24_le(r_start))
        else:
            out.append(0x00)  # Range of packets
            out.extend(encode_uint24_le(r_start))
            out.extend(encode_uint24_le(r_end))

    return bytes(out)


def parse_ack(data: bytes) -> List[int]:
    """Parse an ACK packet and extract acknowledged sequence numbers."""
    if len(data) < 3 or (data[0] & (BITFLAG_ACK | BITFLAG_DATAGRAM)) != (BITFLAG_ACK | BITFLAG_DATAGRAM):
        return []

    record_count = struct.unpack(">H", data[1:3])[0]
    offset = 3
    seq_nums = []

    for _ in range(record_count):
        if offset >= len(data):
            break
        record_type = data[offset]
        offset += 1
        if record_type == 0x01:  # Single
            if offset + 3 > len(data):
                break
            seq, offset = decode_uint24_le(data, offset)
            seq_nums.append(seq)
        elif record_type == 0x00:  # Range
            if offset + 6 > len(data):
                break
            start, offset = decode_uint24_le(data, offset)
            end, offset = decode_uint24_le(data, offset)
            seq_nums.extend(range(start, end + 1))

    return seq_nums


# --- Internal Session Packets ---

def parse_connection_request(data: bytes) -> Optional[Dict[str, Any]]:
    """Parse Connection Request (0x09)."""
    if len(data) < 18 or data[0] != ID_CONNECTION_REQUEST:
        return None
    client_guid, ping_time = struct.unpack(">q q", data[1:17])
    use_encryption = bool(data[17]) if len(data) > 17 else False
    return {
        "client_guid": client_guid,
        "ping_time": ping_time,
        "use_encryption": use_encryption
    }


def build_connection_request_accepted(
    client_ip: str,
    client_port: int,
    ping_time: int,
    pong_time: Optional[int] = None
) -> bytes:
    """Build Connection Request Accepted (0x10)."""
    if pong_time is None:
        pong_time = int(time.time() * 1000)

    client_addr = encode_address(client_ip, client_port)
    system_index = struct.pack(">H", 0)

    # 10 or 20 internal system addresses
    sys_addr = encode_address("127.0.0.1", 0)
    sys_addrs = sys_addr * 10

    times = struct.pack(">q q", ping_time, pong_time)
    return bytes([ID_CONNECTION_REQUEST_ACCEPTED]) + client_addr + system_index + sys_addrs + times


def parse_connected_ping(data: bytes) -> Optional[int]:
    """Parse Connected Ping (0x00). Returns ping_time."""
    if len(data) < 9 or data[0] != ID_CONNECTED_PING:
        return None
    return struct.unpack(">q", data[1:9])[0]


def build_connected_pong(ping_time: int, pong_time: Optional[int] = None) -> bytes:
    """Build Connected Pong (0x03)."""
    if pong_time is None:
        pong_time = int(time.time() * 1000)
    return struct.pack(">B q q", ID_CONNECTED_PONG, ping_time, pong_time)
