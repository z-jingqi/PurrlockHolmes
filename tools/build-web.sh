#!/usr/bin/env sh
# Export the same native fixed-camera scene without changing the native entry point.
set -eu
cd "$(dirname "$0")/.."
root="$PWD"
godot="${GODOT:-godot}"
if [ -n "${GODOT_WEB_TEMPLATE:-}" ]; then
  template="$(realpath "$GODOT_WEB_TEMPLATE")"
else
  version="$("$godot" --version | cut -d. -f1-4)"
  template="${XDG_DATA_HOME:-$HOME/.local/share}/godot/export_templates/$version/web_nothreads_release.zip"
fi
test -f "$template" || { echo "Web export template not found: $template" >&2; exit 1; }
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
mkdir -p "$scratch/project/game" "$scratch/project/assets" "$scratch/export"
cp game/*.gd game/*.gdshader game/ui-zh.otf "$scratch/project/game/"
cp assets/room.webp assets/tea-sprites.webp assets/hint-ray.png assets/paw-box.svg assets/teddy.glb assets/teddy-look.png "$scratch/project/assets/"
cp web/index.html "$scratch/project/shell.html"
cp main.tscn project.godot "$scratch/project/"
cat > "$scratch/project/export_presets.cfg" <<PRESET
[preset.0]
name="Web"
platform="Web"
runnable=true
export_filter="all_resources"
include_filter=""
exclude_filter="shell.html"

[preset.0.options]
custom_template/release="$template"
variant/extensions_support=false
variant/thread_support=false
html/custom_html_shell="res://shell.html"
html/canvas_resize_policy=2
html/focus_canvas_on_start=true
progressive_web_app/enabled=false
PRESET
"$godot" --headless --path "$scratch/project" --import
"$godot" --headless --path "$scratch/project" --export-release Web "$scratch/export/engine.html"
out="$root/dist/static"
rm -rf "$out"
mkdir -p "$out"
cp "$scratch/export/engine.html" "$out/index.html"
cp "$root/game/NotoSansCJK-OFL.txt" "$out/font-license.txt"
cp "$scratch/export"/*.js "$scratch/export/engine.pck" "$out/"
# Workers Static Assets limits the size of individual files. The raw WASM is
# ~39 MB; keep the official binary intact and serve it with Content-Encoding.
gzip -n -9 -c "$scratch/export/engine.wasm" > "$out/engine.wasm.gz"
