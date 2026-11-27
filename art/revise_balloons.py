"""Replace only the balloon props in the room source and bake transparent balloon-only crops.

PURRLOCK_BALLOON_STAGE=/tmp/balloon PURRLOCK_SAVE_BALLOONS=1 blender -b art/room.blend -P art/revise_balloons.py
"""
import json, math, os, sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from hero_props import BALLOON_DESIGNS, balloon, balloon_string
from room_props import finish_material

out=Path(os.environ["PURRLOCK_BALLOON_STAGE"])
out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
camera=scene.camera
markers={o["room_marker"]:o for o in scene.objects if "room_marker" in o}
collection=next(o.users_collection[0] for o in scene.objects if "room_balloon" in o)
for obj in list(scene.objects):
    if "room_balloon" in obj or "room_balloon_string" in obj:
        bpy.data.objects.remove(obj,do_unlink=True)

cord_material=finish_material("Balloon • unbleached cotton cord","cdb493",.92,.22)
for i,recipe in enumerate(BALLOON_DESIGNS):
    tip=balloon(collection,i,*recipe)
    markers[f"balloon_{i}"].location=tip
    balloon_string(collection,i,markers["tether"].location,tip,cord_material,scene)

bpy.context.view_layer.update()
if os.environ.get("PURRLOCK_SAVE_BALLOONS")=="1":
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)

W,H=1200,896
resolution=300
scene.render.resolution_x,scene.render.resolution_y=W,H
scene.render.resolution_percentage=resolution
scene.render.use_border=scene.render.use_crop_to_border=True
scene.render.film_transparent=True
scene.render.threads_mode="FIXED"
scene.render.threads=min(8,os.cpu_count() or 4)
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
scene.cycles.samples=128
scene.cycles.use_adaptive_sampling=True
scene.cycles.adaptive_threshold=.013
scene.cycles.seed=29

def project(v):
    p=world_to_camera_view(scene,camera,v)
    return p.x*W,(1-p.y)*H

metadata={}
for i in range(3):
    group=[o for o in scene.objects if o.get("room_balloon")==i]
    assert len(group)==3
    for o in scene.objects:
        if o.type in {"MESH","CURVE"} or o.instance_type=="COLLECTION":
            o.hide_render=o not in group
    corners=[project(o.matrix_world@Vector(p)) for o in group for p in o.bound_box]
    l,t=[math.floor(min(p[j] for p in corners))-8 for j in range(2)]
    r,b=[math.ceil(max(p[j] for p in corners))+8 for j in range(2)]
    scene.render.border_min_x,scene.render.border_max_x=(l+.01)/W,(r+.01)/W
    scene.render.border_min_y,scene.render.border_max_y=(H-b+.01)/H,(H-t+.01)/H
    key=f"balloon_{i}"
    scene.render.filepath=str(out/(key+".png"))
    bpy.ops.render.render(write_still=True)
    metadata[key]={"bounds":[l,t,r,b],"tip":project(markers[key].location)}
(out/"balloons.json").write_text(json.dumps(metadata,indent=2))
