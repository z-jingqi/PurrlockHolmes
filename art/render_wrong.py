"""Bake hit silhouettes and clean backing for recognized non-target props."""
from pathlib import Path
import os, re, sys
import bpy
root=Path(bpy.data.filepath).resolve().parents[1]
sys.path.insert(0,str(root/'art'))
from bake_pick import bake
out=Path(os.environ.get("PURR_PICKUP_DIR","/tmp/purr-pickup"))
out.mkdir(exist_ok=True,parents=True)
s=bpy.context.scene
for o in s.objects:
    n=re.sub(r'\.\d{3,}$','',o.name)
    i=0
    if n.startswith('Cat '):i=1
    elif n in ('Blush pillow','Butter pillow'):i=2 if n.startswith('Blush') else 3
    elif n in ('Storybook','Book label'):i=4
    elif n=='Notebook':i=5
    elif n.startswith('Clementine'):i=6
    elif n.startswith('Toy car'):i=7
    elif n=='Wooden toy block':
        x=o.location.x
        i=8 if x<0 else 9 if x<4.5 else 10 if x<4.8 else 11
    elif n.startswith('House slipper') or n=='Slipper upper':i=12 if o.location.x < -4.80 else 13
    elif n in ('Basket','Basket piping','Reed bands','Basket fabric'):i=14
    elif n in ('Red balloon','Balloon knot'):i=15
    elif n in ('Floor magazine','Magazine art'):i=16
    elif n in ('Plant pot','Pot earth','Rubber plant leaf','Plant stalk'):
        x=o.matrix_world.translation.x
        if n=='Plant stalk':x=o.data.splines[0].points[0].co.x
        i=17 if x<0 else 18
    elif n in ('Little book','Bookend'):i=19
    if i in (1,2,3,17,18):i=0
    o['wrong_id']=i
bake(root/'assets/wrong.png',key='wrong_id',stride=8)
for o in s.objects:
    if o.get('wrong_id',0):o.hide_render=True
s.render.filepath=str(out/'wrong-clean.png')
bpy.ops.render.render(write_still=True)
