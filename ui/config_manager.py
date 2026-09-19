"""Configuration manager for saving and loading server profiles."""

import json
import os
import uuid
from typing import List, Dict, Any, Optional

DEFAULT_SERVERS = [
    {
        "id": "hive",
        "name": "The Hive Bedrock",
        "host": "geo.hivebedrock.network",
        "port": 19132,
        "sub_name": "Bedwars, Murder Mystery, SkyWars"
    },
    {
        "id": "galaxite",
        "name": "Galaxite",
        "host": "play.galaxite.net",
        "port": 19132,
        "sub_name": "Custom Mini-Games & Prisons"
    },
    {
        "id": "cubecraft",
        "name": "CubeCraft Games",
        "host": "play.cubecraft.net",
        "port": 19132,
        "sub_name": "EggWars & Skyblock"
    },
    {
        "id": "mineville",
        "name": "Mineville",
        "host": "play.inpvp.net",
        "port": 19132,
        "sub_name": "Survival, City & High School"
    },
    {
        "id": "custom",
        "name": "Mon Serveur Privé / Geyser",
        "host": "192.168.1.50",
        "port": 19132,
        "sub_name": "Survie entre amis"
    }
]


class ConfigManager:
    """Manages persistent application settings and saved server list."""

    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self.config_path = config_path
        else:
            app_dir = os.path.expanduser("~/.config/bedrock-directconnect")
            try:
                os.makedirs(app_dir, exist_ok=True)
                self.config_path = os.path.join(app_dir, "config.json")
            except Exception:
                self.config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")

        self.data: Dict[str, Any] = {
            "servers": DEFAULT_SERVERS,
            "favorites": [],
            "selected_server_id": "hive",
            "bind_port": 19132,
            "auto_ping": True,
            "bedrock_version": "1.26.51",
            "protocol_version": 2193,
        }
        self.load()

    def load(self):
        """Load configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        if "servers" in loaded and isinstance(loaded["servers"], list):
                            self.data["servers"] = loaded["servers"]
                        if "favorites" in loaded and isinstance(loaded["favorites"], list):
                            self.data["favorites"] = loaded["favorites"]
                        if "selected_server_id" in loaded:
                            self.data["selected_server_id"] = loaded["selected_server_id"]
                        if "bind_port" in loaded:
                            self.data["bind_port"] = loaded["bind_port"]
                        if "bedrock_version" in loaded:
                            # Auto-upgrade outdated 1.26.45 default to 1.26.51
                            bv = loaded["bedrock_version"]
                            self.data["bedrock_version"] = "1.26.51" if bv == "1.26.45" else bv
                        if "protocol_version" in loaded:
                            # Auto-upgrade outdated 2168 protocol to 2193
                            pv = loaded["protocol_version"]
                            self.data["protocol_version"] = 2193 if pv == 2168 else pv
                        if loaded.get("bedrock_version") == "1.26.45" or loaded.get("protocol_version") == 2168:
                            self.save()
            except Exception as e:
                print(f"Error loading config: {e}")

    def save(self):
        """Save current configuration to file."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_bedrock_version(self) -> str:
        return self.data.get("bedrock_version", "1.26.51")

    def get_protocol_version(self) -> int:
        return self.data.get("protocol_version", 2193)

    def set_bedrock_version(self, version_str: str, protocol_ver: int):
        self.data["bedrock_version"] = version_str
        self.data["protocol_version"] = protocol_ver
        self.save()

    def get_servers(self) -> List[Dict[str, Any]]:
        return self.data.get("servers", [])

    def get_selected_server(self) -> Optional[Dict[str, Any]]:
        sel_id = self.data.get("selected_server_id")
        for s in self.get_servers():
            if s.get("id") == sel_id:
                return s
        servers = self.get_servers()
        return servers[0] if servers else None

    def set_selected_server_id(self, server_id: str):
        self.data["selected_server_id"] = server_id
        self.save()

    def add_server(self, name: str, host: str, port: int = 19132, sub_name: str = "") -> Dict[str, Any]:
        server_id = str(uuid.uuid4())[:8]
        new_server = {
            "id": server_id,
            "name": name,
            "host": host,
            "port": port,
            "sub_name": sub_name
        }
        self.data["servers"].append(new_server)
        self.data["selected_server_id"] = server_id
        self.save()
        return new_server

    def update_server(self, server_id: str, name: str, host: str, port: int, sub_name: str):
        for s in self.data["servers"]:
            if s.get("id") == server_id:
                s["name"] = name
                s["host"] = host
                s["port"] = port
                s["sub_name"] = sub_name
                break
        self.save()

    def delete_server(self, server_id: str):
        self.data["servers"] = [s for s in self.data["servers"] if s.get("id") != server_id]
        if self.data["selected_server_id"] == server_id:
            servers = self.get_servers()
            self.data["selected_server_id"] = servers[0]["id"] if servers else None
        self.save()

    def get_favorites(self) -> List[Dict[str, Any]]:
        """Return list of favorite servers (max 5)."""
        return self.data.get("favorites", [])

    def add_favorite(self, host: str, port: int = 19132) -> bool:
        """Add server to favorites (limit 5). Returns True if added, False if limit reached or already exists."""
        favs = self.get_favorites()
        # Clean host
        clean_host = host.strip()
        if not clean_host:
            return False

        # Check if already exists
        for f in favs:
            if f.get("host", "").lower() == clean_host.lower() and f.get("port") == port:
                return False

        if len(favs) >= 5:
            return False

        favs.append({
            "id": str(uuid.uuid4())[:8],
            "host": clean_host,
            "port": port
        })
        self.data["favorites"] = favs
        self.save()
        return True

    def remove_favorite(self, host: str, port: int) -> bool:
        """Remove server from favorites."""
        favs = self.get_favorites()
        initial_len = len(favs)
        self.data["favorites"] = [
            f for f in favs if not (f.get("host", "").lower() == host.strip().lower() and f.get("port") == port)
        ]
        if len(self.data["favorites"]) != initial_len:
            self.save()
            return True
        return False

