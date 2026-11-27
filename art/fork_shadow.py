"""Keep the planted handle's shadow close; the raised shoulders cast it farther."""
from bisect import bisect_right
from PIL import Image, ImageFilter

def make_shadow(appearance, output, profile=None):
    profile=sorted(profile or [])
    xp=[x for x,z in profile]

    def height_at(x):
        i=bisect_right(xp,x)
        if i==0:return profile[0][1]
        if i==len(xp):return profile[-1][1]
        a,za=profile[i-1]
        b,zb=profile[i]
        return za+(zb-za)*(x-a)/(b-a)

    alpha=appearance.getchannel("A")
    # The fork points to the right in room space. Offset by 0.5–3 logical
    # pixels from handle to head, then give the shadow a soft penumbra.
    mask=Image.new("L",(alpha.width+24,alpha.height+24))
    for x in range(alpha.width):
        ratio=x/max(1,alpha.width-1)
        offset=round(1+32*max(0,height_at(x)-.016)) if profile else round(1+5*ratio**1.6)
        column=alpha.crop((x,0,x+1,alpha.height))
        mask.paste(column,(12+x+round(ratio),12+offset))
    shade=Image.new("RGBA",mask.size,(65,46,32,0))
    shade.putalpha(mask.filter(ImageFilter.GaussianBlur(2.5)).point(lambda a:round(a*.31)))
    shade.save(output,optimize=True)
