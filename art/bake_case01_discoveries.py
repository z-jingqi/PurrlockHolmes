"""Build and bake the Case 01 discovery props at the locked room camera.

CASE01_STAGE=/tmp/case01 blender -b art/room.blend -P art/bake_case01_discoveries.py
python3 art/pack_case01_discoveries.py /tmp/case01
"""
import os,sys,json,math
from pathlib import Path
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from tea_assets import Studio,glaze,instance
scene=bpy.context.scene
cam=scene.camera
fixed=list(scene.objects)
stage=Path(os.environ["CASE01_STAGE"]);stage.mkdir(parents=True,exist_ok=True)
W,H=1200,896

def at(px,py,z):
    frame=cam.data.view_frame(scene=scene)
    u=[v.x for v in frame];v=[v.y for v in frame]
    local=Vector((min(u)+(max(u)-min(u))*px/W,max(v)-(max(v)-min(v))*py/H,frame[0].z))
    ray=cam.matrix_world.to_3x3()@local
    return cam.location+ray*((z-cam.location.z)/ray.z)

studio=Studio()
def prop(key,x,y,z,yaw,builder,scale=1.):
    col=bpy.data.collections.new("Case 01 · "+key)
    studio.collection=col;builder(studio)
    ob=instance(key,col,at(x,y,z),yaw)
    ob.scale=(scale,)*3
    return ob

def turn(s,name,profile,material):
    return s.lathe(name,profile,material)
def pitcher(s):
    turn(s,"Creamer · glazed foot and hollow mouth",[(.002,.023),(.115,.015),(.146,.02),(.17,.086),(.189,.19),(.17,.279),(.136,.313),(.108,.318),(.103,.293),(.141,.19),(.12,.078),(.002,.065)],s.ivory)
    s.tube("Creamer · pulled handle",[(.14,0,.11),(.22,0,.12),(.256,0,.196),(.22,0,.268),(.135,0,.257)],[.022,.021,.022,.024,.024],s.ivory)
    s.tube("Creamer · open lip",[(-.098,0,.256),(-.15,0,.279),(-.202,0,.295),(-.211,0,.333)],[.068,.058,.048,.040],s.ivory,hollow=.36)
    s.band("Creamer · peach ribbon",.177,.224,.007,s.peach)
def blade(s):
    # One slightly cambered, rounded butter blade with a porcelain grip.
    rows=[(-.44,.012),(-.42,.051),(-.23,.054),(-.04,.044),(.05,.032),(.14,.049),(.36,.065),(.43,.044),(.45,.006)]
    vs=[(sgn*w,y,.022+.012*(y+.44)) for y,w in rows for sgn in [-1,1]]
    b=s.mesh("Butter knife · blunt taper",vs,[(i,i+1,i+3,i+2) for i in range(0,len(vs)-2,2)],s.steel)
    b.modifiers.new("Steel stock","SOLIDIFY").thickness=.014
    e=b.modifiers.new("Soft bevel","BEVEL");e.width=.006;e.segments=3
    s.tube("Butter knife · celadon grip",[(0,-.43,.037),(0,-.37,.038),(0,-.22,.037),(0,-.08,.032)],[.023,.043,.044,.031],s.sky,axis=(1,0,0))
def spoon(s):
    s.tube("Teaspoon · rounded steel handle",[(0,-.36,.035),(0,-.27,.04),(0,-.02,.037),(0,.14,.034)],[.025,.035,.025,.028],s.steel,axis=(1,0,0))
    bowl=turn(s,"Teaspoon · hollow oval bowl",[(.002,.011),(.064,.014),(.116,.039),(.129,.071),(.121,.079),(.106,.062),(.071,.033),(.002,.029)],s.steel)
    bowl.location.y=.22;bowl.scale.y=1.42
def eggcup(s):
    turn(s,"Egg cup · turned foot, stem and glazed bowl",[(.002,.015),(.095,.012),(.123,.014),(.145,.027),(.144,.047),(.083,.065),(.061,.099),(.071,.147),(.121,.19),(.150,.245),(.152,.29),(.142,.304),(.123,.299),(.124,.274),(.116,.231),(.076,.188),(.002,.171)],s.sky)
    s.band("Egg cup · cream rim",.145,.287,.009,s.ivory)
def cloth(s):
    c=glaze("Case 01 · woven dusty peach linen","d0a593",.87)
    hem=glaze("Case 01 · warm fine hem","edd3b7",.9)
    n,m=23,17;v=[]
    for j in range(m):
        y=(j/(m-1)-.5)*.58
        for i in range(n):
            x=(i/(n-1)-.5)*.89
            f=.019+.074*math.exp(-((x+.07)/.28)**2-((y+.03)/.24)**2)+.015*math.cos(15*x+2*y)**2
            v.append((x+.017*math.sin(y*9),y+.02*math.cos(x*7),f))
    faces=[(j*n+i,j*n+i+1,(j+1)*n+i+1,(j+1)*n+i) for j in range(m-1) for i in range(n-1)]
    s.mesh("Folded cloth · close drape",v,faces,c).modifiers.new("Linen thickness","SOLIDIFY").thickness=.014
    s.tube("Stitched edge",[v[i+1] for i in range(n-2)],[.007]*(n-2),hem,sections=8,samples=1)
def tin(s):
    # A storage canister, not part of the collection objective.
    turn(s,"Sewing tin · curved painted wall",[(.002,.014),(.213,.011),(.247,.022),(.253,.049),(.25,.269),(.238,.290),(.215,.289),(.216,.057),(.002,.057)],s.peach)
    s.band("Sewing tin · pale shoulder band",.252,.23,.012,s.ivory)
def lid(s):
    turn(s,"Lift-off tin lid",[(.002,.265),(.247,.265),(.263,.278),(.263,.312),(.249,.327),(.002,.329)],s.peach)
    turn(s,"Lid · carved wooden pull",[(.002,.329),(.061,.33),(.044,.352),(.055,.385),(.044,.407),(.002,.408)],s.honey)
    s.band("Seam · around the removable lid",.256,.304,.009,s.ivory)
# Draw coordinates are 1× background pixels; z is the corresponding room support plane.
objects={
 "creamer":prop("creamer",319,474,.062,.36,pitcher),
 "butter_knife":prop("butter_knife",529,596,.137,-1.15,blade,1.05),
 "teaspoon":prop("teaspoon",413,591,.137,-.67,spoon,1.08),
 "napkin_cover":prop("napkin_cover",405,590,.139,-.21,cloth,1.03),
 "egg_cup":prop("egg_cup",732,450,.062,.08,eggcup,1.13),
 "tin_base":prop("tin_base",763,434,.062,.08,tin,1.37),
 "tin_lid":prop("tin_lid",763,434,.062,.08,lid,1.37),
}
for o in fixed:
    if o.type in ("MESH","CURVE") or o.instance_type=="COLLECTION":o.hide_render=True
bpy.context.view_layer.update()
scene.render.resolution_x=W;scene.render.resolution_y=H;scene.render.resolution_percentage=300
scene.render.use_border=True;scene.render.use_crop_to_border=True;scene.render.film_transparent=True
scene.render.image_settings.file_format="PNG";scene.render.image_settings.color_mode="RGBA"
scene.render.threads_mode="FIXED";scene.render.threads=8
scene.cycles.samples=96;scene.cycles.adaptive_threshold=.018;scene.cycles.use_denoising=False
meta={}
for key,ob in objects.items():
    for o in objects.values():o.hide_render=o!=ob
    ps=[world_to_camera_view(scene,cam,ob.matrix_world@obj.matrix_world@Vector(v)) for obj in ob.instance_collection.objects for v in obj.bound_box]
    l=math.floor(min(p.x for p in ps)*W)-5;r=math.ceil(max(p.x for p in ps)*W)+5
    t=math.floor(min(1-p.y for p in ps)*H)-5;b=math.ceil(max(1-p.y for p in ps)*H)+5
    scene.render.border_min_x=(l+.01)/W;scene.render.border_max_x=(r+.01)/W
    scene.render.border_min_y=(H-b+.01)/H;scene.render.border_max_y=(H-t+.01)/H
    scene.render.filepath=str(stage/(key+".png"));bpy.ops.render.render(write_still=True)
    meta[key]=[l,t,r,b]
(stage/"bounds.json").write_text(json.dumps(meta))
