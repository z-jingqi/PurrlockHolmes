"""Prepare the 2× room plate, retaining soft shadows and the approved framing."""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

root=Path(__file__).resolve().parents[1]
base=Image.open(sys.argv[1]).convert("RGB")
assert base.size==(2400,1792)
pixels=np.asarray(base)
# Keep shapes on the true 2x grid. Denoise interiors, without smearing
# shadows and seams across neighboring surfaces or adding dark outlines.
soft=cv2.fastNlMeansDenoisingColored(pixels,None,3.1,3.0,7,13)
base=Image.blend(base,Image.fromarray(soft),.84)
# Match the level cat's baked contact on the seat: only the cat model moves.
l,t,r,b=(380,231,530,354)
tile=base.crop((l*2,t*2,r*2,b*2)).convert("RGBA")
for x,y,rx,ry,alpha,blur in [(473,313,42,11,63,5.5),(510,310,13,5,40,3.1),
                             (415,328,12,3,73,2.3),(450,330,11,3,71,2.3)]:
    layer=Image.new("L",tile.size)
    ImageDraw.Draw(layer).ellipse(tuple(2*v for v in (x-l-rx,y-t-ry,x-l+rx,y-t+ry)),fill=alpha)
    ink=Image.new("RGBA",tile.size,(45,47,37,0))
    ink.putalpha(layer.filter(ImageFilter.GaussianBlur(blur*2)))
    tile=Image.alpha_composite(tile,ink)
base.paste(tile.convert("RGB"),(l*2,t*2))
base.save(root/"assets"/"room.webp",quality=95,method=6)
