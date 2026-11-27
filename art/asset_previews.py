"""Refresh the thumbnails on the room's reusable Blender Collection Assets."""
from pathlib import Path
import os
import bpy
from mathutils import Vector

room=Path(bpy.data.filepath).resolve()
stage=Path(os.environ.get("PURRLOCK_BAKE_DIR",str(room.parent/".bake")))
thumbs=stage/"thumbs"
thumbs.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
assets={c["asset_id"]:c for c in bpy.data.collections if c.asset_data and "asset_id" in c}
camera=scene.camera
camera_before=(camera.matrix_world.copy(),camera.data.type,camera.data.ortho_scale)
visible={}
render_fields=("resolution_x","resolution_y","resolution_percentage","film_transparent","threads_mode","threads","filepath")
render_before={k:getattr(scene.render,k) for k in render_fields}
color_before=scene.render.image_settings.color_mode
samples_before=scene.cycles.samples
for obj in list(scene.objects):
    if obj.type in {'MESH','CURVE'} or obj.instance_type=='COLLECTION':
        visible[obj]=obj.hide_render
        obj.hide_render=True
scene.render.resolution_x=scene.render.resolution_y=192
scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.color_mode='RGBA'
scene.cycles.samples=28
scene.render.threads_mode="FIXED"
scene.render.threads=8
camera.data.type='ORTHO'

for key,asset in assets.items():
    preview=thumbs/(key+".png")
    if not preview.is_file():
        obj=bpy.data.objects.new("Asset preview only",None)
        scene.collection.objects.link(obj)
        obj.instance_type="COLLECTION"
        obj.instance_collection=asset
        points=[o.matrix_world@Vector(b) for o in asset.objects if o.type in {'MESH','CURVE'} for b in o.bound_box]
        lo=Vector(min(v[i] for v in points) for i in range(3))
        hi=Vector(max(v[i] for v in points) for i in range(3))
        center=(lo+hi)*.5
        view=Vector((.48,-.72,.70)).normalized()
        camera.location=center+view*5
        rotation=(-view).to_track_quat('-Z','Y')
        camera.rotation_euler=rotation.to_euler()
        q=rotation.inverted()
        on_screen=[q@(p-center) for p in points]
        camera.data.ortho_scale=2.28*max(max(abs(v.x),abs(v.y)) for v in on_screen)
        scene.render.filepath=str(preview)
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(obj,do_unlink=True)
    with bpy.context.temp_override(id=asset):
        bpy.ops.ed.lib_id_load_custom_preview(filepath=str(preview))

# Only the new asset previews should persist. Re-open the original scene with the previews saved.
for obj, was_hidden in visible.items():
    obj.hide_render=was_hidden
camera.matrix_world,camera.data.type,camera.data.ortho_scale=camera_before
for k,value in render_before.items():setattr(scene.render,k,value)
scene.render.image_settings.color_mode=color_before
scene.cycles.samples=samples_before
bpy.ops.wm.save_as_mainfile(filepath=str(room),compress=True)
