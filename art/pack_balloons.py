"""Refresh only three balloon crops and their attachment markers; preserve every other atlas slot."""
import json, re, sys
from pathlib import Path
from PIL import Image

root=Path(__file__).resolve().parents[1]
stage=Path(sys.argv[1])
metadata=json.loads((stage/"balloons.json").read_text())
atlas_file=root/"assets"/"tea-sprites.webp"
atlas=Image.open(atlas_file).convert("RGBA")
frames_file=root/"game"/"tea_frames.gd"
frames=frames_file.read_text()
# Existing positions are locked unless there isn't enough free padding.
# The official atlas has this run of three adjacent slots with a 6 px gutter.
def frame_match(key):
    return re.search(r'"'+key+r'": \[Rect2\((\d+),(\d+),(\d+),(\d+)\),Vector2\((\d+),(\d+)\)\]',frames)
slots={}
for key in metadata:
    i,j,w,h,*_=map(int,frame_match(key).groups())
    slots[key]=(i,j)
    atlas.paste((0,0,0,0),(i,j,i+w,j+h))
# Preserve not just occupied pixels but logical frame rectangles and a one-pixel sampling margin.
occupied=Image.new("L",atlas.size)
for key,x,y,w,h in re.findall(r'"([^"]+)": \[Rect2\((\d+),(\d+),(\d+),(\d+)\),Vector2',frames):
    if key not in metadata:
        x,y,w,h=map(int,(x,y,w,h))
        occupied.paste(255,(x-1,y-1,x+w+1,y+h+1))
for key,data in metadata.items():
    l,t,r,b=data["bounds"]
    source=Image.open(stage/(key+".png")).convert("RGBA")
    assert source.size==((r-l)*3,(b-t)*3)
    reduced=source.resize((r-l,b-t),Image.Resampling.LANCZOS)
    x,y,a,z=reduced.getchannel("A").point(lambda v:255 if v>=5 else 0).getbbox()
    left,top,right,bottom=max(0,x-2),max(0,y-2),min(r-l,a+2),min(b-t,z+2)
    part=reduced.crop((left,top,right,bottom))
    i,j=slots[key]
    w,h=part.size
    assert i+w+1 < atlas.width and j+h+1 < atlas.height
    assert not occupied.crop((i-1,j-1,i+w+1,j+h+1)).getbbox(),(key,part.size)
    occupied.paste(255,(i,j,i+w,j+h))
    atlas.paste(part,(i,j))
    current=frame_match(key).group()
    frame=f'"{key}": [Rect2({i},{j},{w},{h}),Vector2({l+left},{t+top})]'
    frames=frames.replace(current,frame)
    x,y=data["tip"]
    frames,count=re.subn(r'"'+key+r'": Vector2\([^\n]+?\)',f'"{key}": Vector2({x:.2f},{y:.2f})',frames)
    assert count==1
atlas.save(atlas_file,lossless=True,method=6,exact=True)
frames_file.write_text(frames)
