#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p dist/assets
cp web/index.html web/style.css web/game.js dist/
cp web/physics.html dist/
cp assets/room.webp assets/pick.png dist/assets/
cp assets/pickups.webp assets/pickups.json assets/paw-box.svg dist/assets/
cp assets/wrong.webp assets/wrong.png assets/wrong.json dist/assets/
cp assets/hint-ray.png dist/assets/
cp web/replays/physics.mp4 web/replays/physics-poster.webp dist/assets/
node tools/bundle-worker.mjs
