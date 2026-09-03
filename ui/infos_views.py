"""Views and sub-pages for the Infos section with mobile back navigation."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QScrollArea,
    QFrame,
    QTabWidget,
    QTextBrowser,
)


class InfosView(QWidget):
    """Container widget for the Infos section with a sub-navigation stacked widget."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # Stack for Infos views:
        # Index 0: Main Infos Menu (Guide, Dépannage, À propos)
        # Index 1: Guide Sub-page
        # Index 2: Dépannage Sub-page
        # Index 3: À propos Sub-page
        self.stack = QStackedWidget()

        self.menu_page = self._create_menu_page()
        self.guide_page = self._create_guide_page()
        self.troubleshoot_page = self._create_troubleshoot_page()
        self.about_page = self._create_about_page()

        self.stack.addWidget(self.menu_page)          # Index 0
        self.stack.addWidget(self.guide_page)         # Index 1
        self.stack.addWidget(self.troubleshoot_page)  # Index 2
        self.stack.addWidget(self.about_page)         # Index 3

        layout.addWidget(self.stack)

    def _create_header_with_back(self, title: str) -> QWidget:
        """Create a header row with a top-left back button and a title."""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(10)

        back_btn = QPushButton("← Retour")
        back_btn.setObjectName("BackButton")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #ffffff;")

        layout.addWidget(back_btn)
        layout.addWidget(title_lbl)
        layout.addStretch()
        return header

    def _create_menu_page(self) -> QWidget:
        """Main Infos navigation hub with 3 big mobile cards."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(12)

        # Title
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("Centre d'Aide & Infos")
        title.setObjectName("TitleLabel")
        sub = QLabel("Consultez les guides, solutions et fonctionnement.")
        sub.setObjectName("SubtitleLabel")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        layout.addLayout(title_box)

        layout.addSpacing(6)

        # Button 1: Guide
        guide_btn = QPushButton("📖   Guide de Connexion Console\n      PlayStation, Xbox, Switch, Mobile")
        guide_btn.setObjectName("MenuNavCard")
        guide_btn.setCursor(Qt.PointingHandCursor)
        guide_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        layout.addWidget(guide_btn)

        # Button 2: Dépannage
        depan_btn = QPushButton("🛠️   Dépannage & Solutions\n      Que faire si le serveur n'apparaît pas")
        depan_btn.setObjectName("MenuNavCard")
        depan_btn.setCursor(Qt.PointingHandCursor)
        depan_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        layout.addWidget(depan_btn)

        # Button 3: À propos
        about_btn = QPushButton("ℹ️   À propos de l'application\n      Comment fonctionne la redirection directe")
        about_btn.setObjectName("MenuNavCard")
        about_btn.setCursor(Qt.PointingHandCursor)
        about_btn.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        layout.addWidget(about_btn)

        layout.addStretch()
        return widget

    def _create_text_browser(self, html_content: str) -> QTextBrowser:
        browser = QTextBrowser()
        browser.setHtml(html_content)
        browser.setOpenExternalLinks(True)
        browser.setStyleSheet(
            "background-color: #0e131d; border: 1px solid #1c2436; border-radius: 12px; padding: 12px; color: #cbd5e1;"
        )
        return browser

    def _create_guide_page(self) -> QWidget:
        """Sub-page: Full connection guide with console tabs."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Top-left back button + title
        layout.addWidget(self._create_header_with_back("Guide de Connexion"))

        # Tabs for consoles
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #1c2436;
                background-color: #0e131d;
                border-radius: 10px;
            }
            QTabBar::tab {
                background-color: #141a24;
                color: #8da2be;
                padding: 6px 10px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 600;
                font-size: 11px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0e131d;
                color: #34d399;
                border-bottom: 2px solid #10b981;
            }
        """)

        # PS4 / PS5
        ps_html = """
        <h4 style="color: #58a6ff; margin-top: 0;">🎮 PlayStation 4 & 5</h4>
        <ol style="line-height: 1.6; color: #cbd5e1; padding-left: 18px;">
            <li>Assurez-vous que votre PlayStation et cet ordinateur sont sur le <b>même réseau Wi-Fi / box</b>.</li>
            <li>Dans l'application (onglet Jeu), sélectionnez ou saisissez votre serveur et cliquez sur <b>Démarrer</b>.</li>
            <li>Lancez <b>Minecraft</b> sur la PlayStation.</li>
            <li>Allez dans <b>Jouer</b> &gt; Onglet <b>Amis</b>.</li>
            <li>Descendez tout en bas jusqu'à <b>« Parties en réseau local (LAN Games) »</b>.</li>
            <li>Cliquez sur le serveur diffusé pour le rejoindre.</li>
        </ol>
        <div style="background-color: rgba(46, 160, 67, 0.15); border: 1px solid #238636; border-radius: 6px; padding: 8px; margin-top: 8px;">
            <b style="color: #3fb950;">✨ Standalone :</b> Dès que vous êtes dans le monde, vous pouvez fermer l'application sur votre ordinateur !
        </div>
        """
        tabs.addTab(self._create_text_browser(ps_html), "PlayStation")

        # Xbox
        xbox_html = """
        <h4 style="color: #58a6ff; margin-top: 0;">🟢 Xbox One & Series X|S</h4>
        <ol style="line-height: 1.6; color: #cbd5e1; padding-left: 18px;">
            <li>Vérifiez que la Xbox est connectée au même réseau domestique que l'ordinateur.</li>
            <li>Dans l'application, cliquez sur <b>Démarrer</b>.</li>
            <li>Ouvrez <b>Minecraft</b> sur votre Xbox.</li>
            <li>Cliquez sur <b>Jouer</b> &gt; Onglet <b>Amis</b>.</li>
            <li>Dans <b>« Parties en réseau local »</b>, sélectionnez le serveur diffusé.</li>
            <li>Appuyez sur <b>A</b> pour rejoindre : la redirection s'effectue automatiquement.</li>
        </ol>
        """
        tabs.addTab(self._create_text_browser(xbox_html), "Xbox")

        # Switch
        switch_html = """
        <h4 style="color: #58a6ff; margin-top: 0;">🔴 Nintendo Switch</h4>
        <ol style="line-height: 1.6; color: #cbd5e1; padding-left: 18px;">
            <li>Connectez votre Switch au même réseau Wi-Fi local.</li>
            <li>Vérifiez que vous êtes bien connecté à votre <b>Compte Microsoft</b> sur Minecraft.</li>
            <li>Dans cette application, cliquez sur <b>Démarrer</b>.</li>
            <li>Sur la Switch : <b>Jouer</b> &gt; <b>Amis</b> &gt; <b>Parties en réseau local</b>.</li>
            <li>Rejoignez la partie : la Switch est instantanément basculée sur le serveur cible.</li>
        </ol>
        <p style="color: #d29922; font-size: 11px;"><i>Note : Un abonnement Nintendo Switch Online actif est requis.</i></p>
        """
        tabs.addTab(self._create_text_browser(switch_html), "Switch")

        # Mobile
        mobile_html = """
        <h4 style="color: #58a6ff; margin-top: 0;">📱 iPhone, iPad & Android</h4>
        <ol style="line-height: 1.6; color: #cbd5e1; padding-left: 18px;">
            <li>Connectez votre appareil au Wi-Fi local de votre domicile.</li>
            <li>Lancez la redirection avec le bouton <b>Démarrer</b>.</li>
            <li>Ouvrez <b>Minecraft Bedrock</b> sur votre smartphone ou tablette.</li>
            <li>Allez dans <b>Jouer</b> &gt; <b>Amis</b> &gt; <b>Parties LAN</b>.</li>
            <li>Touchez le serveur pour rejoindre instantanément.</li>
        </ol>
        """
        tabs.addTab(self._create_text_browser(mobile_html), "Mobile")

        layout.addWidget(tabs)
        return page

    def _create_troubleshoot_page(self) -> QWidget:
        """Sub-page: Troubleshooting steps if connection fails."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Top-left back button + title
        layout.addWidget(self._create_header_with_back("Dépannage & Solutions"))

        content = """
        <h4 style="color: #f87171; margin-top: 0;">🛠️ Que faire si le serveur n'apparaît pas ?</h4>
        <div style="line-height: 1.6; color: #cbd5e1; font-size: 12px;">
            <p><b>1. Même réseau Wi-Fi & Box Internet :</b><br>
            Votre console et cet ordinateur doivent impérativement être connectés sur la <b>même box</b> (même réseau local). Attention aux réseaux "Invité" ou aux répéteurs Wi-Fi qui isolent parfois les appareils.</p>

            <p><b>2. Désactiver l'isolation Wi-Fi (AP Isolation) :</b><br>
            Certaines box (Livebox Orange, Freebox, SFR, Bouygues) possèdent une option intitulée <i>« Isolation des clients Wi-Fi »</i> qui empêche deux appareils sans fil de communiquer entre eux. Vérifiez dans l'interface de votre box que cette option est <b>désactivée</b>.</p>

            <p><b>3. Pare-feu de l'ordinateur :</b><br>
            Assurez-vous que le pare-feu de votre système (macOS ou Windows) autorise les flux entrants <b>UDP sur le port 19132</b>.</p>

            <p><b>4. Port UDP déjà occupé :</b><br>
            Si une autre application ou un serveur Minecraft local fonctionne déjà sur votre machine sur le port 19132, arrêtez-le avant de démarrer Bedrock DirectConnect.</p>

            <p><b>5. Compte Microsoft requis :</b><br>
            Sur PlayStation et Nintendo Switch, Minecraft exige que vous soyez connecté à un compte Microsoft gratuit pour autoriser les fonctions réseau.</p>

            <p><b>6. Rafraîchissement du menu Minecraft :</b><br>
            Si le serveur ne s'affiche pas, retournez à l'écran titre du jeu puis revenez dans l'onglet Amis, ou redémarrez le jeu Minecraft.</p>
        </div>
        """
        browser = self._create_text_browser(content)
        layout.addWidget(browser)
        return page

    def _create_about_page(self) -> QWidget:
        """Sub-page: About and how it works (vague/general explanations)."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Top-left back button + title
        layout.addWidget(self._create_header_with_back("À propos"))

        content = """
        <h4 style="color: #38bdf8; margin-top: 0;">ℹ️ Comment fonctionne la redirection ?</h4>
        <div style="line-height: 1.6; color: #cbd5e1; font-size: 12px;">
            <p>Sur console (PlayStation, Xbox, Nintendo Switch), les joueurs ne peuvent généralement pas saisir d'adresses IP personnalisées en raison des restrictions des constructeurs.</p>

            <p><b>Le principe en résumé :</b></p>
            <ul style="padding-left: 18px;">
                <li><b>Annonce locale :</b> L'application diffuse un paquet d'annonce sur votre réseau Wi-Fi local via le protocole officiel Minecraft Bedrock (RakNet).</li>
                <li><b>Détection par la console :</b> Votre console détecte automatiquement cette annonce et l'affiche dans son onglet « Amis », comme s'il s'agissait d'une partie LAN entre deux personnes dans la même pièce.</li>
                <li><b>Redirection intelligente :</b> Dès que vous cliquez sur le serveur depuis votre console, l'application lui transmet un paquet spécial appelé <code>TransferPacket</code> contenant l'adresse exacte du serveur distant souhaité.</li>
                <li><b>Connexion directe autonome :</b> La console prend immédiatement le relais et se connecte en direct au serveur externe à travers votre connexion Internet.</li>
                <li><b>Fermeture libre :</b> Une fois le transfert réalisé, la console communique directement avec le serveur : l'ordinateur ne sert plus de relais et vous pouvez fermer cette application en toute tranquillité !</li>
            </ul>

            <div style="background-color: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 8px; padding: 10px; margin-top: 12px;">
                <b style="color: #38bdf8;">Bedrock DirectConnect v2.0</b><br>
                <span style="color: #94a3b8;">Développé pour la communauté Minecraft Bedrock Console & Mobile.</span>
            </div>
        </div>
        """
        browser = self._create_text_browser(content)
        layout.addWidget(browser)
        return page
