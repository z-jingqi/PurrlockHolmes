#!/usr/bin/env sh
# Export the same native physics scene without changing the native entry point.
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
mkdir -p "$scratch/project/physics" "$scratch/project/assets" "$scratch/export"
cp physics/physics_room.gd physics/towel.gd physics/physics_room.tscn physics/room.glb physics/ui-zh.otf "$scratch/project/physics/"
cp assets/paw-box.svg "$scratch/project/assets/"
cp web/godot-physics.html "$scratch/project/shell.html"
sed 's|run/main_scene="res://main.tscn"|run/main_scene="res://physics/physics_room.tscn"|' project.godot > "$scratch/project/project.godot"
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
out="$root/dist/static/physics"
mkdir -p "$out"
cp "$scratch/export/engine.html" "$out/index.html"
cp "$root/physics/NotoSansCJK-OFL.txt" "$out/font-license.txt"
cp "$scratch/export"/*.js "$scratch/export/engine.pck" "$out/"
# Workers Static Assets limits the size of individual files. The raw WASM is
# ~39 MB; keep the official binary intact and serve it with Content-Encoding.
gzip -n -9 -c "$scratch/export/engine.wasm" > "$out/engine.wasm.gz"
