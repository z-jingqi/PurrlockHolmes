from pathlib import Path
from PIL import Image, ImageFilter
import os,json
root=Path(__file__).resolve().parents[1]
out=Path(os.environ.get("PURR_PICKUP_DIR","/tmp/purr-pickup"))
before=Image.open(root/'assets/room.webp').convert('RGBA')
after=Image.open(out/'wrong-clean.png').convert('RGBA')
mask=Image.open(root/'assets/wrong.png').getchannel('R')
atlas=Image.new('RGBA',(960,1300))
x=y=row=0
items={}
for i in (*range(4,17),19):
    a=mask.point(lambda t:255 if t==i*8 else 0); bbox=a.getbbox()
    if bbox is None:continue
    l,t,r,b=bbox; box=(l-3,t-3,r+3,b+3)
    cut=a.crop(box)
    patch=after.crop(box); patch.putalpha(cut.filter(ImageFilter.MaxFilter(5)))
    sprite=before.crop(box);sprite.putalpha(cut)
    data={'origin':[box[0],box[1]]}
    for kind,tile in [('patch',patch),('sprite',sprite)]:
        if x+tile.width+3>atlas.width: x=0;y+=row+3;row=0
        assert y+tile.height<=atlas.height
        atlas.paste(tile,(x,y));data[kind]=[x,y,tile.width,tile.height]
        x+=tile.width+3;row=max(row,tile.height)
    items[str(i)]=data
assert len(items)>=14,items
atlas.crop((0,0,atlas.width,y+row)).save(root/'assets/wrong.webp',quality=90,method=6)
data=json.dumps(items,separators=(',',':'))
(root/'assets/wrong.json').write_text(data+'\n')
(root/'assets/wrong_data.gd').write_text('# Generated.\nconst ITEMS := '+data+'\n')
