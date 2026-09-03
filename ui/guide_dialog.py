"""Interactive Console Connection Guide Dialog."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QWidget,
    QPushButton,
    QTextBrowser,
)


class GuideDialog(QDialog):
    """Modal dialog displaying step-by-step connection guides for each console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Guide de Connexion Console - Bedrock DirectConnect")
        self.resize(650, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Title
        title_layout = QHBoxLayout()
        icon = QLabel("🎮")
        icon.setStyleSheet("font-size: 24px;")
        title = QLabel("Comment rejoindre depuis votre Console")
        title.setObjectName("TitleLabel")
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        subtitle = QLabel(
            "Suivez les étapes ci-dessous pour votre plateforme. Dès que le transfert est effectué, "
            "votre console communique en direct avec le serveur et vous pouvez fermer l'application !"
        )
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Tabs
        self.tabs = QTabWidget()

        self.tabs.addTab(self._create_ps_tab(), "PlayStation (PS4/PS5)")
        self.tabs.addTab(self._create_xbox_tab(), "Xbox One / Series")
        self.tabs.addTab(self._create_switch_tab(), "Nintendo Switch")
        self.tabs.addTab(self._create_mobile_tab(), "iOS & Android")
        self.tabs.addTab(self._create_faq_tab(), "FAQ & Dépannage")

        layout.addWidget(self.tabs)

        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _create_guide_view(self, html_content: str) -> QWidget:
        view = QTextBrowser()
        view.setHtml(html_content)
        view.setOpenExternalLinks(True)
        view.setStyleSheet(
            "background-color: #0d1117; border: 1px solid #21262d; border-radius: 8px; padding: 12px; color: #e6edf3;"
        )
        return view

    def _create_ps_tab(self) -> QWidget:
        content = """
        <h3 style="color: #58a6ff;">🎮 Guide PlayStation 4 & PlayStation 5</h3>
        <ol style="line-height: 1.6; color: #c9d1d9;">
            <li><b>Vérifiez votre réseau :</b> Votre console et cet ordinateur doivent être connectés sur le <b>même réseau Wi-Fi ou réseau local</b> (même box internet).</li>
            <li>Dans cette application, configurez le serveur cible et cliquez sur <b>« Démarrer la redirection »</b>.</li>
            <li>Allumez votre PlayStation et lancez <b>Minecraft</b>.</li>
            <li>Dans le menu principal, cliquez sur <b>Jouer</b>.</li>
            <li>Allez sur le 2ème onglet : <b>Amis</b>.</li>
            <li>Descendez tout en bas jusqu'à la section <b>« Parties en réseau local (LAN Games) »</b>.</li>
            <li>Vous verrez apparaître le serveur (ex: <i>Bedrock DirectConnect</i>).</li>
            <li><b>Cliquez dessus pour le rejoindre !</b></li>
        </ol>
        <div style="background-color: rgba(46, 160, 67, 0.15); border: 1px solid #238636; border-radius: 6px; padding: 10px; margin-top: 10px;">
            <b style="color: #3fb950;">✨ Fonctionnement Standalone :</b><br>
            Dès que vous apparaissez dans le monde du serveur distant, l'application sur votre ordinateur <b>peut être fermée</b>. Vous ne serez <b>pas déconnecté</b> !
        </div>
        """
        return self._create_guide_view(content)

    def _create_xbox_tab(self) -> QWidget:
        content = """
        <h3 style="color: #58a6ff;">🟢 Guide Xbox One & Xbox Series X|S</h3>
        <ol style="line-height: 1.6; color: #c9d1d9;">
            <li>Assurez-vous que votre Xbox est connectée à votre réseau domestique (Wi-Fi ou câble Ethernet sur la même box).</li>
            <li>Lancez la redirection dans l'application avec le bouton <b>« Démarrer »</b>.</li>
            <li>Ouvrez <b>Minecraft</b> sur la Xbox.</li>
            <li>Cliquez sur <b>Jouer</b>, puis rendez-vous dans l'onglet <b>Amis</b>.</li>
            <li>Sous la section <b>« Parties en réseau local »</b>, sélectionnez le serveur diffusé par l'application.</li>
            <li>Appuyez sur <b>A</b> pour rejoindre : la redirection vers votre serveur externe s'effectue instantanément.</li>
        </ol>
        <div style="background-color: rgba(46, 160, 67, 0.15); border: 1px solid #238636; border-radius: 6px; padding: 10px; margin-top: 10px;">
            <b style="color: #3fb950;">✨ Connexion Directe :</b><br>
            Le protocole Minecraft bascule la connexion directement entre votre Xbox et le serveur externe.
        </div>
        """
        return self._create_guide_view(content)

    def _create_switch_tab(self) -> QWidget:
        content = """
        <h3 style="color: #58a6ff;">🔴 Guide Nintendo Switch</h3>
        <ol style="line-height: 1.6; color: #c9d1d9;">
            <li>Vérifiez dans les paramètres de la Switch que vous êtes bien sur le même réseau Wi-Fi que l'ordinateur.</li>
            <li>Dans Minecraft sur Switch, assurez-vous d'être connecté à votre <b>Compte Microsoft</b> (nécessaire pour le multijoueur en ligne).</li>
            <li>Dans cette application, cliquez sur <b>« Démarrer la redirection »</b>.</li>
            <li>Sur Switch : <b>Jouer</b> &gt; Onglet <b>Amis</b> &gt; Section <b>Parties en réseau local</b>.</li>
            <li>Rejoignez la partie : la Switch se connecte à l'ordinateur puis est instantanément transférée sur le serveur distant.</li>
        </ol>
        <p style="color: #d29922;"><i>Note : Un abonnement Nintendo Switch Online actif est requis pour jouer sur des serveurs externes avec d'autres joueurs.</i></p>
        """
        return self._create_guide_view(content)

    def _create_mobile_tab(self) -> QWidget:
        content = """
        <h3 style="color: #58a6ff;">📱 Guide iPhone, iPad & Android</h3>
        <ol style="line-height: 1.6; color: #c9d1d9;">
            <li>Connectez votre téléphone ou tablette au Wi-Fi local.</li>
            <li>Cliquez sur <b>« Démarrer la redirection »</b> dans l'application.</li>
            <li>Ouvrez <b>Minecraft Bedrock</b> sur votre mobile.</li>
            <li>Onglet <b>Amis</b> &gt; <b>Parties LAN</b> &gt; Cliquez sur le serveur.</li>
            <li>Le transfert se fait en moins d'une seconde vers le serveur distant !</li>
        </ol>
        """
        return self._create_guide_view(content)

    def _create_faq_tab(self) -> QWidget:
        content = """
        <h3 style="color: #58a6ff;">❓ Foire Aux Questions & Dépannage</h3>
        <div style="line-height: 1.6; color: #c9d1d9;">
            <p><b style="color: #ffffff;">Q : Le serveur n'apparaît pas dans l'onglet « Amis » sur ma console ?</b><br>
            • Vérifiez que votre console et votre ordinateur sont sur le <b>même réseau Wi-Fi</b>.<br>
            • Sur certaines box (Livebox, Freebox), vérifiez que l'option « Isolation des clients Wi-Fi » est désactivée.<br>
            • Vérifiez que le pare-feu de votre ordinateur n'interdit pas les paquets UDP entrants sur le port 19132.</p>

            <p><b style="color: #ffffff;">Q : Pourquoi puis-je fermer l'application après connexion ?</b><br>
            Contrairement à un proxy relais standard qui consomme constamment la bande passante de votre PC, cette application utilise le paquet <code>TransferPacket</code> natif du protocole officiel Minecraft. Elle indique à la console l'adresse du serveur cible, la console s'y connecte directement en standalone, et l'application n'a plus besoin d'intervenir !</p>

            <p><b style="color: #ffffff;">Q : Est-ce compatible avec les serveurs Java ?</b><br>
            Oui, si le serveur Java utilise le plugin <b>GeyserMC</b> (qui ajoute la compatibilité Bedrock sur le port 19132).</p>
        </div>
        """
        return self._create_guide_view(content)
