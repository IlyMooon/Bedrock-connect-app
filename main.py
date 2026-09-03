#!/usr/bin/env python3
"""Bedrock DirectConnect - Application Launcher.

Permet de connecter les joueurs Minecraft Bedrock console (PS4/PS5, Xbox, Switch)
et mobiles à n'importe quel serveur externe via redirection autonome TransferPacket.
"""

import argparse
import sys
import time

def run_cli(host: str, port: int, name: str, sub: str):
    """Run BedrockTransferServer in CLI headless mode."""
    from core.server.transfer_server import BedrockTransferServer

    print("=" * 60)
    print(" Bedrock DirectConnect (Mode Console / Headless)")
    print("=" * 60)
    print(f"[*] Serveur cible : {host}:{port}")
    print(f"[*] Nom diffusé   : {name}")
    print(f"[*] Port d'écoute : UDP 19132")
    print("=" * 60)

    server = BedrockTransferServer(
        target_host=host,
        target_port=port,
        server_name=name,
        sub_name=sub,
        log_callback=lambda msg, lvl: print(f"[{lvl}] {msg}")
    )

    try:
        server.start()
        print("[+] Redirection en écoute. Appuyez sur Ctrl+C pour arrêter.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt demandé...")
    finally:
        server.stop()
        print("Serveur arrêté proprement.")


def run_gui():
    """Launch PyQt5 graphical user interface."""
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
    except ImportError:
        print("Erreur : PyQt5 n'est pas installé. Lancez : python3 -m pip install PyQt5")
        sys.exit(1)

    # Enable High DPI scaling
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Bedrock DirectConnect")

    from ui.main_window import MainWindow

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


def main():
    parser = argparse.ArgumentParser(description="Bedrock DirectConnect - Redirection Minecraft Bedrock Standalone")
    parser.add_argument("--cli", action="store_true", help="Lancer en mode ligne de commande sans interface graphique")
    parser.add_argument("--host", type=str, default="geo.hivebedrock.network", help="Adresse IP ou domaine du serveur cible")
    parser.add_argument("--port", type=int, default=19132, help="Port UDP du serveur cible (défaut: 19132)")
    parser.add_argument("--name", type=str, default="Bedrock DirectConnect", help="Nom affiché dans le menu LAN de la console")
    parser.add_argument("--sub", type=str, default="Cliquez pour rejoindre", help="Sous-titre MOTD")

    args = parser.parse_args()

    if args.cli:
        run_cli(args.host, args.port, args.name, args.sub)
    else:
        run_gui()


if __name__ == "__main__":
    main()
