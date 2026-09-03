# Bedrock DirectConnect 🎮

Application Python de bureau moderne avec interface graphique (PyQt5) permettant aux joueurs **Minecraft Bedrock Edition** sur consoles (**PlayStation 4/5**, **Xbox One / Series**, **Nintendo Switch**) et mobiles (**iOS**, **Android**) de rejoindre n'importe quel serveur Minecraft Bedrock externe (ou serveur Java avec Geyser).

> **Fonctionnalité Clé (Standalone 100% Déconnectable) :**  
> Contrairement aux proxys relais classiques où l'application doit rester active et relayer tout le trafic en permanence, **Bedrock DirectConnect utilise le paquet natif `TransferPacket` de Minecraft Bedrock**. Dès que la console clique sur le serveur local dans l'onglet « Amis », le serveur envoie un ordre de transfert natif : le client Minecraft de la console se connecte alors **directement** au serveur cible.  
> **Vous pouvez fermer ou éteindre l'application sur votre PC/Mac dès que la connexion est établie : le joueur continue à jouer sans aucune interruption !**

---

## Fonctionnalités

- **Interface Graphique Moderne & Sombre :** Design soigné inspiré des applications gaming modernes avec accents émeraude Minecraft.
- **Redirection Standalone Native :** Redirige le joueur via le protocole officiel Minecraft `TransferPacket` (`ID 85`).
- **Diffusion LAN Instantanée :** Broadcast automatique sur `255.255.255.255:19132` et sous-réseau local pour que le serveur apparaisse immédiatement dans l'onglet « Amis » sans latence.
- **Test de Ping en Direct :** Mesure de latence (ms), statut en ligne/hors-ligne, nombre de joueurs et rendu visuel du MOTD coloré (conversion des codes couleur `§` de Minecraft).
- **Gestionnaire de Profils de Serveurs :** Enregistrez vos serveurs préférés (*The Hive, Galaxite, CubeCraft, votre serveur privé survie, serveur Geyser*, etc.).
- **Journal d'Événements en Temps Réel :** Affiche la détection de la console, le pseudo/Gamertag du joueur et la confirmation du transfert.
- **Guide Console Intégré :** Instructions pas-à-pas illustrées pour PlayStation, Xbox, Nintendo Switch et mobiles.
- **Mode CLI / Headless :** Possibilité de faire tourner la redirection en ligne de commande pure sans interface graphique sur un serveur ou Raspberry Pi.

---

## Installation

L'application ne nécessite que Python 3 et la bibliothèque standard, avec PyQt5 pour l'interface graphique :

```bash
cd "Bedrock connect"
python3 -m pip install -r requirements.txt
```

---

## Utilisation

### 1. Mode Interface Graphique (Recommandé)

Lancez l'application :
```bash
python3 main.py
```

1. Sélectionnez ou ajoutez votre serveur dans la liste des profils.
2. Cliquez sur **« ⚡ Tester »** pour vérifier que le serveur est bien en ligne et afficher son MOTD.
3. Cliquez sur le grand bouton vert **« ▶ Démarrer la Redirection »**.
4. Sur votre console (PS4/PS5, Xbox, Switch) :
   - Lancez Minecraft.
   - Cliquez sur **Jouer** &gt; Onglet **Amis**.
   - Descendez dans la section **Parties en réseau local**.
   - Cliquez sur **Bedrock DirectConnect** !
5. Dès que le joueur apparaît dans le monde distant, le journal affiche la confirmation de transfert vert. **Vous pouvez alors fermer l'application !**

### 2. Mode Ligne de Commande (CLI / Headless)

Pour faire tourner la redirection sur un serveur dédié ou dans un terminal sans écran :

```bash
python3 main.py --cli --host geo.hivebedrock.network --port 19132 --name "Mon Serveur Hive"
```

---

## Guide par Console

| Console | Instructions |
| :--- | :--- |
| **PlayStation (PS4 / PS5)** | Assurez-vous d'être sur le même Wi-Fi. Minecraft &gt; **Jouer** &gt; **Amis** &gt; **Parties en réseau local** &gt; Cliquez sur le serveur. |
| **Xbox One / Series** | Connecté au même réseau. Minecraft &gt; **Jouer** &gt; **Amis** &gt; **Parties en réseau local**. |
| **Nintendo Switch** | Connecté au même Wi-Fi avec compte Microsoft connecté. **Amis** &gt; **Parties LAN**. |
| **iOS / Android** | Connecté au Wi-Fi. Menu Minecraft &gt; **Amis** &gt; **Parties LAN**. |

---

## Structure du Code

- `core/protocol/varint.py` : Encodage et décodage LEB128 standard (varuint32, varint32, varuint64).
- `core/protocol/raknet.py` : Protocole RakNet complet (Ping/Pong, Handshakes 0x05 à 0x08, Datagrams 0x80, ACK 0xC0).
- `core/protocol/bedrock.py` : Paquets Bedrock Game (Batch 0xFE, RequestNetworkSettings, NetworkSettings, Login, TransferPacket).
- `core/protocol/query.py` : Client de ping RakNet en temps réel et convertisseur de couleurs Minecraft (`§` vers HTML).
- `core/server/transfer_server.py` : Moteur serveur UDP autonome (Broadcast LAN, handshake et transfert instantané).
- `ui/main_window.py` : Fenêtre principale PyQt5.
- `ui/components.py` : Cartes de statut, aperçu MOTD, journal d'événements.
- `ui/guide_dialog.py` : Modal d'aide avec guides dédiés par console.
- `ui/styles.py` : Thème sombre QSS haute fidélité.
- `ui/config_manager.py` : Gestion de la persistance JSON des serveurs.

---

## Tests Unitaires

Pour exécuter les tests unitaires du protocole :

```bash
python3 -m unittest tests/test_protocol.py
```
