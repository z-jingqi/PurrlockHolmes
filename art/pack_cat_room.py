"""Prepare the room couch plate and the cat's open- and closed-eye surface maps.

Inputs: clean sofa PNG from clear_room_cat.py, approved edge-extended UV appearance.
Requires Pillow, Numpy and OpenCV.
"""
from pathlib import Path
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

assets = Path(__file__).resolve().parents[1]/"assets"
sofa_file, source = map(Path, sys.argv[1:])
room = Image.open(assets/"room.webp").convert("RGB")
sofa = Image.open(sofa_file).convert("RGB")
l,t,r,b = 380,231,530,354
assert sofa.size == (r-l,b-t)
# Denoise the baked sofa without changing its color or elsewhere in the room.
clean = Image.fromarray(cv2.fastNlMeansDenoisingColored(np.asarray(sofa),None,3.4,3.2,7,17))
sofa = Image.blend(sofa, clean, .87).convert("RGBA")
# Soft contact under the broad torso, tail and planted paws; no hard outline.
shade = Image.new("RGBA",sofa.size)
for x,y,rx,ry,alpha,blur in [(473,313,42,11,63,5.5),(510,310,13,5,40,3.1),
                             (415,328,12,3,73,2.3),(450,330,11,3,71,2.3)]:
    layer = Image.new("L",sofa.size)
    ImageDraw.Draw(layer).ellipse((x-l-rx,y-t-ry,x-l+rx,y-t+ry),fill=alpha)
    ink = Image.new("RGBA",sofa.size,(45,47,37,0))
    ink.putalpha(layer.filter(ImageFilter.GaussianBlur(blur)))
    shade = Image.alpha_composite(shade,ink)
sofa = Image.alpha_composite(sofa,shade).convert("RGB")
feather = Image.new("L",sofa.size)
ImageDraw.Draw(feather).rectangle((9,7,142,117),fill=255)
feather = feather.filter(ImageFilter.GaussianBlur(3))
room.paste(sofa,(l,t),feather)
room.save(assets/"room.webp",lossless=True,method=6)

idle = Image.open(source).convert("RGB")
assert idle.size == (1254,1254)
rgb = np.asarray(idle)
mask = np.zeros(rgb.shape[:2],dtype=np.uint8)
eyes = [(281,592,26,31),(508,620,30,32)]
for x,y,rx,ry in eyes:
    cv2.ellipse(mask,(x,y),(rx,ry),0,0,360,255,-1)
clean = cv2.inpaint(rgb,mask,13,cv2.INPAINT_TELEA)
weight = cv2.GaussianBlur(mask,(0,0),4).astype(np.float32)[:,:,None]/255
closed = np.uint8(np.rint(rgb*(1-weight)+clean*weight))
lid = Image.new("RGBA",idle.size)
draw = ImageDraw.Draw(lid)
for x,y,rx,_ in eyes:
    pts = [(round(x+rx*.78*s/16),round(y+4+8*(1-(s/16)**2))) for s in range(-16,17)]
    draw.line(pts,fill=(112,71,52,228),width=6,joint="curve")
closed = Image.alpha_composite(Image.fromarray(closed).convert("RGBA"),lid.filter(ImageFilter.GaussianBlur(1.2))).convert("RGB")
for name, im in [("cat-look",idle),("cat-blink",closed)]:
    im.resize((512,512),Image.Resampling.LANCZOS).save(assets/(name+".webp"),quality=94,method=6)
