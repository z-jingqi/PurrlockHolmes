"""Keep the planted handle's shadow close; the raised shoulders cast it farther."""
from PIL import Image, ImageFilter

def make_shadow(appearance, output):
    alpha=appearance.getchannel("A")
    # The fork points to the right in room space. Offset by 0.5–3 logical
    # pixels from handle to head, then give the shadow a soft penumbra.
    mask=Image.new("L",(alpha.width+24,alpha.height+24))
    for x in range(alpha.width):
        ratio=x/max(1,alpha.width-1)
        offset=round(1+5*ratio**1.6)
        column=alpha.crop((x,0,x+1,alpha.height))
        mask.paste(column,(12+x+round(ratio),12+offset))
    shade=Image.new("RGBA",mask.size,(65,46,32,0))
    shade.putalpha(mask.filter(ImageFilter.GaussianBlur(2.5)).point(lambda a:round(a*.31)))
    shade.save(output,optimize=True)
