"""LEB128 VarInt and VarUInt encoding/decoding utilities for Minecraft Bedrock protocol."""

from typing import Tuple


def encode_varuint32(val: int) -> bytes:
    """Encode an unsigned 32-bit integer into LEB128 varuint bytes."""
    val &= 0xFFFFFFFF
    out = bytearray()
    while val >= 0x80:
        out.append((val & 0x7F) | 0x80)
        val >>= 7
    out.append(val & 0x7F)
    return bytes(out)


def decode_varuint32(data: bytes, offset: int = 0) -> Tuple[int, int]:
    """Decode a LEB128 unsigned 32-bit integer from bytes.
    
    Returns (value, new_offset).
    """
    val = 0
    shift = 0
    while shift < 35:
        if offset >= len(data):
            raise IndexError("Unexpected EOF while reading varuint32")
        b = data[offset]
        offset += 1
        val |= (b & 0x7F) << shift
        if not (b & 0x80):
            return val & 0xFFFFFFFF, offset
        shift += 7
    raise ValueError("varuint32 exceeds 35 bits")


def encode_varint32(val: int) -> bytes:
    """Encode a signed 32-bit integer using ZigZag encoding."""
    raw = (val << 1) ^ (val >> 31)
    return encode_varuint32(raw & 0xFFFFFFFF)


def decode_varint32(data: bytes, offset: int = 0) -> Tuple[int, int]:
    """Decode a ZigZag-encoded signed 32-bit integer from bytes."""
    raw, offset = decode_varuint32(data, offset)
    val = (raw >> 1) ^ -(raw & 1)
    return val, offset


def encode_varuint64(val: int) -> bytes:
    """Encode an unsigned 64-bit integer into LEB128 varuint bytes."""
    val &= 0xFFFFFFFFFFFFFFFF
    out = bytearray()
    while val >= 0x80:
        out.append((val & 0x7F) | 0x80)
        val >>= 7
    out.append(val & 0x7F)
    return bytes(out)


def decode_varuint64(data: bytes, offset: int = 0) -> Tuple[int, int]:
    """Decode a LEB128 unsigned 64-bit integer from bytes."""
    val = 0
    shift = 0
    while shift < 70:
        if offset >= len(data):
            raise IndexError("Unexpected EOF while reading varuint64")
        b = data[offset]
        offset += 1
        val |= (b & 0x7F) << shift
        if not (b & 0x80):
            return val & 0xFFFFFFFFFFFFFFFF, offset
        shift += 7
    raise ValueError("varuint64 exceeds 70 bits")


def encode_string(s: str) -> bytes:
    """Encode a string prefixed with its UTF-8 byte length as varuint32."""
    b = s.encode("utf-8")
    return encode_varuint32(len(b)) + b


def decode_string(data: bytes, offset: int = 0) -> Tuple[str, int]:
    """Decode a varuint32 length-prefixed UTF-8 string."""
    length, offset = decode_varuint32(data, offset)
    if offset + length > len(data):
        raise IndexError("Unexpected EOF while reading string content")
    s = data[offset:offset + length].decode("utf-8", errors="replace")
    return s, offset + length
