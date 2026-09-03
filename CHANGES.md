# 📋 Explications et Plan des Changements (CHANGES.md)

## 1. 🔍 Pourquoi étiez-vous bloqué sur « Recherche de serveur » ?

Lors de votre dernier test, vous êtes resté bloqué sur l'écran **« Recherche du serveur... »** (Locating server).

Deux causes précises ont été identifiées :
1. **Conflit de port UDP 19132 avec Java** :  
   Un processus Java (`BedrockConnect-1.0-SNAPSHOT.jar`, PID 15671) tournait en arrière-plan et écoutait sur le port `UDP 19132`.  
   Sous macOS, les sockets UDP autorisent parfois plusieurs liaisons simultanées (`SO_REUSEADDR`). En conséquence, les paquets réseau envoyés par votre console étaient interceptés par le processus Java au lieu de parvenir à l'application Python. La console n'obtenait aucune réponse de handshake RakNet et restait indéfiniment sur « Recherche du serveur ».
2. **Absence de nettoyage automatique du port 19132** :  
   L'application Python doit vérifier avant de démarrer si le port 19132 est déjà occupé par un autre processus (Java, ancienne instance Python, etc.), libérer le port automatiquement et le lier proprement.

---

## 2. 🌍 Le secret des applications comme BedrockTogether : Le "Monde Minecraft temporaire"

Vous avez souligné une observation cruciale :
> *"la plus part des applis qui font la même chose du point de vu d'un joueur, il lance la redirection, ça le met dans un espèce de monde minecraft, et là il se fait transférer"*

C'est **exactement** ainsi que fonctionnent **BedrockTogether** et **BedrockConnect** sur console (PlayStation, Nintendo Switch, Xbox) :

### Pourquoi ce monde temporaire est-il indispensable sur console ?
- Sur console, le moteur de Minecraft Bedrock refuse d'exécuter un `TransferPacket` si le client n'a pas terminé sa transition vers une session de jeu active.
- Si le serveur envoie un transfert trop tôt (pendant l'écran de chargement des packs), la console ignore le paquet ou freeze.
- **La solution éprouvée de BedrockTogether** :
  1. Après la négociation des packs de ressources, le serveur envoie un paquet **`StartGamePacket`** (ID 11 / `0x0B`).
  2. Il envoie un mini chunk vide **`LevelChunkPacket`** (ID 58 / `0x3A`).
  3. Il envoie **`PlayStatusPacket(PLAYER_SPAWN)`** (ID 2 / `0x02`, statut 3).
  4. L'écran de la console affiche **« Génération du terrain... »** et le joueur entre dans le monde virtuel vide (vide/ciel).
  5. Une fois dans cet état de jeu actif, le serveur envoie le **`TransferPacket`** (ID 85 / `0x55`).
  6. Le moteur Bedrock prend le relais nativement : il affiche **« Transfert vers un autre serveur... »** et connecte le joueur en direct au serveur externe, sans le moindre accroc !

---

## 3. 🛠️ Ce que nous allons changer et régler dans le code

### A. Dans `core/protocol/bedrock.py` :
- **Ajout du `StartGamePacket` (ID 11)** : Intégration du vecteur d'initialisation de monde minimal (`LAN Proxy`) extrait directement du dépôt `BedrockTogether/Protocol` (v2168 / 1.26.45).
- **Ajout du `LevelChunkPacket` (ID 58)** : Génération du chunk vide (258 octets) permettant à la console d'initialiser le rendu du monde sans charger de blocs lourds.
- **Ajout de `build_player_spawn()`** : Paquet `PlayStatus(PLAYER_SPAWN = 3)`.

### B. Dans `core/server/transfer_server.py` :
- **Nettoyage automatique du port UDP 19132** :
  - Avant de bind la socket, détection via `lsof` de tout processus tiers occupant le port 19132 (ex. `BedrockConnect-1.0-SNAPSHOT.jar` ou ancien process).
  - Fermeture / libération automatique du port avec journalisation claire dans l'interface.
- **Séquence complète de transition "Monde -> Transfert"** :
  - Dès réception de `ResourcePackClientResponse` (`COMPLETED` ou `HAVE_ALL_PACKS`), le serveur envoie dans la même trame ou successivement :
    1. `StartGamePacket` (ouvre la session de monde)
    2. `LevelChunkPacket` (satisfait l'attente de terrain)
    3. `PlayStatus(PLAYER_SPAWN)` (déclenche le spawn)
    4. `TransferPacket` (déclenche la redirection instantanée)
- **Garantie Standalone** :
  - Dès que la console exécute le transfert, elle se connecte directement à l'IP externe (`89.168.43.164:19132`). L'application peut alors être arrêtée sans perturber la partie.

---

## 4. 🚀 Résultat attendu pour le joueur

1. Vous cliquez sur le serveur local dans l'onglet **Amis**.
2. La console affiche **« Connexion au monde... »** puis **« Génération du terrain... »** (vous voyez le ciel / monde temporaire pendant une fraction de seconde).
3. La console affiche immédiatement **« Transfert vers le serveur... »**.
4. Vous êtes connecté sur votre serveur externe !
