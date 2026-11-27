"""Render the clean room and transparent moving props from the editable room."""
import bpy, os, math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
out=Path(os.environ.get("PURR_PICKUP_DIR","/tmp/purr-pickup"))
out.mkdir(exist_ok=True,parents=True)
s=bpy.context.scene
s.render.image_settings.file_format='PNG'
s.render.image_settings.color_mode='RGBA'
s.render.use_border=False
s.render.use_crop_to_border=False
mesh=[o for o in s.objects if o.type in ('MESH','CURVE')]
for o in mesh:
    if o.get('pick_id',0):
        o.hide_render=True
s.render.filepath=str(out/'clean.png')
bpy.ops.render.render(write_still=True)
s.render.film_transparent=True
s.cycles.samples=24
w,h=s.render.resolution_x,s.render.resolution_y
deps=bpy.context.evaluated_depsgraph_get()
for i in range(1,8):
    group=[o for o in mesh if o.get('pick_id',0)==i]
    for o in mesh:
        o.hide_render=o not in group
    corners=[world_to_camera_view(s,s.camera,o.matrix_world @ Vector(v)) for o in group for v in o.bound_box]
    l=max(0,math.floor(min(v.x for v in corners)*w)-18)
    r=min(w,math.ceil(max(v.x for v in corners)*w)+18)
    b=max(0,math.floor(min(v.y for v in corners)*h)-18)
    t=min(h,math.ceil(max(v.y for v in corners)*h)+18)
    s.render.use_border=True
    s.render.use_crop_to_border=False
    s.render.border_min_x=l/w
    s.render.border_max_x=r/w
    s.render.border_min_y=b/h
    s.render.border_max_y=t/h
    s.render.filepath=str(out/f'item-{i}.png')
    bpy.ops.render.render(write_still=True)
