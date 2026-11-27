"""Bake the first room, collectible layers and short plant animations."""
import json
import math
import os
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

root=Path(bpy.data.filepath).resolve().parents[1]
stage=Path(os.environ.get("PURRLOCK_BAKE_DIR",str(root/"art"/".bake")))
stage.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
camera=scene.camera
W,H=1200,896
scene.render.resolution_x=W
scene.render.resolution_y=H
scene.render.resolution_percentage=100
scene.render.threads_mode='FIXED'
scene.render.threads=min(8,os.cpu_count() or 4)
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.cycles.use_adaptive_sampling=True
scene.cycles.adaptive_threshold=.014
scene.cycles.seed=29
scene.cycles.use_denoising=os.environ.get("PURRLOCK_OIDN")=="1"
samples=int(os.environ.get("PURRLOCK_SAMPLES","144"))

targets={o["tea_key"]:o for o in scene.objects if "tea_key" in o}
assert set(targets)=={"saucer","cup","plate","fork","bowl","teapot"}
plants={o.instance_collection["asset_id"]:o for o in scene.objects
        if o.instance_type=="COLLECTION" and o.instance_collection
        and o.instance_collection.get("asset_id") in {"rubber_plant","lance_plant"}}
assert len(plants)==2
balloons=[[o for o in scene.objects if o.get("room_balloon")==i] for i in range(3)]
assert all(len(group)==3 for group in balloons)
geom=[o for o in scene.objects if o.type in {"MESH","CURVE"} or o.instance_type=="COLLECTION"]
animated=[*(o for o in geom if o.name.startswith("Cat ")),*targets.values(),*plants.values(),*(o for group in balloons for o in group)]

bpy.context.view_layer.update()

def pixel(point):
    v=world_to_camera_view(scene,camera,point)
    return (v.x*W,(1-v.y)*H)

def crop_bounds(objects,pad):
    points=[]
    for o in objects:
        instances=[(p,o.matrix_world@p.matrix_world) for p in o.instance_collection.objects] if o.instance_type=="COLLECTION" else [(o,o.matrix_world)]
        for obj,m in instances:
            if obj.type not in {"MESH","CURVE"}:continue
            points += [pixel(m@Vector(p)) for p in obj.bound_box]
    return [max(0,math.floor(min(p[0] for p in points))-pad),
            max(0,math.floor(min(p[1] for p in points))-pad),
            min(W,math.ceil(max(p[0] for p in points))+pad),
            min(H,math.ceil(max(p[1] for p in points))+pad)]

bounds={key:crop_bounds([obj],11 if key in targets else 15) for key,obj in (targets|plants).items()}
for i,group in enumerate(balloons):bounds[f"balloon_{i}"]=crop_bounds(group,7)
markers={o["room_marker"]:[round(v,2) for v in pixel(o.location)] for o in scene.objects if "room_marker" in o}
# Upright cup may settle a few pixels lower if its supporting saucer is removed.
cup_pos=targets["cup"].location
p0,p1=pixel(cup_pos),pixel(cup_pos+Vector((0,0,-.075)))
markers["cup_drop"]=[round(b-a,2) for a,b in zip(p0,p1)]
(stage/"room-layout.json").write_text(json.dumps({"bounds":bounds,"markers":markers},indent=2))

def render(name,box=None):
    scene.render.use_border=box is not None
    scene.render.use_crop_to_border=box is not None
    if box:
        l,t,r,b=box
        # The tiny fraction avoids floating point truncation at integer boundaries.
        scene.render.border_min_x=(l+.01)/W
        scene.render.border_max_x=(r+.01)/W
        scene.render.border_min_y=(H-b+.01)/H
        scene.render.border_max_y=(H-t+.01)/H
    scene.render.filepath=str(stage/(name+".png"))
    bpy.ops.render.render(write_still=True)

for o in geom:o.hide_render=o in animated
scene.render.film_transparent=False
scene.cycles.samples=samples
render("room")
if os.environ.get("PURRLOCK_REFRESH_BACKGROUND_ONLY")=="1":
    raise SystemExit(0)

for o in geom:o.hide_render=True
scene.render.film_transparent=True
scene.cycles.samples=max(32,samples//2)
scene.cycles.adaptive_threshold=.021
for key,obj in targets.items():
    obj.hide_render=False
    if key=="fork":
        scene.render.resolution_percentage=200
        render(key,bounds[key])
        scene.render.resolution_percentage=100
    else:
        render(key,bounds[key])
    obj.hide_render=True
for i,group in enumerate(balloons):
    for o in group:o.hide_render=False
    render(f"balloon_{i}",bounds[f"balloon_{i}"])
    for o in group:o.hide_render=True
for key,obj in plants.items():
    obj.hide_render=False
    leaves={p:p.matrix_world.copy() for p in obj.instance_collection.objects if "leaf_joint" in p}
    # Each leaf rotates around its end of the stem with a staggered start, different
    # pitch and flex, plus a tiny radial twist. Soil, stems and pot never move.
    for frame in range(17):
        at=frame/20
        for leaf,m in leaves.items():
            j=leaf["leaf_joint"]
            joint=Vector(leaf["leaf_root"])
            origin=Matrix.Translation(joint)
            t=max(0,at-(j%4)*.024)
            amp=(.21+(j%3)*.064)*math.exp(-t*5.2)*math.sin(t*(17.8+j*.63)) if t>0 else 0
            if j%3==1:amp*=-1
            amp*=max(0.0,min(1.0,(.80-at)/.17))
            bend=Matrix.Rotation(amp,4,Vector(leaf["leaf_axis"]))
            twist=Matrix.Rotation(amp*.34,4,Vector(leaf["leaf_direction"]))
            leaf.matrix_world=origin@twist@bend@Matrix.Translation(-joint)@m
        render(f"{key}_{frame:02d}",bounds[key])
    for leaf,m in leaves.items():leaf.matrix_world=m
    obj.hide_render=True
