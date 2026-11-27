"""Bake the tea level from art/room.blend. Geometry, pose and lighting have one source."""
from pathlib import Path
import bpy, os, re

root = Path(bpy.data.filepath).resolve().parents[1]
stage=Path(os.environ.get("PURRLOCK_BAKE_DIR",str(root/"art"/".bake")))
stage.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
assets={o["tea_key"]:o for o in scene.objects if "tea_key" in o}
expect={"saucer","cup","plate","fork","bowl","teapot"}
assert set(assets)==expect
decoys={}
for obj in scene.objects:
    name=re.sub(r'\.\d{3,}$','',obj.name)
    if name.startswith("Toy car"):key="car"
    elif name=="Wooden toy block":key="blocks" if obj.location.x>0 else "block"
    elif name in {"Red balloon","Balloon knot","Balloon thread"}:key="balloon"
    else:continue
    decoys[obj]=(key,name)

scene.render.resolution_x=1200
scene.render.resolution_y=896
scene.render.resolution_percentage=100
scene.render.threads_mode='FIXED'
scene.render.threads=8
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.cycles.samples=int(os.environ.get("PURRLOCK_SAMPLES","128"))
scene.cycles.use_adaptive_sampling=True
scene.cycles.adaptive_threshold=.012
scene.cycles.use_denoising=os.environ.get("PURRLOCK_OIDN")=="1"
for o in [*assets.values(),*decoys]:o.hide_render=True
scene.render.filepath=str(stage/"room.png")
if os.environ.get("PURRLOCK_KEEP_BACKGROUND")!="1" or not (stage/"room.png").is_file():
    bpy.ops.render.render(write_still=True)

# Transparent renders provide the exact same pixels at rest, during hints and during pickup.
for o in scene.objects:
    if o.type in {'MESH','CURVE'}:o.hide_render=True
scene.render.film_transparent=True
scene.cycles.samples=max(32,scene.cycles.samples//2)
scene.cycles.adaptive_threshold=.025
for key,o in assets.items():
    o.hide_render=False
    scene.render.filepath=str(stage/(key+".png"))
    bpy.ops.render.render(write_still=True)
    o.hide_render=True

# For interactive distractors only. Non-interactive furniture belongs to the baked room.
bpy.ops.object.select_all(action="DESELECT")
for o,(key,name) in decoys.items():
    for mod in o.modifiers:
        if mod.type=='BEVEL':mod.segments=3
    transform=o.matrix_world.copy()
    o.parent=None;o.matrix_world=transform
    o.name=f'{key}__{name}';o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(root/'assets/room.glb'),export_format='GLB',
                         use_selection=True,export_apply=True,export_texcoords=False,
                         export_cameras=False,export_lights=False,export_animations=False)
