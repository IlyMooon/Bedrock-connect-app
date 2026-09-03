import os
import sys
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.protocol.varint import (
    encode_varuint32,
    decode_varuint32,
    encode_varint32,
    decode_varint32,
    encode_string,
    decode_string,
)
from core.protocol.raknet import (
    encode_uint24_le,
    decode_uint24_le,
    encode_address,
    decode_address,
    parse_open_connection_request_1,
    build_open_connection_reply_1,
    build_open_connection_reply_2,
    EncapsulatedPacket,
    build_datagram,
    parse_datagram,
    build_ack,
    parse_ack,
    build_unconnected_pong,
    parse_unconnected_pong,
    RELIABILITY_RELIABLE_ORDERED,
    RAKNET_MAGIC,
)
from core.protocol.bedrock import (
    ID_TRANSFER,
    encode_packet_header,
    decode_packet_header,
    build_transfer_packet,
    build_play_status,
    encode_batch,
    decode_batch,
    COMPRESSION_ZLIB,
    COMPRESSION_NONE,
)


class TestVarint(unittest.TestCase):
    def test_varuint32(self):
        cases = [0, 1, 127, 128, 255, 300, 16384, 2097151, 4294967295]
        for num in cases:
            encoded = encode_varuint32(num)
            val, offset = decode_varuint32(encoded, 0)
            self.assertEqual(val, num)
            self.assertEqual(offset, len(encoded))

    def test_varint32(self):
        cases = [0, -1, 1, -128, 127, -2147483648, 2147483647]
        for num in cases:
            encoded = encode_varint32(num)
            val, offset = decode_varint32(encoded, 0)
            self.assertEqual(val, num)
            self.assertEqual(offset, len(encoded))

    def test_string(self):
        test_str = "Hello Bedrock Connect! 🎮 §aMinecraft"
        encoded = encode_string(test_str)
        decoded, offset = decode_string(encoded, 0)
        self.assertEqual(decoded, test_str)
        self.assertEqual(offset, len(encoded))


class TestRakNet(unittest.TestCase):
    def test_uint24_le(self):
        cases = [0, 1, 255, 65535, 16777215]
        for num in cases:
            enc = encode_uint24_le(num)
            self.assertEqual(len(enc), 3)
            dec, offset = decode_uint24_le(enc, 0)
            self.assertEqual(dec, num)
            self.assertEqual(offset, 3)

    def test_address(self):
        ip = "192.168.1.50"
        port = 19132
        enc = encode_address(ip, port)
        (dec_ip, dec_port), offset = decode_address(enc, 0)
        self.assertEqual(dec_ip, ip)
        self.assertEqual(dec_port, port)
        self.assertEqual(offset, len(enc))

    def test_unconnected_pong(self):
        pong = build_unconnected_pong(123456, 99999999, "MCPE;Test Server;748;1.21.50;1;100;99999999;Sub;Survival")
        parsed = parse_unconnected_pong(pong)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["ping_time"], 123456)
        self.assertEqual(parsed["server_guid"], 99999999)
        self.assertIn("Test Server", parsed["motd"])

    def test_datagram_and_frame(self):
        payload = b"Hello Bedrock Frame"
        frame = EncapsulatedPacket(
            content=payload,
            reliability=RELIABILITY_RELIABLE_ORDERED,
            message_index=42,
            order_index=1,
            order_channel=0
        )
        datagram = build_datagram(sequence_number=10, frames=[frame])
        parsed = parse_datagram(datagram)
        self.assertIsNotNone(parsed)
        seq_num, frames = parsed
        self.assertEqual(seq_num, 10)
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].content, payload)
        self.assertEqual(frames[0].message_index, 42)
        self.assertEqual(frames[0].order_index, 1)

    def test_ack(self):
        seqs = [1, 2, 3, 5, 8, 9, 10]
        ack_pkt = build_ack(seqs)
        parsed_seqs = parse_ack(ack_pkt)
        self.assertEqual(sorted(parsed_seqs), sorted(seqs))


class TestBedrock(unittest.TestCase):
    def test_packet_header(self):
        header = encode_packet_header(ID_TRANSFER)
        pid, offset = decode_packet_header(header, 0)
        self.assertEqual(pid, ID_TRANSFER)

    def test_transfer_packet(self):
        target_ip = "play.mycustomserver.net"
        target_port = 19132
        pk = build_transfer_packet(target_ip, target_port)
        pid, offset = decode_packet_header(pk, 0)
        self.assertEqual(pid, ID_TRANSFER)
        decoded_ip, offset = decode_string(pk, offset)
        self.assertEqual(decoded_ip, target_ip)

    def test_batch_zlib(self):
        pk1 = build_play_status(0)
        pk2 = build_transfer_packet("192.168.1.100", 19132)
        batch = encode_batch([pk1, pk2], compression_algo=COMPRESSION_ZLIB)
        self.assertEqual(batch[0], 0xFE)
        self.assertEqual(batch[1], 0x00)  # Flate / Zlib marker

        decoded = decode_batch(batch)
        self.assertEqual(len(decoded), 2)
        self.assertEqual(decoded[0], pk1)
        self.assertEqual(decoded[1], pk2)

    def test_split_frame(self):
        # Test split frame serialization and deserialization
        content = b"X" * 1500
        frame = EncapsulatedPacket(
            content=content,
            reliability=RELIABILITY_RELIABLE_ORDERED,
            message_index=1,
            order_index=0,
            split=True,
            split_count=2,
            split_id=101,
            split_index=0
        )
        serialized = frame.serialize()
        deserialized, offset = EncapsulatedPacket.deserialize(serialized, 0)
        self.assertTrue(deserialized.split)
        self.assertEqual(deserialized.split_count, 2)
        self.assertEqual(deserialized.split_id, 101)
        self.assertEqual(deserialized.split_index, 0)
        self.assertEqual(deserialized.content, content)

    def test_resource_packs_packets(self):
        from core.protocol.bedrock import (
            ID_RESOURCE_PACKS_INFO,
            ID_RESOURCE_PACK_STACK,
            ID_RESOURCE_PACK_CLIENT_RESPONSE,
            RESPONSE_STATUS_HAVE_ALL_PACKS,
            RESPONSE_STATUS_COMPLETED,
            build_resource_packs_info,
            build_resource_pack_stack,
            parse_resource_pack_client_response
        )

        # Test build ResourcePacksInfo for protocol 2168
        info_pk = build_resource_packs_info(2168)
        pid, offset = decode_packet_header(info_pk, 0)
        self.assertEqual(pid, ID_RESOURCE_PACKS_INFO)

        # Test build ResourcePackStack for protocol 2168
        stack_pk = build_resource_pack_stack("1.26.45", 2168)
        pid, offset = decode_packet_header(stack_pk, 0)
        self.assertEqual(pid, ID_RESOURCE_PACK_STACK)

        # Test client response parsing (both string marker and status ordinal)
        dummy_resp_have_packs = bytearray(encode_packet_header(ID_RESOURCE_PACK_CLIENT_RESPONSE))
        dummy_resp_have_packs.extend(encode_varuint32(RESPONSE_STATUS_HAVE_ALL_PACKS - 1))
        dummy_resp_have_packs.extend(encode_string("downloadingfinished"))
        status = parse_resource_pack_client_response(bytes(dummy_resp_have_packs), 2168)
        self.assertEqual(status, RESPONSE_STATUS_HAVE_ALL_PACKS)

        dummy_resp_completed = bytearray(encode_packet_header(ID_RESOURCE_PACK_CLIENT_RESPONSE))
        dummy_resp_completed.extend(encode_varuint32(RESPONSE_STATUS_COMPLETED - 1))
        dummy_resp_completed.extend(encode_string("resourcepackstackfinished"))
        status = parse_resource_pack_client_response(bytes(dummy_resp_completed), 2168)
        self.assertEqual(status, RESPONSE_STATUS_COMPLETED)

    def test_start_game_and_world_packets(self):
        import struct
        from core.protocol.bedrock import (
            ID_START_GAME,
            ID_LEVEL_CHUNK,
            ID_PLAY_STATUS,
            STATUS_PLAYER_SPAWN,
            build_start_game,
            build_level_chunk,
            build_player_spawn,
        )

        sg_pk = build_start_game(2168)
        pid, _ = decode_packet_header(sg_pk, 0)
        self.assertEqual(pid, ID_START_GAME)
        self.assertIn(b"LAN Proxy", sg_pk)

        chunk_pk = build_level_chunk()
        pid, _ = decode_packet_header(chunk_pk, 0)
        self.assertEqual(pid, ID_LEVEL_CHUNK)
        self.assertEqual(len(chunk_pk), 262)  # 1 byte header + 3 bytes metadata + 258 bytes chunk data

        spawn_pk = build_player_spawn()
        pid, _ = decode_packet_header(spawn_pk, 0)
        self.assertEqual(pid, ID_PLAY_STATUS)
        status_val = struct.unpack(">i", spawn_pk[1:5])[0]
        self.assertEqual(status_val, STATUS_PLAYER_SPAWN)


if __name__ == "__main__":
    unittest.main()
