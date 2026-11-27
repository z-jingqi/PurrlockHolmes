"""Export the Blender-authored props retained by the 3D physics experiment."""
from pathlib import Path
import re
import bpy

root = Path(bpy.data.filepath).resolve().parents[1]
names = {'Tea table':'table', 'Low table leg':'table',
         'Storybook':'book','Book label':'book',
         'Notebook':'notebook','Clementine':'orange','Clementine leaf':'orange'}
labels = {1:'cup',2:'plate',3:'fork'}
static = {'Diorama plinth','Birch floorboard','Back wall','Left return wall','Back skirting',
          'Sofa base','Sofa back','Seat cushion','Sofa arm','Blush pillow','Butter pillow',
          'Wool rug','Rug stitched dash','Window frame','Window pane','Window crossbar',
          'Window post','Window sill','Cloud through glass','Sideboard','Sideboard top',
          'Linen cupboard door','Drawer pull','Cat body','Cat head','Cat ear','Cat ear blush',
          'Cat dot eye','Cat blush','Cat little nose','Cat little paw','Cat tail'}
materials = bpy.data.materials
for m in materials:
    if not m.use_nodes:continue
    shader=m.node_tree.nodes.get('Principled BSDF')
    if not shader:continue
    name=m.name
    roughness={'Milk':.88,'Cloud blue':.61,'Soft pewter':.32,
               'Honey beech':.67,'Pale oak':.71,'Rice paper':.92,
               'Pistachio':.89,'Leaf':.82,'Peach':.82}.get(name,.75)
    shader.inputs['Roughness'].default_value=roughness
    shader.inputs['Metallic'].default_value=.82 if name=='Soft pewter' else 0.
bpy.ops.object.select_all(action="DESELECT")
for o in tuple(bpy.context.scene.objects):
    n=re.sub(r'\.\d{3,}$','',o.name)
    group=labels.get(o.get('pick_id',-1),names.get(n,'set' if n in static else None))
    if not group or o.type not in {'MESH','CURVE'}:continue
    # Round previews at game distance do not need 4 bevel loops.
    for k in o.modifiers:
        if k.type=='BEVEL':k.segments=2
    bpy.context.view_layer.update()
    transform=o.matrix_world.copy()
    o.parent=None
    o.matrix_world=transform
    o.name=f'{group}__{n}'
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(root/'physics/room.glb'),export_format='GLB',
                         use_selection=True,export_apply=True,export_texcoords=False,
                         export_cameras=False,export_lights=False,export_animations=False)
