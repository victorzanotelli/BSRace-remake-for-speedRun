#!/usr/bin/env bash
# Reconstruit BS Folio Race (jeu + éditeur TAS) pour Linux (AppImage) et Windows (zip).
# Prérequis : git, Node 20+, npm. Usage : ./build.sh [dossier-du-clone-folio-2025]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="${1:-$HERE/../folio-2025}"
COMMIT="$(cat "$HERE/patches/UPSTREAM_COMMIT")"

# 1. Code du jeu : dépôt de Bruno Simon, au commit sur lequel le correctif TAS a été écrit
if [ ! -d "$SRC/.git" ]; then
    git clone https://github.com/brunosimon/folio-2025.git "$SRC"
fi
cd "$SRC"
git fetch -q origin || true
git checkout -q "$COMMIT"
git checkout -q -- sources
rm -f sources/Game/Tas.js sources/Game/TasEditor.js
git apply "$HERE/patches/folio-2025-tas.patch"

# 2. Compilation du jeu (.env obligatoire : sans VITE_WHISPERS_COUNT, le rendu WebGPU plante)
npm install --legacy-peer-deps --no-audit --no-fund
# Mode TAS : version déterministe de Rapier (snapshots reproductibles, mêmes résultats sur toutes les machines)
npm install --legacy-peer-deps --no-audit --no-fund --no-save @dimforge/rapier3d-deterministic@0.17.3
[ -f .env ] || cp .env.example .env
sed -i.bak -e 's/^VITE_GAME_PUBLIC=.*/VITE_GAME_PUBLIC=1/' -e 's/^VITE_COMPRESSED=.*/VITE_COMPRESSED=1/' \
    -e 's/^VITE_PLAYER_SPAWN=.*/VITE_PLAYER_SPAWN=circuit/' -e 's/^VITE_LOG=.*/VITE_LOG=/' \
    -e 's/^VITE_WHISPERS_COUNT=$/VITE_WHISPERS_COUNT=30/' .env && rm -f .env.bak
npm run build

# 3. Allègement : on retire les fichiers que la version compressée n'utilise pas
cd dist
rm -f sounds/musics/*.wav
find . -name "*.glb" ! -name "*-compressed.glb" | while read -r f; do [ -f "${f%.glb}-compressed.glb" ] && rm "$f"; done
find . -name "*.png" | while read -r f; do [ -f "${f%.png}.ktx" ] && rm "$f"; done

# 4. Emballage Electron
cd "$HERE"
rm -rf app && cp -r "$SRC/dist" app && cp "$SRC/license.md" LICENSE-folio-2025.md
npm install --no-audit --no-fund
npx electron-builder --linux --win --x64 --publish never || true
ls -la dist/*.AppImage dist/*.zip
