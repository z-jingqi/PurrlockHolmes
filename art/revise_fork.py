"""Update only the fork collection, then bake at the first room's fixed camera.

PURRLOCK_FORK_STAGE=/tmp/fork blender -b art/room.blend -P art/revise_fork.py
"""
import json, math, os, sys
from pathlib import Path
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from tea_assets import Studio

out=Path(os.environ["PURRLOCK_FORK_STAGE"])
out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
camera=scene.camera
fork=next(o for o in scene.objects if o.get("tea_key")=="fork")
collection=fork.instance_collection
for obj in list(collection.objects):
    bpy.data.objects.remove(obj,do_unlink=True)
studio=Studio()
studio.collection=collection
model=studio.fork()
model["asset_id"]="fork"
collection.asset_data.description="Curved stainless steel with a raised neck, scooped head and four tapered tines."
bpy.context.view_layer.update()
# Keep the authored scene identical, including light positions and other instances.
if os.environ.get("PURRLOCK_SAVE_FORK")=="1":
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)

for obj in scene.objects:
    if obj.type in {"MESH","CURVE"} or obj.instance_type=="COLLECTION":
        obj.hide_render=obj!=fork
w,h=1200,896
scene.render.resolution_x,scene.render.resolution_y = w,h
scene.render.resolution_percentage=400
corners=[world_to_camera_view(scene,camera,fork.matrix_world@model.matrix_world@Vector(p)) for p in model.bound_box]
l=math.floor(min(p.x for p in corners)*w)-10
r=math.ceil(max(p.x for p in corners)*w)+10
t=math.floor(min(1-p.y for p in corners)*h)-10
b=math.ceil(max(1-p.y for p in corners)*h)+10
scene.render.use_border=scene.render.use_crop_to_border=True
scene.render.border_min_x,scene.render.border_max_x=(l+.01)/w,(r+.01)/w
scene.render.border_min_y,scene.render.border_max_y=(h-b+.01)/h,(h-t+.01)/h
scene.render.film_transparent=True
scene.render.threads_mode="FIXED";scene.render.threads=8
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
scene.cycles.samples=128
scene.cycles.adaptive_threshold=.013
scene.cycles.use_denoising=False
scene.render.filepath=str(out/"fork.png")
bpy.ops.render.render(write_still=True)
(out/"fork.json").write_text(json.dumps({"bounds":[l,t,r,b]}))
