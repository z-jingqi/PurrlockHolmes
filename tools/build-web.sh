#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p dist/assets
cp web/index.html web/style.css web/game.js dist/
cp assets/room.webp assets/pick.png dist/assets/
node tools/bundle-worker.mjs
