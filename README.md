# BS Folio Race — édition speedrun / TAS

Version jouable hors ligne de la course du [portfolio 2025 de Bruno Simon](https://github.com/brunosimon/folio-2025) (licence MIT), pour Linux et Windows, avec un **éditeur TAS** intégré.

- Le jeu démarre directement à côté du circuit.
- **F9** bascule entre le jeu normal et l'éditeur TAS.
- F11 : plein écran · F12 : outils de développement.

## Lancer

| Système | Fichier | Commande |
|---|---|---|
| Windows | `BS-Folio-Race-<version>-win-x64.zip` | dézipper, lancer `BS Folio Race.exe` |
| Linux | `BS-Folio-Race-<version>-x86_64.AppImage` | `chmod +x` puis `./BS-Folio-Race-…AppImage` (sous WSL : ajouter `--appimage-extract-and-run`) | autre variante pour seulement lancer la version tas `./BS-Folio-Race-1.1.0-x86_64.AppImage --appimage-extract-and-run --tas`

Options : `--tas` (ouvrir directement l'éditeur), `--debug` (panneau de réglages du jeu), `--webgpu` (Linux : tenter WebGPU au lieu de WebGL2).

## L'éditeur TAS

En mode TAS, le jeu est **entièrement déterministe**. Les mêmes entrées donnent toujours exactement la même course, au bit près, et un movie se rejoue à l'identique dans l'éditeur, après n'importe quel retour en arrière, et dans une autre instance du jeu. Pour y arriver, le mode TAS :

- fait avancer le jeu image par image (60 images/s) en temps virtuel : boucle principale, animations gsap, `Date.now`, `setTimeout` et `setInterval` ;
- utilise un hasard à graine fixe, avec une source séparée pour les sons et l'interface ;
- coupe le jeu du clavier, de la souris et de la manette : l'éditeur lit les touches lui-même et le jeu ne reçoit que les entrées du movie, par le même chemin en enregistrement et en relecture ;
- utilise la version **déterministe** du moteur physique Rapier (`@dimforge/rapier3d-deterministic`, même version 0.17.3). Avec la version standard, recharger un savestate ne redonne pas exactement le même état. La version déterministe garantit aussi les mêmes résultats entre Windows et Linux. Le jeu normal (hors mode TAS) garde le Rapier d'origine.

Le movie démarre à la **première image chronométrée** (fin du compte à rebours). Le chrono est celui du jeu.

### Raccourcis

| Touche | Action |
|---|---|
| F2 | Lecture / pause (à la vitesse choisie) |
| F4 | Image suivante (maintenir : avance image par image) |
| F3 | Image précédente (maintenir : rembobiner) |
| F5 | Enregistrement ON/OFF : vos touches (flèches/ZQSD, Maj, B, Espace, pavé numérique…) sont écrites dans le movie à chaque image jouée |
| F6 | Retour au départ |
| F7 / F8 | Ralentir / accélérer la lecture (×0,05 à ×4) |
| Ctrl+Z / Ctrl+Y | Annuler / rétablir |
| Inser / Suppr | Insérer une image neutre / supprimer l'image courante |
| Ctrl+S / Ctrl+O | Enregistrer / ouvrir un movie (`.json`) |
| F1 | Aide |
| F9 | Retour au jeu normal |

### Édition à la souris

Chaque ligne de la liste correspond à une image : **Gaz** (▲ avant, ▼ arrière, · rien), **Direction** (barre de gauche à droite, de -1 à +1), **Bst** (boost), **Frn** (frein), **Saut** (suspensions hautes).

- Clic : modifier. Pour la direction, la valeur dépend de l'endroit du clic (bord gauche = plein gauche, centre = tout droit).
- Glisser : peindre plusieurs images d'un coup.
- Clic droit sur Direction : remettre à 0.
- Molette : ±1 image (Maj : ±10). La barre de temps permet de sauter n'importe où.

Quand vous modifiez une image passée, la course est **recalculée exactement** à partir du dernier savestate (un savestate est pris automatiquement toutes les 20 images, point vert dans la liste).

### Méthode conseillée

1. En pause, activez **REC** (F5), maintenez les touches voulues et avancez avec **F4**. Vous pouvez aussi enregistrer en lecture continue au ralenti (F7 puis F2).
2. Revenez en arrière avec **F3** ou la molette pour corriger : la suite du movie est conservée.
3. Affinez image par image à la souris.
4. À l'arrivée, le temps final et l'image d'arrivée s'affichent. Enregistrez avec Ctrl+S.

Le movie en cours est aussi sauvegardé automatiquement (et restauré au prochain lancement de l'éditeur).

### Format des movies

```json
{
  "format": "bs-folio-tas-movie", "version": 1, "game": "brunosimon/folio-2025", "fps": 60,
  "result": { "frames": 1652, "time": 27.533, "timings": [ … ] },
  "inputs": [ [ gaz, direction, boost, frein, "suspensions" ], … ]
}
```

- `gaz` : -1 à 1.
- `direction` : -1 à 1 ; **+1 = gauche**, -1 = droite (convention du jeu).
- `boost`, `frein` : 0 ou 1.
- `suspensions` : `""` (normal) ou 4 lettres `l`/`m`/`h` (bas/milieu/haut) pour avant-droite, avant-gauche, arrière-droite, arrière-gauche ; `"hhhh"` = saut.

## Reconstruire

```bash
./build.sh            # clone folio-2025, applique patches/folio-2025-tas.patch, compile, emballe
```

Le correctif `patches/folio-2025-tas.patch` ajoute `sources/Game/Tas.js` (mode déterministe, savestates) et `sources/Game/TasEditor.js` (interface), et modifie trois lignes (`index.js`, `Rendering.js`, `Game.js` pour charger Rapier déterministe en mode TAS). Il s'applique sur le commit indiqué dans `patches/UPSTREAM_COMMIT`.

Les exécutables (> 100 Mo) se publient dans les **Releases** GitHub, pas dans le dépôt.

## Outils (facultatif)

Le dossier `tools/` contient le pilote sans affichage (Chromium + Playwright) utilisé pour les tests de déterminisme. Il servira de base à l'optimisation automatique :

```bash
cd tools && npm install playwright && npx playwright install chromium
node determinism.mjs ../../folio-2025/dist     # même movie, deux instances → trajectoires identiques ?
node savestate-test.mjs ../../folio-2025/dist  # savestates et retours en arrière → identique au run continu ?
```

## Licences

Jeu : © 2025 Bruno Simon, licence MIT (`LICENSE-folio-2025.md`). Emballage et éditeur TAS : MIT.
