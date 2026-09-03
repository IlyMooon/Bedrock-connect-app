"""Minecraft Bedrock game packets & batch framing implementation."""

import binascii
import json
import re
import struct
import zlib
from typing import List, Tuple, Dict, Any, Optional

from core.protocol.varint import (
    encode_varuint32,
    decode_varuint32,
    encode_string,
    decode_string,
)

# Bedrock Packet IDs
ID_LOGIN = 1                      # 0x01
ID_PLAY_STATUS = 2                # 0x02
ID_SERVER_TO_CLIENT_HANDSHAKE = 3 # 0x03
ID_CLIENT_TO_SERVER_HANDSHAKE = 4 # 0x04
ID_DISCONNECT = 5                 # 0x05
ID_RESOURCE_PACKS_INFO = 6          # 0x06
ID_RESOURCE_PACK_STACK = 7          # 0x07
ID_RESOURCE_PACK_CLIENT_RESPONSE = 8 # 0x08
ID_START_GAME = 11                  # 0x0B
ID_LEVEL_CHUNK = 58                 # 0x3A
ID_TRANSFER = 85                    # 0x55
ID_SET_LOCAL_PLAYER_AS_INITIALIZED = 113 # 0x71
ID_NETWORK_SETTINGS = 143           # 0x8F
ID_REQUEST_NETWORK_SETTINGS = 193   # 0xC1

# Resource Pack Response Statuses
RESPONSE_STATUS_REFUSED = 1
RESPONSE_STATUS_SEND_PACKS = 2
RESPONSE_STATUS_HAVE_ALL_PACKS = 3
RESPONSE_STATUS_COMPLETED = 4

# Bedrock Version Constants (Minecraft 1.26.45 / 26.45)
CURRENT_PROTOCOL_VERSION = 2168
CURRENT_VERSION_STRING = "1.26.45"

# Compression Algorithms
COMPRESSION_ZLIB = 0
COMPRESSION_SNAPPY = 1
COMPRESSION_NONE = 0xFFFF

# Play Statuses
STATUS_LOGIN_SUCCESS = 0
STATUS_LOGIN_FAILED_CLIENT_OLD = 1
STATUS_LOGIN_FAILED_SERVER_OLD = 2
STATUS_PLAYER_SPAWN = 3


def compress_flate(data: bytes) -> bytes:
    """Compress data using raw Deflate (RFC 1951) as required by Minecraft Bedrock."""
    comp = zlib.compressobj(level=6, method=zlib.DEFLATED, wbits=-zlib.MAX_WBITS)
    return comp.compress(data) + comp.flush()


def decompress_flate(data: bytes) -> bytes:
    """Decompress data using raw Deflate (RFC 1951) with fallback to RFC 1950 zlib."""
    try:
        # Standard Minecraft Bedrock raw deflate stream (no zlib headers)
        return zlib.decompress(data, -zlib.MAX_WBITS)
    except Exception:
        try:
            # Fallback to standard zlib format
            return zlib.decompress(data)
        except Exception:
            return data


def encode_packet_header(packet_id: int, sender_subclient: int = 0, recipient_subclient: int = 0) -> bytes:
    """Encode the Bedrock packet header."""
    raw = (packet_id & 0x3FF) | ((sender_subclient & 0x03) << 10) | ((recipient_subclient & 0x03) << 12)
    return encode_varuint32(raw)


def decode_packet_header(data: bytes, offset: int = 0) -> Tuple[int, int]:
    """Decode the packet ID from a packet header. Returns (packet_id, new_offset)."""
    raw, offset = decode_varuint32(data, offset)
    packet_id = raw & 0x3FF
    return packet_id, offset


# --- Batch Framing (0xFE) ---

def encode_batch(packets: List[bytes], compression_algo: int = COMPRESSION_NONE) -> bytes:
    """Encode multiple game packets into a 0xFE Bedrock Batch packet."""
    raw_batch = bytearray()
    for pk in packets:
        raw_batch.extend(encode_varuint32(len(pk)))
        raw_batch.extend(pk)

    if compression_algo == COMPRESSION_ZLIB:
        compressed = compress_flate(bytes(raw_batch))
        # 0xFE + 0x00 (Zlib algorithm byte) + compressed payload
        return b"\xfe\x00" + compressed
    elif compression_algo == COMPRESSION_NONE:
        # Uncompressed batch with marker
        return b"\xfe\xff" + raw_batch
    else:
        # Raw batch without compression byte (used for initial network settings handshake)
        return b"\xfe" + raw_batch


def decode_batch(data: bytes) -> List[bytes]:
    """Decode a 0xFE Bedrock Batch packet into individual game packet payloads."""
    if len(data) < 2 or data[0] != 0xFE:
        return []

    payload = data[1:]

    # Check compression header byte if present
    if len(payload) > 0:
        algo_byte = payload[0]
        if algo_byte == 0x00:
            # Flate / Zlib compressed
            payload = decompress_flate(payload[1:])
        elif algo_byte == 0xFF:
            # Uncompressed with marker
            payload = payload[1:]
        elif algo_byte == 0x01:
            # Snappy (rare in Bedrock default LAN, attempt decompress if module available)
            try:
                import snappy
                payload = snappy.decompress(payload[1:])
            except Exception:
                pass

    packets = []
    offset = 0
    while offset < len(payload):
        try:
            length, offset = decode_varuint32(payload, offset)
            if offset + length > len(payload):
                break
            packets.append(payload[offset:offset + length])
            offset += length
        except Exception:
            break

    return packets


# --- Packet Serialization ---

def parse_request_network_settings(payload: bytes) -> Optional[Dict[str, Any]]:
    """Parse RequestNetworkSettingsPacket (ID 193 / 0xC1)."""
    try:
        packet_id, offset = decode_packet_header(payload, 0)
        if packet_id != ID_REQUEST_NETWORK_SETTINGS:
            return None
        if offset + 4 > len(payload):
            return None
        client_protocol = struct.unpack(">i", payload[offset:offset + 4])[0]
        return {"protocol_version": client_protocol}
    except Exception:
        return None


def build_network_settings(
    compression_threshold: int = 1,
    compression_algorithm: int = COMPRESSION_ZLIB
) -> bytes:
    """Build NetworkSettingsPacket (ID 143 / 0x8F)."""
    header = encode_packet_header(ID_NETWORK_SETTINGS)
    # compression_threshold (uint16 LE) + compression_algo (uint16 LE) + client_throttle (bool) + threshold (uint8) + scalar (float32 LE)
    body = struct.pack("<H H B B f", compression_threshold, compression_algorithm, 0, 0, 0.0)
    return header + body


def parse_login(payload: bytes) -> Optional[Dict[str, Any]]:
    """Parse LoginPacket (ID 1 / 0x01) and extract player Gamertag and protocol version."""
    try:
        packet_id, offset = decode_packet_header(payload, 0)
        if packet_id != ID_LOGIN:
            return None

        if offset + 4 > len(payload):
            return None
        protocol_version = struct.unpack(">i", payload[offset:offset + 4])[0]
        offset += 4

        connection_request = payload[offset:]

        # Search for displayName in the JWT JSON tokens inside connection_request
        display_name = "Joueur Console"
        try:
            text = connection_request.decode("utf-8", errors="ignore")
            # Match "displayName":"<name>"
            match = re.search(r'"displayName"\s*:\s*"([^"]+)"', text)
            if match:
                display_name = match.group(1)
        except Exception:
            pass

        return {
            "protocol_version": protocol_version,
            "display_name": display_name
        }
    except Exception:
        return None


def build_play_status(status: int = STATUS_LOGIN_SUCCESS) -> bytes:
    """Build PlayStatusPacket (ID 2 / 0x02)."""
    header = encode_packet_header(ID_PLAY_STATUS)
    body = struct.pack(">i", status)
    return header + body


def build_transfer_packet(address: str, port: int, reload_world: bool = False) -> bytes:
    """Build TransferPacket (ID 85 / 0x55).
    
    Tells the Minecraft Bedrock client to disconnect from the local game
    and connect directly to the target external server.
    """
    header = encode_packet_header(ID_TRANSFER)
    addr_bytes = encode_string(address)
    port_bytes = struct.pack("<H", port)
    reload_bytes = b"\x01" if reload_world else b"\x00"
    gathering_info = b"\x00"  # Optional GatheringJoinInfo: false
    return header + addr_bytes + port_bytes + reload_bytes + gathering_info


def build_resource_packs_info(protocol_version: int = CURRENT_PROTOCOL_VERSION) -> bytes:
    """Build ResourcePacksInfoPacket (ID 6 / 0x06).

    Informs the client about available resource packs.
    Sending 0 packs allows the client to immediately progress past 'Chargement des packs de ressources'.
    """
    header = encode_packet_header(ID_RESOURCE_PACKS_INFO)
    data = bytearray(header)
    # forcedToAccept (bool)
    data.append(0)
    # hasAddonPacks (bool)
    data.append(0)
    # scriptingEnabled (bool)
    data.append(0)

    if protocol_version >= 818:
        # vibrantVisualsForceDisabled (bool)
        data.append(0)
        # worldTemplateId (UUID 16 bytes LE: zeros)
        data.extend(b"\x00" * 16)
        # worldTemplateVersion (string: empty)
        data.extend(encode_string(""))

    if protocol_version >= 2168:
        # resourcePackInfos array length (VarUInt32 0)
        data.extend(encode_varuint32(0))
    else:
        # behaviorPackInfos count (uint16 LE 0)
        data.extend(struct.pack("<H", 0))
        # resourcePackInfos count (uint16 LE 0)
        data.extend(struct.pack("<H", 0))

    return bytes(data)


def build_resource_pack_stack(
    game_version: str = CURRENT_VERSION_STRING,
    protocol_version: int = CURRENT_PROTOCOL_VERSION
) -> bytes:
    """Build ResourcePackStackPacket (ID 7 / 0x07).

    Completes the resource pack negotiation sequence so the client finishes loading packs.
    """
    header = encode_packet_header(ID_RESOURCE_PACK_STACK)
    data = bytearray(header)
    # forcedToAccept (bool)
    data.append(0)

    if protocol_version >= 898:
        # resourcePacks array length (VarUInt32 0)
        data.extend(encode_varuint32(0))
        # gameVersion (string)
        data.extend(encode_string(game_version or "*"))
        # experiments: count (uint32 LE 0)
        data.extend(struct.pack("<I", 0))
        # experimentsPreviouslyToggled (bool)
        data.append(0)
        # hasEditorPacks (bool)
        data.append(0)
    elif protocol_version >= 671:
        # behaviorPacks array length (VarUInt32 0)
        data.extend(encode_varuint32(0))
        # resourcePacks array length (VarUInt32 0)
        data.extend(encode_varuint32(0))
        # gameVersion (string)
        data.extend(encode_string(game_version or "*"))
        # experiments count (uint32 LE 0)
        data.extend(struct.pack("<I", 0))
        # experimentsPreviouslyToggled (bool)
        data.append(0)
        # hasEditorPacks (bool)
        data.append(0)
    else:
        # behaviorPacks count (uint16 LE 0)
        data.extend(struct.pack("<H", 0))
        # resourcePacks count (uint16 LE 0)
        data.extend(struct.pack("<H", 0))
        # gameVersion (string)
        data.extend(encode_string(game_version or "*"))
        # experiments count (uint32 LE 0)
        data.extend(struct.pack("<I", 0))
        # experimentsPreviouslyToggled (bool)
        data.append(0)

    return bytes(data)


def parse_resource_pack_client_response(
    payload: bytes,
    protocol_version: int = CURRENT_PROTOCOL_VERSION
) -> Optional[int]:
    """Parse ResourcePackClientResponsePacket (ID 8 / 0x08).

    Returns status:
    3 = HAVE_ALL_PACKS ('downloadingfinished')
    4 = COMPLETED ('resourcepackstackfinished')
    """
    try:
        packet_id, offset = decode_packet_header(payload, 0)
        if packet_id != ID_RESOURCE_PACK_CLIENT_RESPONSE:
            return None

        if offset >= len(payload):
            return None

        # Try v2168 varuint32 first
        try:
            status_val, new_offset = decode_varuint32(payload, offset)
            status = status_val + 1
            if status in (RESPONSE_STATUS_HAVE_ALL_PACKS, RESPONSE_STATUS_COMPLETED):
                return status
        except Exception:
            pass

        # Try byte read
        status_byte = payload[offset]
        if status_byte in (RESPONSE_STATUS_HAVE_ALL_PACKS, RESPONSE_STATUS_COMPLETED):
            return status_byte

        # Fallback string search
        if b"downloadingfinished" in payload:
            return RESPONSE_STATUS_HAVE_ALL_PACKS
        elif b"resourcepackstackfinished" in payload:
            return RESPONSE_STATUS_COMPLETED

        return None
    except Exception:
        return None


# BedrockTogether Reference Vector for StartGamePacket (v2168 / 1.26.45)
# Generates the temporary "LAN Proxy" void world so console clients can spawn and transition cleanly.
_START_GAME_V2168_HEX = (
    "0201020000000000000000000000000000803f0000803fffffffffffffffff"
    "00000000020000000000000000000000400000000000000000000000010108"
    "080100000000000000000002040000000000000000000100000007312e3137"
    "2e34300000000000000000000000000000000005776f726c64094c414e2050"
    "726f78792430303030303030302d303030302d303030302d303030302d3030"
    "30303030303030303030000001000000000000000000000000000a00000000"
    "0000000000154e7a4b213c8d6f395fb4e8d1c7029a0000000000000000"
)
_START_GAME_V2168_BYTES = binascii.unhexlify(_START_GAME_V2168_HEX)

# BedrockTogether Reference Vector for empty LevelChunkPacket (258 bytes)
_EMPTY_CHUNK_V2168_HEX = (
    "0000000000000082020a000000000000000000000000000000000000000000"
    "00000000000000000000000000000000000000000000000000000000000000"
    "00000000000000000000000000000000000000000000000000000000000000"
    "00000000000000000000000000000000000000000000000000000000000000"
    "00000000000000000000000000000000000000000000000000000000000000"
    "00000000000000000000000000000000000000000000000000000000000000"
    "00000000000000000000000000000000000000000000000000000000000000"
    "00000000000000000000000000000000000000000000000000000000000000"
    "00000000000000000000000000"
)
_EMPTY_CHUNK_V2168_BYTES = binascii.unhexlify(_EMPTY_CHUNK_V2168_HEX)


def build_start_game(protocol_version: int = CURRENT_PROTOCOL_VERSION) -> bytes:
    """Build StartGamePacket (ID 11 / 0x0B).
    
    Initializes the local temporary world session so the console client can
    progress through 'Génération du terrain...' and trigger the in-game transfer.
    """
    header = encode_packet_header(ID_START_GAME)
    return header + _START_GAME_V2168_BYTES


def build_level_chunk() -> bytes:
    """Build LevelChunkPacket (ID 58 / 0x3A).
    
    Sends an empty chunk to satisfy world initialization.
    """
    header = encode_packet_header(ID_LEVEL_CHUNK)
    return header + _EMPTY_CHUNK_V2168_BYTES


def build_player_spawn() -> bytes:
    """Build PlayStatusPacket(STATUS_PLAYER_SPAWN = 3).
    
    Signals the client that the player has spawned in the world,
    clearing the loading screen and enabling in-game packet processing.
    """
    return build_play_status(STATUS_PLAYER_SPAWN)


