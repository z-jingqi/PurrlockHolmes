"""Pack the final render atlas with a padded edge for filtering."""
from pathlib import Path
from PIL import Image
import sys,json
root=Path(__file__).resolve().parents[1];stage=Path(sys.argv[1])
atlas=Image.new("RGBA",(512,128))
x,y,h=2,2,0
frames={}
for key,(l,t,r,b) in json.loads((stage/"bounds.json").read_text()).items():
    im=Image.open(stage/(key+".png")).convert("RGBA").resize((r-l,b-t),Image.Resampling.LANCZOS)
    a=im.getchannel("A").point(lambda v:255 if v>8 else 0).getbbox()
    im=im.crop(a)
    if x+im.width+2>atlas.width:x,y,h=2,y+h+4,0
    assert y+im.height+2<=atlas.height
    atlas.paste(im,(x,y))
    frames[key]=(x,y,im.width,im.height,l+a[0],t+a[1])
    x+=im.width+4;h=max(h,im.height)
atlas.save(root/"assets"/"case01-discoveries.webp",lossless=True,method=6)
p=root/"game"/"case01_discovery_frames.gd"
with p.open("w") as f:
    f.write("extends RefCounted\n## Baked alignment with the fixed room art. Regenerate with art/pack_case01_discoveries.py.\nconst FRAMES := {\n")
    for key,(x,y,w,h,l,t) in frames.items():f.write(f'\t"{key}": [Rect2({x},{y},{w},{h}),Vector2({l},{t})],\n')
    f.write("}\n")
