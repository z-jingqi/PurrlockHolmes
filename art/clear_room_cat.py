"""Render the sofa tile without the old cat, for the live 3D replacement."""
import math, os
from pathlib import Path
import bpy

scene = bpy.context.scene
for obj in scene.objects:
    if (obj.name.startswith("Cat ") or "tea_key" in obj or "room_balloon" in obj or "room_balloon_string" in obj
            or obj.instance_type == "COLLECTION" and obj.instance_collection
            and obj.instance_collection.get("asset_id") in {"rubber_plant","lance_plant"}):
        obj.hide_render = True

w, h = 1200, 896
l, t, r, b = 380, 231, 530, 354
scene.render.resolution_x, scene.render.resolution_y = w, h
scene.render.resolution_percentage = 100
scene.render.use_border = scene.render.use_crop_to_border = True
scene.render.border_min_x,scene.render.border_max_x = (l+.01)/w,(r+.01)/w
scene.render.border_min_y,scene.render.border_max_y = (h-b+.01)/h,(h-t+.01)/h
scene.render.film_transparent = False
scene.render.image_settings.file_format = "PNG"
scene.render.threads_mode = "FIXED"
scene.render.threads = min(8,os.cpu_count() or 4)
scene.cycles.samples = 192
scene.cycles.use_denoising = False
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = .010
scene.cycles.seed = 29
scene.render.filepath = str(Path(os.environ["PURRLOCK_CAT_STAGE"])/"sofa-clear.png")
bpy.ops.render.render(write_still=True)
