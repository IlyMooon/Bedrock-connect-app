"""Reusable UI components for Bedrock DirectConnect with DailyMe aesthetic."""

import datetime
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QTextEdit,
    QPushButton,
)


class PingStatusCard(QFrame):
    """DailyMe Hero Card displaying remote server ping, online status, players, and cloned MOTD."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HeroCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Top bar: Title & Status pill badge
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)

        self.badge_title = QLabel("🎯 SERVEUR CIBLE & MOTD")
        self.badge_title.setObjectName("SectionTitle")

        self.status_badge = QLabel("● Prêt à tester")
        self.status_badge.setObjectName("StatusPillInactive")

        top_layout.addWidget(self.badge_title)
        top_layout.addStretch()
        top_layout.addWidget(self.status_badge)
        layout.addLayout(top_layout)

        # MOTD display sub-card
        self.motd_frame = QFrame()
        self.motd_frame.setObjectName("SubCard")
        motd_layout = QVBoxLayout(self.motd_frame)
        motd_layout.setContentsMargins(12, 10, 12, 10)
        motd_layout.setSpacing(3)

        self.motd_title = QLabel("En attente du serveur cible...")
        self.motd_title.setTextFormat(Qt.RichText)
        self.motd_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #ffffff;")
        self.motd_title.setWordWrap(True)

        self.motd_sub = QLabel("Le MOTD officiel sera cloné pour votre console.")
        self.motd_sub.setTextFormat(Qt.RichText)
        self.motd_sub.setStyleSheet("font-size: 11px; color: #8da2be;")
        self.motd_sub.setWordWrap(True)

        motd_layout.addWidget(self.motd_title)
        motd_layout.addWidget(self.motd_sub)
        layout.addWidget(self.motd_frame)

        # 3 Stat Chips row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(8)

        # Chip 1: Latency
        chip_lat = QFrame()
        chip_lat.setObjectName("StatChip")
        chip_lat_layout = QHBoxLayout(chip_lat)
        chip_lat_layout.setContentsMargins(6, 6, 6, 6)
        self.latency_label = QLabel("⚡ -- ms")
        self.latency_label.setAlignment(Qt.AlignCenter)
        self.latency_label.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 11px;")
        chip_lat_layout.addWidget(self.latency_label)

        # Chip 2: Players
        chip_ply = QFrame()
        chip_ply.setObjectName("StatChip")
        chip_ply_layout = QHBoxLayout(chip_ply)
        chip_ply_layout.setContentsMargins(6, 6, 6, 6)
        self.players_label = QLabel("👥 -- / --")
        self.players_label.setAlignment(Qt.AlignCenter)
        self.players_label.setStyleSheet("color: #34d399; font-weight: 700; font-size: 11px;")
        chip_ply_layout.addWidget(self.players_label)

        # Chip 3: Version
        chip_ver = QFrame()
        chip_ver.setObjectName("StatChip")
        chip_ver_layout = QHBoxLayout(chip_ver)
        chip_ver_layout.setContentsMargins(6, 6, 6, 6)
        self.version_label = QLabel("🏷️ v1.26.45")
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600;")
        chip_ver_layout.addWidget(self.version_label)

        stats_layout.addWidget(chip_lat)
        stats_layout.addWidget(chip_ply)
        stats_layout.addWidget(chip_ver)
        layout.addLayout(stats_layout)

    def set_loading(self, host: str, port: int):
        """Set card to testing/loading state."""
        self.status_badge.setText("⏳ Test...")
        self.status_badge.setObjectName("StatusPillInactive")
        self.status_badge.setStyle(self.status_badge.style())
        self.latency_label.setText("...")
        self.motd_title.setText(f"Interrogation de {host}:{port}...")
        self.motd_sub.setText("Récupération du MOTD officiel via RakNet...")

    def set_result(self, result: dict):
        """Update card with ping result."""
        if result.get("online"):
            latency = result.get("latency_ms", 0)
            players = result.get("current_players", 0)
            max_players = result.get("max_players", 0)
            version = result.get("version_name", "1.26.45")

            self.status_badge.setText("● En ligne & Cloné")
            self.status_badge.setObjectName("StatusPill")
            self.status_badge.setStyle(self.status_badge.style())
            self.latency_label.setText(f"⚡ {latency} ms")
            self.players_label.setText(f"👥 {players} / {max_players}")
            self.version_label.setText(f"🏷️ v{version}")

            html_name = result.get("html_server_name", result.get("server_name", ""))
            html_sub = result.get("html_sub_name", result.get("sub_name", ""))

            self.motd_title.setText(html_name if html_name else "Minecraft Bedrock Server")
            self.motd_sub.setText(html_sub if html_sub else "MOTD cloné avec succès pour votre console.")
        else:
            err = result.get("error", "Serveur injoignable")
            self.status_badge.setText("● Hors-ligne")
            self.status_badge.setObjectName("StatusPillInactive")
            self.status_badge.setStyle(self.status_badge.style())
            self.latency_label.setText("⚡ -- ms")
            self.players_label.setText("👥 0 / 0")
            self.version_label.setText("🏷️ v--")
            self.motd_title.setText(f"<span style='color: #f87171;'>{err}</span>")
            self.motd_sub.setText("Vérifiez l'adresse IP et le port UDP du serveur externe.")


class LiveLogWidget(QFrame):
    """DailyMe compact styled terminal activity viewer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("ACTIVITÉ EN DIRECT")
        title.setObjectName("SectionTitle")

        clear_btn = QPushButton("Effacer")
        clear_btn.setStyleSheet("padding: 3px 8px; font-size: 11px; border-radius: 8px;")
        clear_btn.clicked.connect(self.clear_logs)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(clear_btn)
        layout.addLayout(header_layout)

        # Log Text Box (compact)
        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("LogView")
        self.text_edit.setReadOnly(True)
        self.text_edit.setMinimumHeight(100)
        self.text_edit.setMaximumHeight(140)
        layout.addWidget(self.text_edit)

        # Initial message
        self.append_log("Application prête. MOTD cloné automatiquement.", "INFO")

    def append_log(self, message: str, level: str = "INFO"):
        """Append a colored, timestamped log line."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        colors = {
            "INFO": "#38bdf8",
            "SUCCESS": "#34d399",
            "WARNING": "#fbbf24",
            "ERROR": "#f87171",
            "DEBUG": "#64748b",
        }
        color = colors.get(level.upper(), "#94a3b8")

        line_html = f"<span style='color: #475569;'>[{timestamp}]</span> <span style='color: {color}; font-weight: 500;'>{message}</span>"
        self.text_edit.append(line_html)
        self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())

    def clear_logs(self):
        self.text_edit.clear()
        self.append_log("Journal réinitialisé.", "DEBUG")


class NetworkInfoBanner(QFrame):
    """Informational banner showing local Wi-Fi IP and port in DailyMe pill style."""

    def __init__(self, local_ip: str, port: int = 19132, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "background-color: rgba(16, 185, 129, 0.08); "
            "border: 1px solid rgba(16, 185, 129, 0.2); "
            "border-radius: 12px;"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        icon = QLabel("📡")
        icon.setStyleSheet("font-size: 14px;")

        info_label = QLabel(f"<b>Wi-Fi :</b> {local_ip} &nbsp;•&nbsp; <b>Port :</b> {port} &nbsp;•&nbsp; <span style='color: #34d399;'>Mode Standalone</span>")
        info_label.setStyleSheet("color: #cbd5e1; font-size: 11px;")

        layout.addWidget(icon)
        layout.addWidget(info_label)
        layout.addStretch()


class PartnerServerCard(QFrame):
    """Card displaying a partner server with real name and player count."""
    clicked = pyqtSignal(dict)

    def __init__(self, server_info: dict, parent=None):
        super().__init__(parent)
        self.server_info = server_info
        self.is_selected = False
        self.setObjectName("PartnerCard")
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Top row: Name + Partner badge
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        self.name_label = QLabel(server_info.get("name", "Serveur"))
        self.name_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #ffffff;")

        self.badge = QLabel("PARTENAIRE")
        self.badge.setObjectName("PartnerBadge")

        top_row.addWidget(self.name_label)
        top_row.addStretch()
        top_row.addWidget(self.badge)

        # Bottom row: Player count badge + selection checkmark
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(6)

        cur_p = server_info.get("current_players", 0)
        max_p = server_info.get("max_players", 0)
        self.players_badge = QLabel(f"👥 {cur_p:,} / {max_p:,}")
        self.players_badge.setObjectName("PlayerBadge")

        self.check_label = QLabel("")
        self.check_label.setStyleSheet("color: #10b981; font-weight: 800; font-size: 11px;")

        bottom_row.addWidget(self.players_badge)
        bottom_row.addStretch()
        bottom_row.addWidget(self.check_label)

        layout.addLayout(top_row)
        layout.addLayout(bottom_row)

    def set_player_count(self, current: int, max_p: int):
        self.players_badge.setText(f"👥 {current:,} / {max_p:,}")

    def set_selected(self, selected: bool):
        self.is_selected = selected
        if selected:
            self.setObjectName("PartnerCardSelected")
            self.check_label.setText("✓ Choisi")
        else:
            self.setObjectName("PartnerCard")
            self.check_label.setText("")
        self.setStyle(self.style())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.server_info)
        super().mousePressEvent(event)


class FavoriteServerCard(QFrame):
    """Card displaying a saved favorite server (strictly showing IP) with player count and delete button."""
    clicked = pyqtSignal(dict)
    delete_requested = pyqtSignal(str, int)

    def __init__(self, fav_info: dict, parent=None):
        super().__init__(parent)
        self.fav_info = fav_info
        self.setObjectName("FavoriteCard")
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 10, 10)
        layout.setSpacing(10)

        # Info Box
        info_box = QVBoxLayout()
        info_box.setSpacing(3)

        host = fav_info.get("host", "127.0.0.1")
        port = fav_info.get("port", 19132)

        # Strictly display ONLY the IP address as required
        self.ip_label = QLabel(host)
        self.ip_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #ffffff;")

        # Sub line with players and port
        sub_layout = QHBoxLayout()
        sub_layout.setSpacing(8)

        cur_p = fav_info.get("current_players", "--")
        max_p = fav_info.get("max_players", "--")
        self.players_label = QLabel(f"👥 {cur_p} / {max_p}")
        self.players_label.setObjectName("PlayerBadge")

        port_label = QLabel(f"Port {port}")
        port_label.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600;")

        sub_layout.addWidget(self.players_label)
        sub_layout.addWidget(port_label)
        sub_layout.addStretch()

        info_box.addWidget(self.ip_label)
        info_box.addLayout(sub_layout)

        layout.addLayout(info_box, stretch=1)

        # Delete Button (✕)
        self.del_btn = QPushButton("✕")
        self.del_btn.setObjectName("FavDeleteBtn")
        self.del_btn.setFixedSize(26, 26)
        self.del_btn.setToolTip("Supprimer ce serveur des favoris")
        self.del_btn.clicked.connect(self._on_delete_clicked)
        layout.addWidget(self.del_btn)

    def set_player_count(self, current: int, max_p: int):
        self.players_label.setText(f"👥 {current:,} / {max_p:,}")

    def _on_delete_clicked(self):
        self.delete_requested.emit(self.fav_info.get("host", ""), self.fav_info.get("port", 19132))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.fav_info)
        super().mousePressEvent(event)


class BottomNavBar(QFrame):
    """Fixed bottom navigation bar for mobile style interface."""
    tab_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BottomNavBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        self.tabs = [
            ("🎮  Jeu", 0),
            ("🚧  Bientôt...", 1),
            ("ℹ️  Infos", 2),
        ]
        self.buttons = []

        for label, idx in self.tabs:
            btn = QPushButton(label)
            btn.setObjectName("NavTabActive" if idx == 0 else "NavTab")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx: self.select_tab(i))
            layout.addWidget(btn, stretch=1)
            self.buttons.append(btn)

        self.current_index = 0

    def select_tab(self, index: int):
        if index == self.current_index:
            return
        self.current_index = index
        for i, btn in enumerate(self.buttons):
            if i == index:
                btn.setObjectName("NavTabActive")
            else:
                btn.setObjectName("NavTab")
            btn.setStyle(btn.style())
        self.tab_changed.emit(index)


class IOSSegmentedSlider(QFrame):
    """Authentic iOS-styled animated segmented control slider for page navigation."""
    tab_changed = pyqtSignal(int)

    def __init__(self, items=None, parent=None):
        super().__init__(parent)
        if items is None:
            items = ["🎮  Jeu", "🚧  Bientôt...", "ℹ️  Infos"]
        self.items = items
        self.current_index = 0

        self.setObjectName("IOSSliderContainer")
        self.setFixedHeight(46)

        # Sliding thumb pill (drawn behind buttons)
        self.thumb = QFrame(self)
        self.thumb.setObjectName("IOSSliderThumb")
        self.thumb.setAttribute(Qt.WA_TransparentForMouseEvents)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        self.buttons = []
        for i, item in enumerate(self.items):
            btn = QPushButton(item, self)
            btn.setObjectName("IOSSliderTextActive" if i == 0 else "IOSSliderText")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=i: self.set_index(idx))
            layout.addWidget(btn, stretch=1)
            self.buttons.append(btn)

        # Ensure thumb is visually behind the buttons
        self.thumb.lower()

        self._anim = QPropertyAnimation(self.thumb, b"geometry")
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_thumb_geometry(animate=False)

    def _update_thumb_geometry(self, animate=True):
        if not self.buttons:
            return
        n = len(self.buttons)
        margin = 4
        total_w = self.width() - (margin * 2)
        h = self.height() - (margin * 2)
        if total_w <= 0 or n <= 0:
            return
        tab_w = total_w / n
        target_x = int(margin + self.current_index * tab_w)
        target_w = int(tab_w)
        target_rect = QRect(target_x, margin, target_w, h)

        if animate:
            self._anim.stop()
            self._anim.setStartValue(self.thumb.geometry())
            self._anim.setEndValue(target_rect)
            self._anim.start()
        else:
            self.thumb.setGeometry(target_rect)

    def set_index(self, index: int):
        if index == self.current_index:
            return
        self.current_index = index
        self._update_thumb_geometry(animate=True)

        for i, btn in enumerate(self.buttons):
            if i == index:
                btn.setObjectName("IOSSliderTextActive")
            else:
                btn.setObjectName("IOSSliderText")
            btn.setStyle(btn.style())

        self.tab_changed.emit(index)


