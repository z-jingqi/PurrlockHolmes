"""Update only the fork in the room atlas and bake a 2x draw texture."""
import json, re, sys
from pathlib import Path
from PIL import Image
from fork_shadow import make_shadow

root=Path(__file__).resolve().parents[1]
stage=Path(sys.argv[1])
l,t,r,b=json.loads((stage/"fork.json").read_text())["bounds"]
source=Image.open(stage/"fork.png").convert("RGBA")
size=(r-l,b-t)
assert source.size==tuple(v*4 for v in size)
im=source.resize(size,Image.Resampling.LANCZOS)
alpha=im.getchannel("A")
bounds=alpha.point(lambda v:255 if v>=5 else 0).getbbox()
x,y,rr,bb=bounds
box=(max(0,x-2),max(0,y-2),min(size[0],rr+2),min(size[1],bb+2))
part=im.crop(box)
draw=source.crop(tuple(v*4 for v in box)).resize(
    tuple(v*2 for v in part.size),Image.Resampling.LANCZOS)
draw.save(root/"assets"/"fork-detail.png",optimize=True)
make_shadow(draw,root/"assets"/"fork-shadow.png")
atlas_file=root/"assets"/"tea-sprites.webp"
atlas=Image.open(atlas_file).convert("RGBA")
frames_file=root/"game"/"tea_frames.gd"
frames=frames_file.read_text()
fork=r'"fork": \[Rect2\((\d+),(\d+),(\d+),(\d+)\),Vector2\((\d+),(\d+)\)\]'
old=list(map(int,re.search(fork,frames).groups()))
old_rect=(old[0],old[1],old[0]+old[2],old[1]+old[3])
atlas.paste((0,0,0,0),old_rect)
# A dedicated tile after the last short plant row; leave margin for the filter.
i,j=448,665
assert i+part.width<atlas.width and j+part.height<atlas.height
assert not atlas.crop((i-2,j-2,i+part.width+2,j+part.height+2)).getchannel("A").getbbox()
atlas.paste(part,(i,j))
atlas.save(atlas_file,lossless=True,method=6)
left,top=l+box[0],t+box[1]
frames_file.write_text(re.sub(fork,f'"fork": [Rect2({i},{j},{part.width},{part.height}),Vector2({left},{top})]',frames))
