"""Bake a smooth tapered white-gold radial shaft for the two hint renderers."""
from pathlib import Path
from math import exp
from PIL import Image

def smooth(a,b,v):
    p=max(0., min(1.,(v-a)/(b-a)))
    return p*p*(3-2*p)

im=Image.new('RGBA',(160,56))
for y in range(im.height):
    for x in range(im.width):
        t=(x+.5)/im.width
        d=abs(y+.5-im.height*.5)
        longitudinal=smooth(0,.075,t)*(1-smooth(.64,1,t))
        inner=exp(-.5*(d/(1.9+2.0*t-1.6*t*t))**2)
        shaft=exp(-.5*(d/(2.0+6.2*t))**2)
        haze=exp(-.5*(d/(3.2+8.0*t))**2)
        border=1-smooth(18,28,d)
        alpha=min(1.,longitudinal*(.73*inner+.32*shaft+.26*haze)*border)
        white=min(1.,inner*.86+shaft*.20)
        rgb=(255,round(187+65*white),round(100+140*white))
        im.putpixel((x,y),(*rgb,round(255*alpha)))
im.save(Path(__file__).resolve().parents[1]/'assets/hint-ray.png',optimize=True)
