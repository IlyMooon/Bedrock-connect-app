"""Bedrock Transfer Server engine.

Listens on UDP 19132, advertises LAN game to consoles, handles RakNet
handshake, and seamlessly transfers connecting players to the target
external server using native Bedrock TransferPacket redirection.
"""

import os
import shutil
import signal
import socket
import struct
import subprocess
import threading
import time
from typing import Dict, Tuple, Optional, Callable

from core.protocol.raknet import (
    ID_CONNECTED_PING,
    ID_UNCONNECTED_PING,
    ID_UNCONNECTED_PING_OPEN_CONNECTIONS,
    ID_OPEN_CONNECTION_REQUEST_1,
    ID_OPEN_CONNECTION_REQUEST_2,
    ID_CONNECTION_REQUEST,
    ID_NEW_INCOMING_CONNECTION,
    ID_DISCONNECTION_NOTIFICATION,
    ID_GAME_PACKET,
    BITFLAG_DATAGRAM,
    BITFLAG_ACK,
    EncapsulatedPacket,
    RELIABILITY_RELIABLE,
    RELIABILITY_RELIABLE_ORDERED,
    build_unconnected_pong,
    parse_open_connection_request_1,
    build_open_connection_reply_1,
    parse_open_connection_request_2,
    build_open_connection_reply_2,
    parse_connection_request,
    build_connection_request_accepted,
    parse_connected_ping,
    build_connected_pong,
    build_datagram,
    parse_datagram,
    build_ack,
)
from core.protocol.bedrock import (
    ID_LOGIN,
    ID_REQUEST_NETWORK_SETTINGS,
    ID_RESOURCE_PACKS_INFO,
    ID_RESOURCE_PACK_STACK,
    ID_RESOURCE_PACK_CLIENT_RESPONSE,
    ID_SET_LOCAL_PLAYER_AS_INITIALIZED,
    RESPONSE_STATUS_HAVE_ALL_PACKS,
    RESPONSE_STATUS_COMPLETED,
    COMPRESSION_ZLIB,
    COMPRESSION_NONE,
    STATUS_LOGIN_SUCCESS,
    STATUS_PLAYER_SPAWN,
    CURRENT_PROTOCOL_VERSION,
    CURRENT_VERSION_STRING,
    decode_packet_header,
    decode_batch,
    encode_batch,
    parse_request_network_settings,
    build_network_settings,
    parse_login,
    build_play_status,
    build_resource_packs_info,
    build_resource_pack_stack,
    parse_resource_pack_client_response,
    build_start_game,
    build_level_chunk,
    build_player_spawn,
    build_transfer_packet,
)
from core.protocol.query import ping_bedrock_server


class ClientSession:
    """State for an active client connection."""

    def __init__(self, address: Tuple[str, int], mtu: int = 1400):
        self.address = address
        self.mtu = mtu
        self.client_guid: int = 0
        self.server_seq_num: int = 0
        self.message_index: int = 0
        self.order_index: int = 0
        self.compression_negotiated = False
        self.compression_algo = COMPRESSION_ZLIB
        self.transferred = False
        self.player_name: str = "Joueur Console"
        self.last_active = time.time()
        self.protocol_version: int = CURRENT_PROTOCOL_VERSION

        # Split frame reassembly buffers
        self.split_packets: Dict[int, Dict[int, bytes]] = {}  # split_id -> {split_index: chunk}
        self.split_counts: Dict[int, int] = {}                # split_id -> split_count

    def next_seq_num(self) -> int:
        seq = self.server_seq_num
        self.server_seq_num = (self.server_seq_num + 1) & 0xFFFFFF
        return seq

    def next_message_index(self) -> int:
        idx = self.message_index
        self.message_index = (self.message_index + 1) & 0xFFFFFF
        return idx

    def next_order_index(self) -> int:
        idx = self.order_index
        self.order_index = (self.order_index + 1) & 0xFFFFFF
        return idx


class BedrockTransferServer:
    """High-performance UDP server that acts as a LAN redirector for Minecraft Bedrock."""

    def __init__(
        self,
        target_host: str,
        target_port: int = 19132,
        server_name: str = "Bedrock DirectConnect",
        sub_name: str = "§aCliquez pour vous connecter",
        bind_ip: str = "0.0.0.0",
        bind_port: int = 19132,
        protocol_version: int = CURRENT_PROTOCOL_VERSION,
        version_string: str = CURRENT_VERSION_STRING,
        log_callback: Optional[Callable[[str, str], None]] = None,
        player_callback: Optional[Callable[[str, Tuple[str, int]], None]] = None,
        transfer_callback: Optional[Callable[[str, str, int], None]] = None,
    ):
        self.target_host = target_host
        self.target_port = target_port
        self.server_name = server_name
        self.sub_name = sub_name
        self.bind_ip = bind_ip
        self.bind_port = bind_port

        self.log_callback = log_callback
        self.player_callback = player_callback
        self.transfer_callback = transfer_callback

        self.server_guid = 1234567890123456789
        self.protocol_version = protocol_version
        self.version_string = version_string

        self.jar_path = os.path.join(os.path.dirname(__file__), "BedrockDirectEngine.jar")
        self.use_java_engine = os.path.exists(self.jar_path) and bool(shutil.which("java"))
        self.java_proc: Optional[subprocess.Popen] = None
        self.broadcast_sock: Optional[socket.socket] = None
        self.cloned_motd: Optional[str] = None

        self.sock: Optional[socket.socket] = None
        self.running = False
        self.sessions: Dict[Tuple[str, int], ClientSession] = {}
        self.lock = threading.Lock()

        self._listen_thread: Optional[threading.Thread] = None
        self._broadcast_thread: Optional[threading.Thread] = None

    def log(self, message: str, level: str = "INFO"):
        """Send message to logging callback."""
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(f"[{level}] {message}")

    def update_target_motd(self) -> Optional[dict]:
        """Query the remote target server to clone its real MOTD for the local LAN server."""
        try:
            res = ping_bedrock_server(self.target_host, self.target_port, timeout=1.8)
            if res.get("online") and res.get("raw_motd"):
                self.cloned_motd = res["raw_motd"]
                if res.get("server_name"):
                    self.server_name = res["server_name"]
                if res.get("sub_name"):
                    self.sub_name = res["sub_name"]
                if res.get("protocol_version") and str(res["protocol_version"]).isdigit():
                    self.protocol_version = int(res["protocol_version"])
                if res.get("version_name"):
                    self.version_string = str(res["version_name"])
                self.log(f"🎯 MOTD du serveur cible cloné : {res.get('clean_server_name')}", "SUCCESS")
                return res
        except Exception as e:
            self.log(f"Impossible de cloner le MOTD cible ({e}), utilisation du MOTD configuré.", "DEBUG")
        return None

    def get_motd(self) -> str:
        """Format Bedrock MOTD string for LAN game display.
        
        If a cloned MOTD is available from the target server, returns the real
        server MOTD with local bind port so consoles see the real server identity.
        """
        if self.cloned_motd:
            tokens = self.cloned_motd.split(";")
            if len(tokens) >= 10:
                # Direct LAN connection to our local bind port
                if len(tokens) > 10:
                    tokens[10] = str(self.bind_port)
                if len(tokens) > 11:
                    tokens[11] = str(self.bind_port)
                return ";".join(tokens)
            return self.cloned_motd

        clean_name = f"§e✦ {self.server_name}"
        sub = f"§a{self.sub_name} §7[{self.target_host}:{self.target_port}]"
        return f"MCPE;{clean_name};{self.protocol_version};{self.version_string};1;100;{self.server_guid};{sub};Survival;1;{self.bind_port};{self.bind_port};"

    def _ensure_port_available(self, port: int):
        """Check if UDP port is occupied by another process and free it automatically."""
        current_pid = os.getpid()
        try:
            res = subprocess.run(["lsof", "-t", f"-iUDP:{port}"], capture_output=True, text=True)
            pids = [int(p.strip()) for p in res.stdout.strip().split() if p.strip() and int(p.strip()) != current_pid]
            for pid in pids:
                self.log(f"⚠️ Port UDP {port} occupé par un processus (PID {pid}). Libération automatique...", "WARNING")
                try:
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(0.15)
                    os.kill(pid, signal.SIGKILL)
                except Exception:
                    pass
                self.log(f"✅ Port UDP {port} libéré avec succès.", "SUCCESS")
        except Exception as e:
            self.log(f"Vérification du port UDP {port} : {e}", "DEBUG")

    def start(self):
        """Start the Bedrock server and broadcast threads."""
        if self.running:
            return

        self._ensure_port_available(self.bind_port)
        self.running = True

        # Fetch and clone target server MOTD so local broadcast replicates it exactly
        self.update_target_motd()

        # Resolve destination host
        dest_ip = self.target_host
        try:
            resolved = socket.gethostbyname(self.target_host)
            if resolved:
                dest_ip = resolved
        except Exception:
            dest_ip = self.target_host

        if self.use_java_engine:
            self.log("Initialisation du moteur officiel Bedrock (Support monde vide 1.26.51)...", "INFO")
            cmd = [
                "java",
                f"-Dbedrock.target_host={dest_ip}",
                f"-Dbedrock.target_port={self.target_port}",
                "-jar",
                self.jar_path
            ]
            try:
                self.java_proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                self._listen_thread = threading.Thread(
                    target=self._read_java_loop,
                    daemon=True,
                    name="JavaEngineReader"
                )
                self._listen_thread.start()
            except Exception as e:
                self.log(f"Erreur lancement moteur Java : {e}. Bascule sur moteur Python.", "WARNING")
                self.use_java_engine = False

        if not self.use_java_engine:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            try:
                self.sock.bind((self.bind_ip, self.bind_port))
            except Exception as e:
                self.log(f"Impossible de démarrer le serveur sur le port UDP {self.bind_port} : {e}", "ERROR")
                raise

            self.log(f"Serveur de redirection actif sur UDP {self.bind_port}", "SUCCESS")
            self.log(f"Serveur cible configuré : {dest_ip}:{self.target_port}", "INFO")

            self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True, name="TransferServerListener")
            self._listen_thread.start()

        # Start LAN discovery broadcaster
        try:
            self.broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        except Exception:
            self.broadcast_sock = None

        self._broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True, name="TransferServerBroadcaster")
        self._broadcast_thread.start()

    def _read_java_loop(self):
        """Read and parse stdout from BedrockDirectEngine."""
        if not self.java_proc or not self.java_proc.stdout:
            return

        dest_ip = self.target_host
        try:
            resolved = socket.gethostbyname(self.target_host)
            if resolved:
                dest_ip = resolved
        except Exception:
            dest_ip = self.target_host

        while self.running and self.java_proc and self.java_proc.poll() is None:
            line = self.java_proc.stdout.readline()
            if not line:
                break
            line_str = line.strip()
            if not line_str:
                continue

            if "Server is now running" in line_str:
                self.log(f"🚀 Moteur officiel Bedrock actif sur UDP {self.bind_port} (Monde vide & Redirection prêts)", "SUCCESS")
                self.log(f"Serveur cible configuré : {dest_ip}:{self.target_port}", "INFO")
            elif "[DIRECT_TRANSFER]" in line_str:
                parts = line_str.split("Auto-transferring player ")
                pname = parts[1].split(" to ")[0] if len(parts) > 1 else "Joueur Console"
                self.log(f"🎮 Joueur {pname} apparu dans le monde vide ! Redirection automatique en cours...", "INFO")
                if self.player_callback:
                    self.player_callback(pname, (dest_ip, self.target_port))
            elif "Transferred player" in line_str:
                parts = line_str.split("Transferred player ")
                pname = parts[1].split(" to ")[0] if len(parts) > 1 else "Joueur Console"
                self.log(f"✅ Transfert réussi ! {pname} est redirigé en direct vers {dest_ip}:{self.target_port}", "SUCCESS")
                self.log("🎉 La console communique maintenant en standalone. Vous pouvez arrêter l'application sans couper la connexion !", "SUCCESS")
                if self.transfer_callback:
                    self.transfer_callback(pname, dest_ip, self.target_port)
            elif "Player disconnected" in line_str:
                self.log("Joueur console déconnecté du sas local (transfert achevé).", "DEBUG")
            elif "[ERROR]" in line_str:
                self.log(f"Moteur : {line_str}", "WARNING")
            else:
                self.log(f"Moteur : {line_str}", "DEBUG")

    def stop(self):
        """Stop the server and broadcast threads."""
        if not self.running:
            return

        self.running = False

        if self.broadcast_sock:
            try:
                self.broadcast_sock.close()
            except Exception:
                pass
            self.broadcast_sock = None

        if self.java_proc:
            try:
                self.java_proc.terminate()
                self.java_proc.wait(timeout=1.5)
            except Exception:
                try:
                    self.java_proc.kill()
                except Exception:
                    pass
            self.java_proc = None

        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

        self.log("Serveur de redirection arrêté.", "INFO")

    def _broadcast_loop(self):
        """Periodically broadcast LAN ping so consoles immediately discover the game."""
        subnet_bcast = "255.255.255.255"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            parts = local_ip.split(".")
            if len(parts) == 4:
                subnet_bcast = f"{parts[0]}.{parts[1]}.{parts[2]}.255"
        except Exception:
            pass

        tick = 0
        while self.running:
            tick += 1
            if tick % 15 == 0:
                # Refresh target MOTD periodically in background
                self.update_target_motd()

            try:
                pong_data = build_unconnected_pong(
                    int(time.time() * 1000),
                    self.server_guid,
                    self.get_motd()
                )
                if self.broadcast_sock:
                    self.broadcast_sock.sendto(pong_data, ("255.255.255.255", self.bind_port))
                    if subnet_bcast != "255.255.255.255":
                        self.broadcast_sock.sendto(pong_data, (subnet_bcast, self.bind_port))
            except Exception:
                pass
            time.sleep(1.0)

    def _listen_loop(self):
        """Main UDP packet receiver and dispatcher."""
        while self.running and self.sock:
            try:
                data, addr = self.sock.recvfrom(4096)
                if not data:
                    continue
                self._handle_packet(data, addr)
            except socket.error:
                break
            except Exception as e:
                self.log(f"Erreur réception paquet : {e}", "DEBUG")

    def _get_or_create_session(self, addr: Tuple[str, int]) -> ClientSession:
        with self.lock:
            if addr not in self.sessions:
                self.sessions[addr] = ClientSession(addr)
            session = self.sessions[addr]
            session.last_active = time.time()
            return session

    def _send_datagram(self, session: ClientSession, frames: list):
        """Send encapsulated frames inside a Datagram."""
        if not self.sock:
            return
        seq_num = session.next_seq_num()
        datagram = build_datagram(seq_num, frames)
        self.sock.sendto(datagram, session.address)

    def _handle_packet(self, data: bytes, addr: Tuple[str, int]):
        """Handle incoming UDP packet from client."""
        pid = data[0]

        # 1. Unconnected Ping (0x01 / 0x02)
        if pid in (ID_UNCONNECTED_PING, ID_UNCONNECTED_PING_OPEN_CONNECTIONS):
            if len(data) >= 9:
                ping_time = struct.unpack(">Q", data[1:9])[0]
            else:
                ping_time = int(time.time() * 1000)

            pong = build_unconnected_pong(ping_time, self.server_guid, self.get_motd())
            self.sock.sendto(pong, addr)
            return

        # 2. Open Connection Request 1 (0x05)
        if pid == ID_OPEN_CONNECTION_REQUEST_1:
            req = parse_open_connection_request_1(data)
            if req:
                session = self._get_or_create_session(addr)
                session.mtu = req["mtu"]
                reply = build_open_connection_reply_1(self.server_guid, session.mtu)
                self.sock.sendto(reply, addr)
                self.log(f"Connexion console détectée depuis {addr[0]}:{addr[1]} (MTU: {session.mtu})", "INFO")
            return

        # 3. Open Connection Request 2 (0x07)
        if pid == ID_OPEN_CONNECTION_REQUEST_2:
            req = parse_open_connection_request_2(data)
            if req:
                session = self._get_or_create_session(addr)
                session.client_guid = req["client_guid"]
                session.mtu = req["mtu"]
                reply = build_open_connection_reply_2(self.server_guid, addr[0], addr[1], session.mtu)
                self.sock.sendto(reply, addr)
                self.log(f"Négociation RakNet étape 2 validée pour {addr[0]}", "DEBUG")
            return

        # 4. ACK Packet (0xC0)
        if (pid & (BITFLAG_ACK | BITFLAG_DATAGRAM)) == (BITFLAG_ACK | BITFLAG_DATAGRAM):
            # Client acknowledged packets
            return

        # 5. Connected Datagrams (0x80 to 0x8F)
        if (pid & BITFLAG_DATAGRAM) != 0:
            parsed = parse_datagram(data)
            if not parsed:
                return

            seq_num, frames = parsed
            session = self._get_or_create_session(addr)

            # Immediately send ACK to console so it knows we received this datagram
            ack_pkt = build_ack([seq_num])
            self.sock.sendto(ack_pkt, addr)

            # Process encapsulated frames
            for frame in frames:
                self._handle_frame(frame, session)

    def _handle_frame(self, frame: EncapsulatedPacket, session: ClientSession):
        """Process an individual encapsulated RakNet frame, handling split fragments."""
        # Check if frame is a split fragment (critical for large packets like LoginPacket)
        if frame.split:
            if frame.split_id not in session.split_packets:
                session.split_packets[frame.split_id] = {}
                session.split_counts[frame.split_id] = frame.split_count

            session.split_packets[frame.split_id][frame.split_index] = frame.content

            # Check if all split parts have arrived
            if len(session.split_packets[frame.split_id]) < session.split_counts[frame.split_id]:
                # Waiting for more fragments
                return

            # All fragments collected: reassemble in order
            reassembled = bytearray()
            count = session.split_counts[frame.split_id]
            for idx in range(count):
                reassembled.extend(session.split_packets[frame.split_id].get(idx, b""))
            session.split_packets.pop(frame.split_id, None)
            session.split_counts.pop(frame.split_id, None)
            payload = bytes(reassembled)
        else:
            payload = frame.content

        if not payload:
            return

        frame_pid = payload[0]

        # 1. Connection Request (0x09)
        if frame_pid == ID_CONNECTION_REQUEST:
            req = parse_connection_request(payload)
            if req:
                pong_payload = build_connection_request_accepted(
                    session.address[0],
                    session.address[1],
                    req["ping_time"],
                    int(time.time() * 1000)
                )
                resp_frame = EncapsulatedPacket(
                    content=pong_payload,
                    reliability=RELIABILITY_RELIABLE_ORDERED,
                    message_index=session.next_message_index(),
                    order_index=session.next_order_index()
                )
                self._send_datagram(session, [resp_frame])
                self.log("Demande de session console acceptée (0x10 envoyé)", "DEBUG")
            return

        # 2. New Incoming Connection (0x13)
        if frame_pid == ID_NEW_INCOMING_CONNECTION:
            self.log(f"Session RakNet connectée avec succès avec {session.address[0]}", "INFO")
            return

        # 3. Connected Ping (0x00)
        if frame_pid == ID_CONNECTED_PING:
            ping_time = parse_connected_ping(payload)
            if ping_time is not None:
                pong_payload = build_connected_pong(ping_time)
                resp_frame = EncapsulatedPacket(
                    content=pong_payload,
                    reliability=RELIABILITY_RELIABLE_ORDERED,
                    message_index=session.next_message_index(),
                    order_index=session.next_order_index()
                )
                self._send_datagram(session, [resp_frame])
            return

        # 4. Disconnection Notification (0x15)
        if frame_pid == ID_DISCONNECTION_NOTIFICATION:
            self.log(f"Déconnexion du client {session.address[0]}", "INFO")
            with self.lock:
                self.sessions.pop(session.address, None)
            return

        # 5. Game Packet Batch (0xFE)
        if frame_pid == ID_GAME_PACKET:
            self._handle_game_batch(payload, session)

    def _handle_game_batch(self, batch_data: bytes, session: ClientSession):
        """Handle Minecraft Bedrock game packet batch."""
        game_packets = decode_batch(batch_data)

        for pk in game_packets:
            if not pk:
                continue

            try:
                packet_id, offset = decode_packet_header(pk, 0)
            except Exception:
                continue

            # Case A: RequestNetworkSettings (ID 193)
            if packet_id == ID_REQUEST_NETWORK_SETTINGS:
                info = parse_request_network_settings(pk)
                if info:
                    proto = info["protocol_version"]
                    session.protocol_version = proto
                    self.log(f"Paramètres réseau demandés par le client (Protocole v{proto})", "DEBUG")

                # Build NetworkSettingsPacket with Zlib/Flate compression and threshold = 1
                net_settings_pk = build_network_settings(
                    compression_threshold=1,
                    compression_algorithm=COMPRESSION_ZLIB
                )

                # Send response batch (raw batch before compression active)
                batch_resp = encode_batch([net_settings_pk], compression_algo=-1)
                resp_frame = EncapsulatedPacket(
                    content=batch_resp,
                    reliability=RELIABILITY_RELIABLE_ORDERED,
                    message_index=session.next_message_index(),
                    order_index=session.next_order_index()
                )
                self._send_datagram(session, [resp_frame])
                session.compression_negotiated = True
                self.log("Paramètres réseau envoyés au client (Compression Zlib/Flate activée)", "DEBUG")

            # Case B: LoginPacket (ID 1)
            elif packet_id == ID_LOGIN:
                login_info = parse_login(pk)
                player_name = login_info["display_name"] if login_info else "Joueur Console"
                session.player_name = player_name

                self.log(f"🎮 Joueur console connecté : {player_name} ({session.address[0]})", "SUCCESS")
                if self.player_callback:
                    self.player_callback(player_name, session.address)

                # Send PlayStatus(LOGIN_SUCCESS) and ResourcePacksInfoPacket
                # (Essential: client waits for ResourcePacksInfo before leaving 'Chargement des packs de ressources')
                play_status_pk = build_play_status(STATUS_LOGIN_SUCCESS)
                packs_info_pk = build_resource_packs_info(session.protocol_version)

                # Send login handshake batch
                login_batch = encode_batch(
                    [play_status_pk, packs_info_pk],
                    compression_algo=COMPRESSION_ZLIB if session.compression_negotiated else COMPRESSION_NONE
                )
                resp_frame = EncapsulatedPacket(
                    content=login_batch,
                    reliability=RELIABILITY_RELIABLE_ORDERED,
                    message_index=session.next_message_index(),
                    order_index=session.next_order_index()
                )
                self._send_datagram(session, [resp_frame])
                self.log("📦 Envoi de ResourcePacksInfo (dégagement de l'écran de chargement des packs)...", "DEBUG")

            # Case C: ResourcePackClientResponse (ID 8)
            elif packet_id == ID_RESOURCE_PACK_CLIENT_RESPONSE:
                status = parse_resource_pack_client_response(pk, session.protocol_version)
                player_name = session.player_name or "Joueur Console"

                # Resolve hostname to IPv4 address for maximum console compatibility
                dest_host = self.target_host
                try:
                    resolved_ip = socket.gethostbyname(self.target_host)
                    if resolved_ip:
                        dest_host = resolved_ip
                        if dest_host != self.target_host:
                            self.log(f"Résolution DNS : {self.target_host} -> {dest_host}", "DEBUG")
                except Exception:
                    dest_host = self.target_host

                transfer_pk = build_transfer_packet(dest_host, self.target_port, reload_world=False)

                if status == RESPONSE_STATUS_HAVE_ALL_PACKS:
                    # Client completed checking packs -> send StackPacket and TransferPacket
                    stack_pk = build_resource_pack_stack(self.version_string, session.protocol_version)
                    batch_pkts = [stack_pk, transfer_pk]
                    self.log(f"📦 Packs validés par la console. Redirection propre vers {dest_host}:{self.target_port}...", "INFO")
                else:
                    # COMPLETED or other status -> send TransferPacket directly
                    batch_pkts = [transfer_pk]
                    self.log(f"🚀 Négociation terminée. Redirection propre vers {dest_host}:{self.target_port}...", "INFO")

                transfer_batch = encode_batch(
                    batch_pkts,
                    compression_algo=COMPRESSION_ZLIB if session.compression_negotiated else COMPRESSION_NONE
                )
                resp_frame = EncapsulatedPacket(
                    content=transfer_batch,
                    reliability=RELIABILITY_RELIABLE_ORDERED,
                    message_index=session.next_message_index(),
                    order_index=session.next_order_index()
                )
                self._send_datagram(session, [resp_frame])
                session.transferred = True

                self.log(f"✅ Transfert réussi ! {player_name} est redirigé en direct vers {dest_host}:{self.target_port}", "SUCCESS")
                self.log("🎉 La console communique maintenant en standalone avec le serveur externe. Vous pouvez arrêter l'application sans couper la connexion !", "SUCCESS")

                if self.transfer_callback:
                    self.transfer_callback(player_name, dest_host, self.target_port)

            # Case D: SetLocalPlayerAsInitialized (ID 113)
            elif packet_id == ID_SET_LOCAL_PLAYER_AS_INITIALIZED:
                dest_host = self.target_host
                try:
                    resolved_ip = socket.gethostbyname(self.target_host)
                    if resolved_ip:
                        dest_host = resolved_ip
                except Exception:
                    dest_host = self.target_host

                transfer_pk = build_transfer_packet(dest_host, self.target_port, reload_world=False)
                transfer_batch = encode_batch(
                    [transfer_pk],
                    compression_algo=COMPRESSION_ZLIB if session.compression_negotiated else COMPRESSION_NONE
                )
                resp_frame = EncapsulatedPacket(
                    content=transfer_batch,
                    reliability=RELIABILITY_RELIABLE_ORDERED,
                    message_index=session.next_message_index(),
                    order_index=session.next_order_index()
                )
                self._send_datagram(session, [resp_frame])
                session.transferred = True
