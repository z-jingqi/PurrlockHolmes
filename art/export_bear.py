"""Export the original showroom bear as reusable glTF and bake its camera-match inputs."""
import json
import math
import os
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

root=Path(bpy.data.filepath).resolve().parents[1]
out=Path(os.environ.get("PURRLOCK_BEAR_STAGE",str(root/"art"/".bake"/"bear")))
out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
camera=scene.camera
W,H=1200,896
bear=[o for o in scene.objects if o.name.startswith(("Plush bear • ","Bear • "))]
assert len(bear)>=18
foot=Vector((4.72,-.03,.064))
anchor=scene.objects["Ribbon pin"].location.copy()

def projected(v):
    p=world_to_camera_view(scene,camera,v)
    return Vector((p.x*W,(1-p.y)*H))
def godot(v):
    return [round(v.x,8),round(v.z,8),round(-v.y,8)]

pts=[projected(o.matrix_world@Vector(p)) for o in bear for p in o.bound_box]
bounds=[math.floor(min(v.x for v in pts))-12,math.floor(min(v.y for v in pts))-12,
        math.ceil(max(v.x for v in pts))+12,math.ceil(max(v.y for v in pts))+12]
(out/"bear-layout.json").write_text(json.dumps({
    "bounds":bounds, "origin":godot(foot), "anchor_local":godot(anchor-foot), "screen_pin":list(projected(anchor)),
    "camera":godot(camera.location), "target":godot(Vector((0,.06,1.10))),
    "lens":camera.data.lens, "sensor_width":camera.data.sensor_width,
},indent=2))

scene.render.resolution_x=W
scene.render.resolution_y=H
scene.render.resolution_percentage=100
scene.render.threads_mode="FIXED"
scene.render.threads=min(8,os.cpu_count() or 4)
scene.render.use_border=True
scene.render.use_crop_to_border=True
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
l,t,r,b=bounds
scene.render.border_min_x=(l+.01)/W
scene.render.border_max_x=(r+.01)/W
scene.render.border_min_y=(H-b+.01)/H
scene.render.border_max_y=(H-t+.01)/H
scene.cycles.samples=192
scene.cycles.use_adaptive_sampling=True
scene.cycles.adaptive_threshold=.010
scene.cycles.seed=29

# Keep ground contact and bounced light, but see the actual floor behind the bear.
# Match the visibility of the approved room bake.
for o in scene.objects:
    if "tea_key" in o or "room_balloon" in o or (
        o.instance_type=="COLLECTION" and o.instance_collection
        and o.instance_collection.get("asset_id") in {"rubber_plant","lance_plant"}):
        o.hide_render=True
for o in bear:o.visible_camera=False
scene.render.film_transparent=False
scene.render.filepath=str(out/"bear-clear.png")
bpy.ops.render.render(write_still=True)

# The original high-precision coverage supplies clean texture colors at the edges.
for o in scene.objects:
    if o.type in {"MESH","CURVE"} or o.instance_type=="COLLECTION":o.hide_render=o not in bear
for o in bear:o.visible_camera=True
scene.render.resolution_percentage=200
scene.render.film_transparent=True
scene.cycles.samples=96
scene.render.filepath=str(out/"bear-coverage.png")
bpy.ops.render.render(write_still=True)

# Portable source materials, independently settable, with a ground-level origin.
bpy.ops.object.select_all(action="DESELECT")
pivot=bpy.data.objects.new("Teddy · feet origin",None)
scene.collection.objects.link(pivot)
pivot.select_set(True)
for o in bear:
    old=o.matrix_world.copy()
    o.parent=pivot
    o.matrix_world=Matrix.Translation(-foot)@old
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(root/"assets"/"teddy.glb"),export_format="GLB",
                         use_selection=True,export_apply=True,export_texcoords=False,
                         export_cameras=False,export_lights=False,export_animations=False)
