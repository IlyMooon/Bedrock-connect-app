"""Mobile-styled Application Window for Bedrock DirectConnect with iOS Slider."""

import socket
import threading
from typing import Optional, List, Dict, Any

from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QLabel,
    QLineEdit,
    QSpinBox,
    QPushButton,
    QFrame,
    QStackedWidget,
    QMessageBox,
)

from core.protocol.query import ping_bedrock_server
from core.server.transfer_server import BedrockTransferServer
from ui.components import (
    PartnerServerCard,
    FavoriteServerCard,
    IOSSegmentedSlider,
)
from ui.config_manager import ConfigManager
from ui.infos_views import InfosView
from ui.styles import DARK_THEME_QSS


# 5 Curated Minecraft Bedrock Partner Servers
DEFAULT_PARTNER_SERVERS = [
    {
        "name": "The Hive",
        "host": "geo.hivebedrock.network",
        "port": 19132,
        "sub_name": "Bedwars, Murder Mystery & SkyWars",
        "current_players": 6840,
        "max_players": 20000,
    },
    {
        "name": "CubeCraft Games",
        "host": "play.cubecraft.net",
        "port": 19132,
        "sub_name": "EggWars, Lucky Islands & Skyblock",
        "current_players": 3850,
        "max_players": 10000,
    },
    {
        "name": "Galaxite",
        "host": "play.galaxite.net",
        "port": 19132,
        "sub_name": "Custom Mini-Games, Chronos & Core",
        "current_players": 1120,
        "max_players": 4000,
    },
    {
        "name": "Lifeboat Network",
        "host": "play.lbsg.net",
        "port": 19132,
        "sub_name": "Survival Games, Bedwars & Prison",
        "current_players": 2730,
        "max_players": 8000,
    },
    {
        "name": "Mineville",
        "host": "play.inpvp.net",
        "port": 19132,
        "sub_name": "Roleplay, City Life & High School",
        "current_players": 1560,
        "max_players": 5000,
    },
]


class ServerSignals(QObject):
    """Qt signals for thread-safe UI updates from server and pings."""
    log_signal = pyqtSignal(str, str)
    player_signal = pyqtSignal(str, str)
    transfer_signal = pyqtSignal(str, str, int)
    partner_ping_signal = pyqtSignal(str, int, int)
    fav_ping_signal = pyqtSignal(str, int, int)


def get_local_ip() -> str:
    """Detect local LAN IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


class MainWindow(QMainWindow):
    """Main window of Bedrock DirectConnect with clean mobile layout and iOS slider navigation."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bedrock DirectConnect")
        # Sleek mobile portrait aspect ratio
        self.resize(420, 720)
        self.setMinimumSize(390, 620)
        self.setStyleSheet(DARK_THEME_QSS)

        self.config_mgr = ConfigManager()
        self.local_ip = get_local_ip()
        self.server: Optional[BedrockTransferServer] = None
        self.selected_partner: Optional[dict] = None

        # Thread-safe signals
        self.signals = ServerSignals()
        self.signals.log_signal.connect(self._on_log)
        self.signals.player_signal.connect(self._on_player_detected)
        self.signals.transfer_signal.connect(self._on_transfer_success)
        self.signals.partner_ping_signal.connect(self._on_partner_ping_result)
        self.signals.fav_ping_signal.connect(self._on_fav_ping_result)

        self.partner_cards: List[PartnerServerCard] = []
        self.fav_cards: List[FavoriteServerCard] = []

        self._init_ui()
        self._refresh_favorites_ui()
        self._start_background_pings()

    def _init_ui(self):
        """Build the mobile layout: direct page content with iOS slider at the bottom."""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        self.setCentralWidget(container)

        # 1. Main QStackedWidget for the 3 tabs:
        # Index 0: Jeu
        # Index 1: Bientôt...
        # Index 2: Infos
        self.main_stack = QStackedWidget()

        self.game_page = self._build_game_page()
        self.soon_page = self._build_soon_page()
        self.infos_page = InfosView()

        self.main_stack.addWidget(self.game_page)
        self.main_stack.addWidget(self.soon_page)
        self.main_stack.addWidget(self.infos_page)

        container_layout.addWidget(self.main_stack, stretch=1)

        # 2. iOS-style Segmented Slider at the bottom
        bottom_dock = QWidget()
        bottom_dock.setStyleSheet("background-color: #0c1017; border-top: 1px solid #1a2233;")
        bottom_layout = QHBoxLayout(bottom_dock)
        bottom_layout.setContentsMargins(16, 10, 16, 14)
        bottom_layout.setSpacing(0)

        self.slider = IOSSegmentedSlider(items=["🎮  Jeu", "🚧  Bientôt...", "ℹ️  Infos"])
        self.slider.tab_changed.connect(self._on_tab_changed)
        bottom_layout.addWidget(self.slider)

        container_layout.addWidget(bottom_dock)

    def _build_game_page(self) -> QWidget:
        """Build Page 1 (Jeu): Partners, Favorites, and Connection Inputs."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        page_widget = QWidget()
        page_widget.setObjectName("ContentWidget")
        layout = QVBoxLayout(page_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # -------------------------------------------------------------
        # Section A: Serveurs Partenaires (En haut, 5 serveurs réels)
        # -------------------------------------------------------------
        partner_box = QVBoxLayout()
        partner_box.setSpacing(8)

        sec_partner_title = QLabel("✦ SERVEURS PARTENAIRES")
        sec_partner_title.setObjectName("SectionTitle")
        partner_box.addWidget(sec_partner_title)

        for s_info in DEFAULT_PARTNER_SERVERS:
            card = PartnerServerCard(s_info)
            card.clicked.connect(self._on_partner_card_clicked)
            partner_box.addWidget(card)
            self.partner_cards.append(card)

        layout.addLayout(partner_box)

        # -------------------------------------------------------------
        # Section B: Serveurs Favoris (Max 5, masquée si aucun favori)
        # -------------------------------------------------------------
        self.fav_section_container = QWidget()
        self.fav_section_layout = QVBoxLayout(self.fav_section_container)
        self.fav_section_layout.setContentsMargins(0, 0, 0, 0)
        self.fav_section_layout.setSpacing(8)

        self.fav_header_lbl = QLabel("⭐ SERVEURS FAVORIS")
        self.fav_header_lbl.setObjectName("SectionTitle")
        self.fav_section_layout.addWidget(self.fav_header_lbl)

        self.fav_cards_box = QVBoxLayout()
        self.fav_cards_box.setSpacing(6)
        self.fav_section_layout.addLayout(self.fav_cards_box)

        layout.addWidget(self.fav_section_container)

        # -------------------------------------------------------------
        # Section C: Connexion (IP personnalisée & Port, verrouillable)
        # -------------------------------------------------------------
        conn_card = QFrame()
        conn_card.setObjectName("Card")
        conn_layout = QVBoxLayout(conn_card)
        conn_layout.setContentsMargins(14, 14, 14, 14)
        conn_layout.setSpacing(10)

        conn_header_row = QHBoxLayout()
        conn_header_row.setSpacing(8)

        conn_title = QLabel("CONNEXION")
        conn_title.setObjectName("SectionTitle")
        conn_header_row.addWidget(conn_title)

        # Active server status badge
        self.server_status_badge = QLabel("● ACTIF")
        self.server_status_badge.setObjectName("StatusPill")
        self.server_status_badge.setVisible(False)
        conn_header_row.addWidget(self.server_status_badge)

        conn_header_row.addStretch()

        # Partner lock badge with unlock button
        self.partner_lock_badge = QWidget()
        lock_layout = QHBoxLayout(self.partner_lock_badge)
        lock_layout.setContentsMargins(0, 0, 0, 0)
        lock_layout.setSpacing(4)

        lock_lbl = QLabel("🔒 Partenaire")
        lock_lbl.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 700;")

        unlock_btn = QPushButton("✕ Débloquer")
        unlock_btn.setStyleSheet(
            "background-color: transparent; border: 1px solid #334155; border-radius: 6px; "
            "color: #94a3b8; font-size: 10px; padding: 2px 6px;"
        )
        unlock_btn.setCursor(Qt.PointingHandCursor)
        unlock_btn.clicked.connect(self._clear_partner_selection)

        lock_layout.addWidget(lock_lbl)
        lock_layout.addWidget(unlock_btn)
        self.partner_lock_badge.setVisible(False)

        conn_header_row.addWidget(self.partner_lock_badge)
        conn_layout.addLayout(conn_header_row)

        # Fields: Host & Port
        fields_row = QHBoxLayout()
        fields_row.setSpacing(8)

        host_box = QVBoxLayout()
        host_box.setSpacing(2)
        host_lbl = QLabel("ADRESSE IP / DOMAINE")
        host_lbl.setObjectName("FieldLabel")
        self.host_input = QLineEdit()
        self.host_input.setMinimumHeight(36)
        self.host_input.setPlaceholderText("ex: play.monserveur.fr")
        self.host_input.setText("geo.hivebedrock.network")
        host_box.addWidget(host_lbl)
        host_box.addWidget(self.host_input)

        port_box = QVBoxLayout()
        port_box.setSpacing(2)
        port_lbl = QLabel("PORT UDP")
        port_lbl.setObjectName("FieldLabel")
        self.port_spin = QSpinBox()
        self.port_spin.setMinimumHeight(36)
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(19132)
        port_box.addWidget(port_lbl)
        port_box.addWidget(self.port_spin)

        fields_row.addLayout(host_box, stretch=3)
        fields_row.addLayout(port_box, stretch=1)
        conn_layout.addLayout(fields_row)

        # Buttons Row: Start/Stop on the left, Add to Favorites on the right
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        # Left: Start / Stop Button
        self.start_btn = QPushButton("▶  DÉMARRER")
        self.start_btn.setObjectName("StartButton")
        self.start_btn.setMinimumHeight(44)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self._toggle_server)

        # Right: Add to Favorites Button
        self.fav_btn = QPushButton("⭐ + Favori")
        self.fav_btn.setObjectName("FavAddButton")
        self.fav_btn.setMinimumHeight(44)
        self.fav_btn.setCursor(Qt.PointingHandCursor)
        self.fav_btn.setToolTip("Enregistrer ce serveur dans vos favoris (max 5)")
        self.fav_btn.clicked.connect(self._add_current_to_favorites)

        btn_row.addWidget(self.start_btn, stretch=3)
        btn_row.addWidget(self.fav_btn, stretch=2)
        conn_layout.addLayout(btn_row)

        layout.addWidget(conn_card)

        scroll.setWidget(page_widget)
        return scroll

    def _build_soon_page(self) -> QWidget:
        """Build Page 2 (Bientôt...): Construction placeholder symbol."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("HeroCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 36, 24, 36)
        card_layout.setSpacing(16)
        card_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel("🚧")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 68px;")

        title = QLabel("Bientôt disponible")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #ffffff;")

        desc = QLabel(
            "Cette section est en cours de développement.\n"
            "De nouvelles fonctionnalités inédites arriveront très prochainement !"
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #8da2be; font-size: 13px; line-height: 1.5;")

        badge = QLabel("EN CONSTRUCTION")
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            "background-color: rgba(251, 191, 36, 0.12); border: 1px solid rgba(251, 191, 36, 0.3); "
            "color: #fbbf24; border-radius: 10px; font-weight: 800; font-size: 11px; padding: 4px 12px;"
        )

        card_layout.addWidget(icon_label)
        card_layout.addWidget(title)
        card_layout.addWidget(desc)
        card_layout.addWidget(badge, alignment=Qt.AlignCenter)

        layout.addWidget(card)
        return page

    # -------------------------------------------------------------
    # Bottom Navigation Handling
    # -------------------------------------------------------------
    def _on_tab_changed(self, idx: int):
        """Handle iOS slider tab change."""
        self.main_stack.setCurrentIndex(idx)
        # If switching to Infos, reset to the main menu of infos
        if idx == 2 and isinstance(self.infos_page, InfosView):
            self.infos_page.stack.setCurrentIndex(0)

    # -------------------------------------------------------------
    # Partner Servers Logic
    # -------------------------------------------------------------
    def _on_partner_card_clicked(self, s_info: dict):
        """When a partner server is clicked, select it and lock IP/Port inputs."""
        self.selected_partner = s_info

        # Update visual selection on cards
        for card in self.partner_cards:
            is_match = card.server_info.get("name") == s_info.get("name")
            card.set_selected(is_match)

        # Set values in connection inputs
        self.host_input.setText(s_info.get("host", ""))
        self.port_spin.setValue(s_info.get("port", 19132))

        # Lock inputs strictly as required:
        # "l'ip doit etre impossible a changer et a customiser quand le joueur selectionne ces serveurs, juste le lancer"
        self.host_input.setEnabled(False)
        self.port_spin.setEnabled(False)
        self.partner_lock_badge.setVisible(True)

        print(f"[INFO] Serveur Partenaire sélectionné : {s_info.get('name')} (IP verrouillée)")

    def _clear_partner_selection(self):
        """Unselect partner server and unlock IP/Port inputs for custom connection."""
        self.selected_partner = None
        for card in self.partner_cards:
            card.set_selected(False)

        self.host_input.setEnabled(True)
        self.port_spin.setEnabled(True)
        self.partner_lock_badge.setVisible(False)
        print("[INFO] Mode personnalisé activé : IP et port débloqués.")

    # -------------------------------------------------------------
    # Favorites Logic
    # -------------------------------------------------------------
    def _refresh_favorites_ui(self):
        """Refresh favorite cards list. Hide section completely if 0 favorites."""
        favs = self.config_mgr.get_favorites()

        # Clear existing cards in layout
        while self.fav_cards_box.count() > 0:
            item = self.fav_cards_box.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.fav_cards.clear()

        # Rule: "si il n'y a aucun serveur mis en favoris, ne pas afficher cette section"
        if not favs:
            self.fav_section_container.setVisible(False)
            return

        self.fav_section_container.setVisible(True)
        self.fav_header_lbl.setText(f"⭐ SERVEURS FAVORIS ({len(favs)}/5)")

        for fav in favs:
            card = FavoriteServerCard(fav)
            card.clicked.connect(self._on_favorite_clicked)
            card.delete_requested.connect(self._on_favorite_deleted)
            self.fav_cards_box.addWidget(card)
            self.fav_cards.append(card)

    def _on_favorite_clicked(self, fav_info: dict):
        """Load favorite server into connection inputs."""
        # Unselect partner mode
        self._clear_partner_selection()

        self.host_input.setText(fav_info.get("host", ""))
        self.port_spin.setValue(fav_info.get("port", 19132))
        print(f"[INFO] Favori chargé : {fav_info.get('host')}:{fav_info.get('port')}")

    def _on_favorite_deleted(self, host: str, port: int):
        """Remove server from favorites and refresh section."""
        removed = self.config_mgr.remove_favorite(host, port)
        if removed:
            print(f"[WARNING] Favori supprimé : {host}:{port}")
            self._refresh_favorites_ui()

    def _add_current_to_favorites(self):
        """Add the currently typed IP and port to favorites."""
        host = self.host_input.text().strip()
        port = self.port_spin.value()

        if not host:
            QMessageBox.warning(self, "Adresse requise", "Veuillez saisir une adresse IP avant d'ajouter en favori.")
            return

        favs = self.config_mgr.get_favorites()
        if len(favs) >= 5:
            QMessageBox.warning(
                self,
                "Limite atteinte",
                "Vous avez atteint la limite maximale de 5 serveurs favoris.\n"
                "Supprimez-en un avec le bouton '✕' pour en ajouter un nouveau."
            )
            return

        # Check duplicate
        for f in favs:
            if f.get("host", "").lower() == host.lower() and f.get("port") == port:
                QMessageBox.information(self, "Déjà enregistré", f"L'adresse {host}:{port} est déjà dans vos favoris.")
                return

        added = self.config_mgr.add_favorite(host, port)
        if added:
            print(f"[SUCCESS] ⭐ Serveur ajouté aux favoris : {host}")
            self._refresh_favorites_ui()
            # Trigger background ping for this new favorite
            self._ping_single_favorite(host, port)

    # -------------------------------------------------------------
    # Background Pings for Live Player Counts
    # -------------------------------------------------------------
    def _start_background_pings(self):
        """Start thread to query partner servers and favorites live player counts."""
        def worker():
            # Ping partners
            for p in DEFAULT_PARTNER_SERVERS:
                res = ping_bedrock_server(p["host"], p["port"], timeout=2.0)
                if res.get("online"):
                    cur = res.get("current_players", p["current_players"])
                    max_p = res.get("max_players", p["max_players"])
                    self.signals.partner_ping_signal.emit(p["host"], cur, max_p)

            # Ping favorites
            for f in self.config_mgr.get_favorites():
                res = ping_bedrock_server(f["host"], f.get("port", 19132), timeout=2.0)
                if res.get("online"):
                    cur = res.get("current_players", 0)
                    max_p = res.get("max_players", 0)
                    self.signals.fav_ping_signal.emit(f["host"], cur, max_p)

        threading.Thread(target=worker, daemon=True).start()

    def _ping_single_favorite(self, host: str, port: int):
        def worker():
            res = ping_bedrock_server(host, port, timeout=2.0)
            if res.get("online"):
                cur = res.get("current_players", 0)
                max_p = res.get("max_players", 0)
                self.signals.fav_ping_signal.emit(host, cur, max_p)
        threading.Thread(target=worker, daemon=True).start()

    def _on_partner_ping_result(self, host: str, cur: int, max_p: int):
        for card in self.partner_cards:
            if card.server_info.get("host") == host:
                card.set_player_count(cur, max_p)

    def _on_fav_ping_result(self, host: str, cur: int, max_p: int):
        for card in self.fav_cards:
            if card.fav_info.get("host") == host:
                card.set_player_count(cur, max_p)

    # -------------------------------------------------------------
    # Server Start / Stop Execution
    # -------------------------------------------------------------
    def _toggle_server(self):
        """Toggle Bedrock Transfer Server running state."""
        if self.server and self.server.running:
            # Stop server
            self.server.stop()
            self.server = None
            self.start_btn.setText("▶  DÉMARRER")
            self.start_btn.setObjectName("StartButton")
            self.start_btn.setStyle(self.start_btn.style())

            self.server_status_badge.setVisible(False)
            self._enable_inputs(True)
            print("[INFO] Serveur de redirection arrêté.")
        else:
            # Start server
            target_host = self.host_input.text().strip()
            target_port = self.port_spin.value()

            if not target_host:
                QMessageBox.warning(self, "Adresse requise", "Veuillez spécifier l'adresse IP ou le domaine du serveur cible.")
                return

            server_name = self.selected_partner.get("name") if self.selected_partner else "Bedrock DirectConnect"
            sub_name = self.selected_partner.get("sub_name") if self.selected_partner else "Cliquez pour rejoindre"

            proto_ver = self.config_mgr.get_protocol_version()
            ver_str = self.config_mgr.get_bedrock_version()

            try:
                self.server = BedrockTransferServer(
                    target_host=target_host,
                    target_port=target_port,
                    server_name=server_name,
                    sub_name=sub_name,
                    bind_port=self.config_mgr.data.get("bind_port", 19132),
                    protocol_version=proto_ver,
                    version_string=ver_str,
                    log_callback=lambda msg, lvl: self.signals.log_signal.emit(msg, lvl),
                    player_callback=lambda p, a: self.signals.player_signal.emit(p, f"{a[0]}:{a[1]}"),
                    transfer_callback=lambda p, h, pt: self.signals.transfer_signal.emit(p, h, pt)
                )
                self.server.start()

                self.start_btn.setText("⏹  ARRÊTER")
                self.start_btn.setObjectName("StopButton")
                self.start_btn.setStyle(self.start_btn.style())

                self.server_status_badge.setVisible(True)
                self._enable_inputs(False)
                print("[SUCCESS] 🚀 Redirection lancée ! En attente de votre console...")
            except Exception as e:
                QMessageBox.critical(self, "Erreur de démarrage", f"Impossible de démarrer le serveur UDP :\n{e}")

    def _enable_inputs(self, enabled: bool):
        """Enable or disable interactive controls while server is running."""
        if not enabled:
            self.host_input.setEnabled(False)
            self.port_spin.setEnabled(False)
            self.fav_btn.setEnabled(False)
        else:
            self.fav_btn.setEnabled(True)
            if self.selected_partner:
                self.host_input.setEnabled(False)
                self.port_spin.setEnabled(False)
            else:
                self.host_input.setEnabled(True)
                self.port_spin.setEnabled(True)

    def _on_log(self, message: str, level: str):
        print(f"[{level}] {message}")

    def _on_player_detected(self, player_name: str, client_addr: str):
        print(f"[SUCCESS] 🎮 Console détectée : {player_name} ({client_addr})")

    def _on_transfer_success(self, player_name: str, target_host: str, target_port: int):
        print(f"[SUCCESS] 🎉 Transfert accompli ! {player_name} -> {target_host}:{target_port}")

    def closeEvent(self, event):
        """Cleanly stop background server when exiting."""
        if self.server and self.server.running:
            self.server.stop()
        event.accept()
