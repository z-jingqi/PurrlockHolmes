"""Refresh the thumbnails on the marked collection assets after art/pack_tea.py."""
from pathlib import Path
import os
import bpy

room=Path(bpy.data.filepath).resolve()
stage=Path(os.environ.get("PURRLOCK_BAKE_DIR",str(room.parent/".bake")))
assets=[c for c in bpy.data.collections if c.asset_data and "asset_id" in c]
assert len(assets)==6
for asset in assets:
    preview=stage/"thumbs"/(asset["asset_id"]+".png")
    with bpy.context.temp_override(id=asset):
        bpy.ops.ed.lib_id_load_custom_preview(filepath=str(preview))
bpy.ops.wm.save_as_mainfile(filepath=str(room),compress=True)
