# Bedrock DirectConnect 🎮

Standalone LAN redirection gateway enabling Minecraft Bedrock console and mobile players to join any external server.

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt5-41CD52?style=flat&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![Bedrock](https://img.shields.io/badge/Bedrock-v1.26.51%20(Protocol%202193)-blue?style=flat&logo=minecraft&logoColor=white)](https://minecraft.net/)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey?style=flat)](#requirements--prerequisites)
[![License](https://img.shields.io/badge/License-TODO-orange?style=flat)](#license)

---

## Short Description

**Bedrock DirectConnect** is a desktop application (with a PyQt5 graphic user interface and a headless CLI mode) that acts as a local LAN gateway for Minecraft Bedrock Edition.

### The Problem It Solves
Console platforms (PlayStation 4/5, Xbox One / Series X|S, Nintendo Switch) and mobile devices (iOS, Android) restrict players from directly inputting custom server IPs and ports. Existing proxy solutions require running a continuous relay that routes every game packet through a local computer, consuming bandwidth and system resources throughout the play session.

### How It Works
Bedrock DirectConnect broadcasts RakNet discovery ping packets on your local network (`UDP 19132`). The game displays this local broadcast under the **Friends > LAN Games** menu on consoles. When a player connects:
1. The application negotiates the initial RakNet connection and handles Bedrock packet batching.
2. It transitions the console through a minimal temporary world session (`StartGamePacket`, `LevelChunkPacket`, and `PlayStatus(PLAYER_SPAWN)`).
3. It dispatches Minecraft's official `TransferPacket` (Packet ID 85 / `0x55`) containing the destination server address.
4. The console's Minecraft client connects **directly** to the destination server over the Internet.

Once transferred, the computer no longer relays game traffic. You can stop or close the application immediately without disconnecting the player.

### Target Audience
Console and mobile players who want to join external Minecraft Bedrock servers or Java servers running [GeyserMC](https://geysermc.org/), without keeping a dedicated relay proxy active on their computer.

---

## Features

- **Standalone Direct Transfer**: Uses native Bedrock `TransferPacket` (`ID 85`). Once the transfer completes, the console communicates directly with the target server. The desktop app can be closed immediately.
- **Dual Engine Architecture**: Embedded high-performance Java engine (`BedrockDirectEngine.jar` supporting Bedrock protocol version 2193 / Minecraft 1.26.51) with automatic fallback to a pure Python protocol implementation.
- **Instant LAN Game Broadcast**: Sends automated RakNet discovery pings across `255.255.255.255:19132` and local subnet broadcast addresses.
- **Live Target MOTD & Query Cloning**: Automatically queries the target server to clone its real MOTD (including Minecraft `§` color formatting), player counts, and protocol version.
- **Curated Partner Server Presets**: Built-in 1-click presets for *The Hive*, *CubeCraft Games*, *Galaxite*, *Lifeboat Network*, and *Mineville* with input protection.
- **Favorite Servers Manager**: Save up to 5 custom server profiles (IP and UDP port) with background ping checks and persistent storage.
- **Modern Mobile-Inspired GUI**: Responsive dark theme built with PyQt5, featuring an iOS-style segmented navigation slider, card layouts, and status badges.
- **Headless CLI Mode**: Command-line flag (`--cli`) for running on headless servers, Linux boxes, or a Raspberry Pi.
- **Integrated Console Guides**: In-app instructions and troubleshooting steps for PlayStation, Xbox, Nintendo Switch, and iOS/Android.
- **Automatic Port Conflict Resolution**: Checks for conflicting processes occupying UDP port 19132 (using `lsof`) and frees the port before binding.

---

## Screenshots / Demo

<!-- TODO: Add actual screenshots or demo GIF here -->
> *Screenshots and demo recordings will be added in a future update.*

---

## Requirements / Prerequisites

### Operating System & Environment
- **OS**: macOS, Linux, or Windows.
- **Python**: Python 3.8 or higher (tested up to Python 3.14).
- **Java (Optional, Recommended)**: Java 8+ / OpenJDK JRE in your system `PATH`. When present, `BedrockDirectEngine.jar` is used; if unavailable, the app falls back to the native Python engine.

### Network Requirements
- Host computer and gaming console/mobile device must be connected to the **same local network / Wi-Fi router**.
- **AP Isolation** (Client Isolation) must be **disabled** in router settings.
- Inbound traffic on **UDP port 19132** must be allowed by your host computer's firewall.

### Accounts & Subscriptions
- A free **Microsoft Account** signed in to Minecraft Bedrock Edition.
- Platform online multiplayer subscriptions where required by the console vendor (PlayStation Plus, Xbox Game Pass Core, Nintendo Switch Online).

---

## Installation

Clone the repository and install the dependencies in a terminal:

```bash
# Clone repository
git clone https://github.com/IlyMooon/Bedrock-connect.git
cd Bedrock-connect

# (Optional) Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
python3 -m pip install -r requirements.txt
```

---

## Configuration

Bedrock DirectConnect stores user preferences and saved server favorites in JSON format:

- **Configuration File Path**: `~/.config/bedrock-directconnect/config.json` (falls back to `./config.json` if user directory is inaccessible).

### Example Configuration (`config.json`)

```json
{
  "servers": [
    {
      "id": "hive",
      "name": "The Hive Bedrock",
      "host": "geo.hivebedrock.network",
      "port": 19132,
      "sub_name": "Bedwars, Murder Mystery, SkyWars"
    }
  ],
  "favorites": [
    {
      "host": "play.myserver.net",
      "port": 19132
    }
  ],
  "selected_server_id": "hive",
  "bind_port": 19132,
  "auto_ping": true,
  "bedrock_version": "1.26.51",
  "protocol_version": 2193
}
```

### Configuration Options

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `servers` | `list[object]` | *(Default presets)* | List of default partner/preset servers. |
| `favorites` | `list[object]` | `[]` | User-saved custom servers (maximum 5). |
| `selected_server_id` | `string` | `"hive"` | Identifier of the currently selected preset server. |
| `bind_port` | `integer` | `19132` | Local UDP port used for LAN discovery and listener. |
| `auto_ping` | `boolean` | `true` | Enables automatic query and MOTD polling. |
| `bedrock_version` | `string` | `"1.26.51"` | Minecraft Bedrock client version string. |
| `protocol_version` | `integer` | `2193` | Bedrock network protocol version number. |

---

## How to Run

### Development & GUI Mode (Default)
To launch the PyQt5 graphical interface:

```bash
python3 main.py
```

### Production / Headless CLI Mode
To run without a graphical interface (e.g., on a server or terminal):

```bash
# Run with default settings (The Hive)
python3 main.py --cli

# Run targeting a custom server
python3 main.py --cli --host play.myserver.net --port 19132 --name "My Bedrock Server" --sub "Survival World"
```

#### CLI Command-Line Arguments

| Flag | Argument | Default | Description |
| :--- | :--- | :--- | :--- |
| `--cli` | None | `False` | Run in headless command-line mode without GUI. |
| `--host` | `HOST` | `geo.hivebedrock.network` | Target server IP address or domain name. |
| `--port` | `PORT` | `19132` | Target server UDP port. |
| `--name` | `NAME` | `Bedrock DirectConnect` | Display name shown on the console LAN menu. |
| `--sub` | `SUB` | `Cliquez pour rejoindre` | Subtitle text displayed in the LAN MOTD. |

### Running the Test Suite
The repository includes unit tests for protocol serialization and a live ping integration test:

```bash
# Run protocol unit tests
python3 -m unittest discover tests

# Run live query ping test against Bedrock servers
python3 tests/test_query.py
```

---

## Usage

### 1. Connecting via GUI Mode
1. Launch the application:
   ```bash
   python3 main.py
   ```
2. Select a partner server from the list, or type a custom IP address and UDP port in the **Connexion** card.
3. *(Optional)* Click **⭐ + Favori** to save your custom server for future sessions.
4. Click **▶ DÉMARRER**. The status badge switches to **● ACTIF**.
5. Switch to your console or mobile device:
   - Launch **Minecraft Bedrock Edition**.
   - Navigate to **Play** > **Friends** tab.
   - Scroll down to the **LAN Games** section.
   - Click the server entry (e.g. *Bedrock DirectConnect*).
6. The console will connect, display "Generating world", and receive the transfer packet.
7. Once your console connects to the external server, **you can close the desktop application**.

### 2. Platform Connection Summary

| Platform | Instructions |
| :--- | :--- |
| **PlayStation (PS4 / PS5)** | Connect to same Wi-Fi > Minecraft > **Play** > **Friends** > **LAN Games** > Click server. |
| **Xbox One / Series X\|S** | Connect to same network > Minecraft > **Play** > **Friends** > **LAN Games** > Select server. |
| **Nintendo Switch** | Connect to same Wi-Fi > Ensure Microsoft Account is signed in > **Play** > **Friends** > **LAN Games**. |
| **iOS / Android** | Connect to local Wi-Fi > Minecraft > **Play** > **Friends** > **LAN Games**. |

---

## Project Structure

```
Bedrock-connect/
├── core/
│   ├── protocol/
│   │   ├── __init__.py           # Protocol package initialization
│   │   ├── bedrock.py            # Bedrock packet framing, batch encoding/decoding, and TransferPacket builder
│   │   ├── query.py              # Server query/ping client and Minecraft formatting code (§) parser
│   │   ├── raknet.py             # RakNet protocol implementation (pings, handshakes, datagrams, ACKs)
│   │   └── varint.py             # LEB128 VarInt and VarUInt codec
│   └── server/
│       ├── __init__.py           # Server package initialization
│       ├── BedrockDirectEngine.jar # Embedded Java engine supporting Protocol 2193 / Minecraft 1.26.51
│       └── transfer_server.py    # UDP transfer server, LAN broadcaster, and engine supervisor
├── players/                      # Persistent player profile storage generated by the transfer engine
├── tests/
│   ├── test_protocol.py          # Unit tests for VarInt, RakNet, and Bedrock packet framing
│   └── test_query.py             # Live ping test script for remote Bedrock servers
├── ui/
│   ├── __init__.py               # UI package initialization
│   ├── components.py             # Reusable UI widgets (cards, MOTD displays, iOS segmented slider)
│   ├── config_manager.py         # JSON configuration and favorite profile storage manager
│   ├── guide_dialog.py           # Modal dialog with console-specific connection instructions
│   ├── infos_views.py            # Help Center views: console guides, troubleshooting, and about pages
│   ├── main_window.py            # Main PyQt5 application window and signal dispatcher
│   └── styles.py                 # QSS dark theme stylesheet definitions
├── CHANGES.md                    # Technical documentation on temporary world transition & protocol 2193
├── main.py                       # Application entry point supporting GUI and CLI modes
├── main.spec                     # PyInstaller build configuration specification
├── requirements.txt              # Python dependency manifest (PyQt5)
└── README.md                     # Project documentation
```

---

## Build / Deploy

You can bundle Bedrock DirectConnect into a standalone executable using [PyInstaller](https://pyinstaller.org/) and the provided `main.spec` file.

```bash
# Install PyInstaller
python3 -m pip install pyinstaller

# Build the executable using the spec file
pyinstaller main.spec
```

The output files are generated in the `dist/` directory:
- **macOS**: `dist/main.app`
- **Linux / Windows**: `dist/main/`

> **Note on JAR Asset**: The embedded `BedrockDirectEngine.jar` is located in `core/server/`. When building and distributing standalone packages, verify that `core/server/BedrockDirectEngine.jar` is included with the distribution or that a system Java runtime is present. If the JAR is absent, the application automatically uses the native Python protocol engine.

---

## Troubleshooting / FAQ

### The server does not appear under "LAN Games" on the console
- **Same Network**: Verify that the computer and console are connected to the same Wi-Fi router / subnet. Guest Wi-Fi networks and range extenders often isolate devices.
- **Router AP Isolation**: Check your router settings and ensure **AP Isolation** (Client Isolation) is **disabled**.
- **Firewall Rules**: Ensure your computer's firewall allows inbound UDP traffic on port `19132`.
- **Menu Refresh**: On your console, back out to the Minecraft main menu and return to the **Friends** tab, or restart the Minecraft client.

### Port UDP 19132 is already in use
If another application (such as a local Bedrock dedicated server or an existing Python/Java process) is using port 19132:
- On macOS/Linux, check what process is using the port:
  ```bash
  lsof -iUDP:19132
  ```
- Terminate the conflicting process:
  ```bash
  kill -9 <PID>
  ```
- Bedrock DirectConnect includes an automatic port cleanup mechanism that attempts to terminate conflicting processes on startup.

### Stuck on "Locating Server" or "Outdated Server"
- Verify that the target server is online using `python3 tests/test_query.py`.
- Ensure your Minecraft Bedrock client matches the configured protocol version (current default is **1.26.51**, protocol **2193**).

### Why can I close the application after connecting?
Standard proxy relays pass all traffic through your computer for the entire game session. Bedrock DirectConnect uses Minecraft's native `TransferPacket`. It instructs the console to open a direct socket connection to the target server's IP address. Once the console transfers, the computer is completely removed from the connection chain.

### Does this work with Java Edition servers?
Yes, if the Java server runs [GeyserMC](https://geysermc.org/), a bridge plugin that translates Minecraft Bedrock packets to Minecraft Java protocols on UDP port 19132.

---

## Contributing

Contributions and bug reports are welcome:

1. Fork the repository on GitHub.
2. Create a dedicated feature branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```
3. Commit your changes with clear, descriptive commit messages:
   ```bash
   git commit -m "feat: add support for custom bind IP"
   ```
4. Verify that existing tests pass:
   ```bash
   python3 -m unittest discover tests
   ```
5. Push to your branch and submit a Pull Request.

---

## License

<!-- TODO: Add a LICENSE file (e.g., MIT, GPL-3.0, or Apache-2.0) to define project terms and distribution rights. -->
*(TODO: No LICENSE file is currently included in the repository. Please add an appropriate license file.)*

---

## Credits / Acknowledgements

- **[PyQt5](https://riverbankcomputing.com/software/pyqt/)**: Desktop graphical user interface framework.
- **[BedrockConnect](https://github.com/Pugmatt/BedrockConnect)** & **[BedrockTogether](https://github.com/the-bedrock-network)**: Conceptual inspiration for console LAN discovery and Bedrock protocol redirection techniques.
- **[GeyserMC](https://geysermc.org/)**: Bedrock-to-Java cross-play bridge.
- **Mojang Studios & Microsoft**: Creators of Minecraft and Minecraft Bedrock Edition. This project is an independent community utility and is not affiliated with or endorsed by Mojang or Microsoft.
