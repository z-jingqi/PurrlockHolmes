"""Export live Blender props and bake the stationary room with its original soft lights."""
from pathlib import Path
import math
import re
import sys
import bpy
from bpy_extras.object_utils import world_to_camera_view

root = Path(bpy.data.filepath).resolve().parents[1]
out = root / 'assets'
scene = bpy.context.scene
path = {
    'Tea table':'table', 'Low table leg':'table',
    'Sideboard':'cabinet', 'Sideboard top':'cabinet', 'Linen cupboard door':'cabinet', 'Drawer pull':'cabinet',
    'Chair leg':'chair', 'Chair seat':'chair', 'Chair cushion':'chair', 'Chair upright':'chair', 'Chair back':'chair',
    'Chair book':'chair_book','Chair book label':'chair_book',
    'Storybook':'book', 'Book label':'book', 'Notebook':'notebook', 'Clementine':'orange', 'Clementine leaf':'orange',
    'Toy car chassis':'car','Toy car cab':'car','Toy car wheel':'car',
    'Wooden toy block':'block', 'Red balloon':'balloon', 'Balloon knot':'balloon','Balloon thread':'balloon',
}
dish = {1:'cup',2:'plate',3:'fork',4:'bowl'}
grouped = {}
skip = []
for obj in scene.objects:
    base = re.sub(r'\.\d{3,}$','',obj.name)
    key = dish.get(obj.get('pick_id',-1), path.get(base))
    if base in {'Plant pot','Plant stalk','Rubber plant leaf','Pot earth'}:
        x = obj.matrix_world.translation.x
        if obj.type == 'CURVE':
            point = obj.data.splines[0].points[0].co.to_3d()
            x = (obj.matrix_world @ point).x
        if x > 4.:
            key = 'plant'
    if base == 'Little book':
        index = round((obj.location.x - 3.57) / .18)
        key = f'cab_book{index}'
        obj.location.z = 1.62 + (.47 - index*.04)*.5
    if base == 'Bookend':
        key = f'cab_stop{int(obj.location.x > 4.)}'
    if base == 'Wooden toy block':
        key = 'blocks' if obj.location.x > 0 else 'block'
    if base == 'Folded linen':
        skip.append(obj) # replaced by the deforming table-edge towel
    if key and obj.type in {'MESH','CURVE'}:
        grouped[obj] = (key,base)

if "--models-only" not in sys.argv:
    # The clean plate retains the original AgX render and the stationary room, not the furniture.
    # Keep the original camera aspect and slightly lower sample noise with denoising.
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 896
    scene.render.resolution_percentage = 100
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 8
    scene.cycles.samples = 24
    scene.cycles.use_denoising = False
    scene.render.image_settings.file_format = 'WEBP'
    scene.render.image_settings.quality = 91
    for obj in [*grouped, *skip]:
        obj.hide_render=True
    scene.render.filepath = str(out/'room.webp')
    bpy.ops.render.render(write_still=True)

    # Bake isolated sprites for the original lift-and-arc animation.
    static = [o for o in scene.objects if o.type in {'MESH','CURVE'} and o not in grouped]
    for obj in static: obj.hide_render=True
    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = 'RGBA'
    scene.cycles.samples = 16
    for target in ['table','chair','cabinet']:
        current = [obj for obj,(key,name) in grouped.items() if key==target]
        for obj in current: obj.hide_render=False
        scene.render.filepath = str(out/f'flight-{target}.webp')
        bpy.ops.render.render(write_still=True)
        for obj in current: obj.hide_render=True

bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for obj,(key,name) in grouped.items():
    if key in {"table","chair","cabinet"}:continue # baked furniture, collision is kept in Godot
    for mod in obj.modifiers:
        if mod.type=='BEVEL':mod.segments=2
    transform = obj.matrix_world.copy()
    obj.parent=None
    obj.matrix_world=transform
    obj.name=f'{key}__{name}'
    obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(out/'room.glb'),export_format='GLB',
                         use_selection=True,export_apply=True,export_texcoords=False,
                         export_cameras=False,export_lights=False,export_animations=False)
