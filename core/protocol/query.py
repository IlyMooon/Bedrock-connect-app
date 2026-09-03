"""Minecraft Bedrock server query and ping client."""

import html
import socket
import struct
import time
from typing import Optional, Dict, Any

from core.protocol.raknet import RAKNET_MAGIC, ID_UNCONNECTED_PING, ID_UNCONNECTED_PONG

MINECRAFT_COLORS = {
    "0": "#000000",
    "1": "#0000AA",
    "2": "#00AA00",
    "3": "#00AAAA",
    "4": "#AA0000",
    "5": "#AA00AA",
    "6": "#FFAA00",
    "7": "#AAAAAA",
    "8": "#555555",
    "9": "#5555FF",
    "a": "#55FF55",
    "b": "#55FFFF",
    "c": "#FF5555",
    "d": "#FF55FF",
    "e": "#FFFF55",
    "f": "#FFFFFF",
}


def minecraft_to_html(text: str) -> str:
    """Convert Minecraft formatting codes (§) to styled HTML."""
    if not text:
        return ""

    escaped = html.escape(text)
    parts = []
    current_color = None
    is_bold = False
    is_italic = False

    i = 0
    buffer = []

    def flush():
        if not buffer:
            return
        content = "".join(buffer)
        buffer.clear()
        styles = []
        if current_color:
            styles.append(f"color: {current_color};")
        if is_bold:
            styles.append("font-weight: bold;")
        if is_italic:
            styles.append("font-style: italic;")

        if styles:
            style_str = " ".join(styles)
            parts.append(f"<span style=\"{style_str}\">{content}</span>")
        else:
            parts.append(content)

    while i < len(escaped):
        if escaped[i] in ("§", "&") and i + 1 < len(escaped):
            code = escaped[i + 1].lower()
            if code in MINECRAFT_COLORS:
                flush()
                current_color = MINECRAFT_COLORS[code]
                i += 2
                continue
            elif code == "l":
                flush()
                is_bold = True
                i += 2
                continue
            elif code == "o":
                flush()
                is_italic = True
                i += 2
                continue
            elif code == "r":
                flush()
                current_color = None
                is_bold = False
                is_italic = False
                i += 2
                continue
        buffer.append(escaped[i])
        i += 1

    flush()
    return "".join(parts)


def clean_minecraft_text(text: str) -> str:
    """Strip Minecraft color codes (§0-§f, §l, §r, etc.)."""
    import re
    return re.sub(r"[§&][0-9a-fk-or]", "", text)


def ping_bedrock_server(host: str, port: int = 19132, timeout: float = 2.5) -> Dict[str, Any]:
    """Ping a remote Minecraft Bedrock server via RakNet Unconnected Ping.
    
    Returns a dictionary containing latency, online status, MOTD, and player count.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)

    client_time = int(time.time() * 1000)
    packet = struct.pack(">B Q 16s Q", ID_UNCONNECTED_PING, client_time, RAKNET_MAGIC, 12345678)

    start_time = time.time()
    try:
        sock.sendto(packet, (host, port))
        data, _ = sock.recvfrom(4096)
        latency_ms = int((time.time() - start_time) * 1000)

        if len(data) < 35 or data[0] != ID_UNCONNECTED_PONG:
            return {"online": False, "error": "Invalid response"}

        motd_len = struct.unpack(">H", data[33:35])[0]
        motd_str = data[35:35 + motd_len].decode("utf-8", errors="replace")

        # Parse MOTD components:
        # MCPE;ServerName;ProtocolVersion;VersionName;CurrentPlayers;MaxPlayers;ServerGUID;SubName;GameMode
        tokens = motd_str.split(";")

        server_name = tokens[1] if len(tokens) > 1 else host
        protocol_version = tokens[2] if len(tokens) > 2 else "Unknown"
        version_name = tokens[3] if len(tokens) > 3 else "Unknown"
        current_players = int(tokens[4]) if len(tokens) > 4 and tokens[4].isdigit() else 0
        max_players = int(tokens[5]) if len(tokens) > 5 and tokens[5].isdigit() else 0
        sub_name = tokens[7] if len(tokens) > 7 else ""
        game_mode = tokens[8] if len(tokens) > 8 else "Survival"

        return {
            "online": True,
            "host": host,
            "port": port,
            "latency_ms": latency_ms,
            "server_name": server_name,
            "clean_server_name": clean_minecraft_text(server_name),
            "html_server_name": minecraft_to_html(server_name),
            "protocol_version": protocol_version,
            "version_name": version_name,
            "current_players": current_players,
            "max_players": max_players,
            "sub_name": sub_name,
            "clean_sub_name": clean_minecraft_text(sub_name),
            "html_sub_name": minecraft_to_html(sub_name),
            "game_mode": game_mode,
            "raw_motd": motd_str
        }
    except socket.timeout:
        return {"online": False, "error": "Timeout (serveur injoignable)", "host": host, "port": port}
    except Exception as e:
        return {"online": False, "error": str(e), "host": host, "port": port}
    finally:
        sock.close()
