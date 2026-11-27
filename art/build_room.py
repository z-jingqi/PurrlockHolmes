"""Build the editable Purrlock Holmes diorama. Blender 4.3+."""
from pathlib import Path
import bpy, math, sys
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'art'))
from room_props import scene_props, place, finish_material
from hero_props import BALLOON_DESIGNS,balloon,balloon_string,cat,pillow
from tea_assets import Studio
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
def color(h):
    return tuple((v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4) for v in [int(h[i:i+2],16)/255 for i in (0,2,4)])
def mat(name,h):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color(h),1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Roughness'].default_value=.82
    return m
cream=mat('Milk','fff0da'); wood=mat('Honey beech','d99c68'); honey=mat('Pale oak','edbf86'); dark=mat('Cocoa ink','52394a'); mint=mat('Pistachio','a6cba5'); jade=mat('Leaf','659879'); pink=mat('Peach','ee9e9d'); red=mat('Berry','d96066'); blue=mat('Cloud blue','83abc7'); gold=mat('Butterscotch','edb95f'); sand=mat('Rice paper','e8d3b6'); silver=mat('Soft pewter','a5b8bd'); terr=mat('Terracotta','d58c6d'); glass=mat('Window blue','bbdce3'); wall=mat('Barley wall','eee1c6')
def finish(o,name,m):
    o.name=name;o.data.materials.append(m)
    return o
def box(n,p,d,m,b=.07,az=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.rotation_euler.z=az
    if b:
        k=o.modifiers.new('Soft corners','BEVEL');k.width=b;k.segments=4
        o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return finish(o,n,m)
def ell(n,p,d,m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=p);o=bpy.context.object;o.scale=d
    for f in o.data.polygons:f.use_smooth=True
    return finish(o,n,m)
def cyl(n,p,r,depth,m,top=None):
    bpy.ops.mesh.primitive_cone_add(vertices=48,radius1=r,radius2=(r if top is None else top),depth=depth,location=p)
    o=bpy.context.object;k=o.modifiers.new('Round rim','BEVEL');k.width=.025;k.segments=3;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    for f in o.data.polygons:f.use_smooth=True
    return finish(o,n,m)
def ring(n,p,R,r,m,vertical=False):
    bpy.ops.mesh.primitive_torus_add(location=p,major_segments=40,minor_segments=10,major_radius=R,minor_radius=r)
    o=bpy.context.object
    if vertical:o.rotation_euler.x=math.pi/2
    for f in o.data.polygons:f.use_smooth=True
    return finish(o,n,m)
def line(n,pts,r,m):
    c=bpy.data.curves.new(n,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=3;s=c.splines.new('POLY');s.points.add(len(pts)-1)
    for k,p in zip(s.points,pts):k.co=(*p,1)
    o=bpy.data.objects.new(n,c);bpy.context.collection.objects.link(o);return finish(o,n,m)
# A closed book reads by silhouette and structure, even without tiny simulated text.
book_pages=finish_material("Books • cream cut paper","ead9bd",.89)
book_edge=finish_material("Books • pale leaf edges","c9b390",.83)
def book(name,p,w,d,h,tint,yaw,emblem):
    x,y,z=p
    cs,sn=math.cos(yaw),math.sin(yaw)
    def world(u,v,t):return (x+cs*u-sn*v,y+sn*u+cs*v,z+t)
    cover=finish_material(name+" • paperboard",tint,.73,.16)
    spine=finish_material(name+" • cloth spine",tint,.86,.26)
    box(name+' bound lower cover',world(0,0,.009),(w,d,.018),cover,.009,yaw)
    box(name+' ivory paper block',world(.011,0,h*.51),(w-.060,d-.038,h-.033),book_pages,.014,yaw)
    box(name+' bound upper cover',world(0,0,h-.011),(w,d,.022),cover,.010,yaw)
    box(name+' bowed book spine',world(-w*.468,0,h*.505),(.055,d-.014,h*.94),spine,.022,yaw)
    for k in range(3):
        zh=h*(.32+k*.14)
        box(name+' fore edge pages',world(w*.484-.011,0,zh),(.004,d*.84,.0028),book_edge,.0014,yaw)
        box(name+' foot edge pages',world(.012,-d*.5+.017,zh),(w*.80,.005,.0028),book_edge,.0014,yaw)
    box(name+' small cover label',world(.019,.026,h+.003),(w*.55,d*.50,.007),cream,.011,yaw)
    if emblem=="flower":
        for i in range(5):
            a=math.tau*i/5
            ell(name+' painted petal',world(.012+.043*math.cos(a),.026+.043*math.sin(a),h+.009),
                (.020,.020,.003),terr)
        ell(name+' painted flower center',world(.012,.026,h+.011),(.018,.018,.003),gold)
    elif emblem=="leaf":
        line(name+' painted twig',[world(-.060,-.022,h+.009),world(.013,.026,h+.009),world(.076,.060,h+.009)],.007,jade)
        for u,v in [(-.024,.025),(.025,.012),(.057,.058)]:
            o=ell(name+' painted tiny leaf',world(u,v,h+.009),(.025,.014,.003),jade);o.rotation_euler.z=yaw+.42
    else:
        for i,a in enumerate([.12,.07,.10]):
            box(name+' cover mark',world(.025,.069-i*.042,h+.009),(a,.011,.003),blue,.002,yaw)
# envelope and room
box('Diorama plinth',(0,0,-.26),(12.75,9.55,.48),honey,.26)
for j in range(12):
    box('Birch floorboard',(-5.9+j*1.067,0,0),(1.055,9.37,.12),[honey,honey,sand][j%3],.017)
box('Back wall',(0,4.57,2.08),(12.5,.24,4.34),wall,.12)
box('Left return wall',(-6.18,2.58,2.08),(.21,4,4.34),cream,.10)
box('Back skirting',(0,4.4,.22),(12.4,.13,.25),honey)
box('Picture frame',(-2.35,4.41,3.25),(1.30,.13,1.15),wood)
box('Picture print',(-2.35,4.33,3.25),(1.1,.06,.94),cream)
for x,z,r,m in [(-2.63,3.25,.21,terr),(-2.31,3.31,.24,mint),(-2.03,3.13,.12,gold)]:
    o=ell('Printed clouds',(x,4.29,z),(r,.025,r*.64),m)
box('Window frame',(2.35,4.40,2.96),(3.7,.18,2.25),honey,.08)
box('Window pane',(2.35,4.29,2.96),(3.44,.05,2.00),glass,.045)
for x,z,k in [(1.28,3.35,.32),(2.9,3.51,.29),(3.21,3.40,.25)]:
    ell('Cloud through glass',(x,4.248,z),(k,.022,k*.45),cream)
box('Window crossbar',(2.35,4.20,2.96),(3.5,.09,.10),cream,.024)
box('Window post',(2.35,4.20,2.96),(.10,.09,2.02),cream,.024)
box('Window sill',(2.35,4.15,1.87),(3.85,.49,.14),honey)
curtain=finish_material("Curtain • woven warm ivory","fff0dc",.88,.32)
curtain_hem=finish_material("Curtain • sewn edge","dfc9ad",.88,.24)
for xc,left in [(.54,True),(4.17,False)]:
    verts=[];faces=[];nx,nz=49,25
    for j in range(nz):
        t=j/(nz-1)
        for i in range(nx):
            u=i/(nx-1)
            w=.38+.12*(1-t)**2
            x=xc+(u-.5)*w+(.055 if left else -.055)*math.sin(math.pi*t)
            y=4.052+.068*math.cos(8*math.pi*u+.28*t)*(1-.23*t)
            z=2.27+1.75*t+.048*(1-t)**3*math.cos(8*math.pi*u)
            verts.append((x,y,z))
    for j in range(nz-1):
        for i in range(nx-1):
            q=j*nx+i;faces.append((q,q+1,q+nx+1,q+nx))
    tailor=Studio.__new__(Studio);tailor.collection=bpy.context.collection
    o=tailor.mesh("Continuous folded curtain",verts,faces,curtain)
    md=o.modifiers.new("Folded cloth edge","SOLIDIFY");md.thickness=.027
    line("Curtain lower sewn hem",verts[:nx],.013,curtain_hem)
    for i in [4,14,24,34,44]:
        x=verts[(nz-1)*nx+i][0]
        ring('Fabric curtain loop',(x,4.06,4.043),.042,.010,curtain_hem,vertical=True)
rod=finish_material("Curtain rod • champagne bronze","bc9c74",.47)
line('Curtain rod',[(.28,4.078,4.066),(4.43,4.078,4.066)],.036,rod)
for x in [.264,4.447]:
    ell('Curtain rod end',(x,4.078,4.066),(.066,.052,.052),rod)
# couch, rug, low table
for x in [-4.95,-2.05]:
    for y in [1.50,3.12]:cyl('Sofa foot',(x,y,.26),.11,.45,wood)
box('Sofa base',(-3.49,2.32,.67),(3.75,2.1,.67),jade,.24)
box('Sofa back',(-3.49,3.20,1.37),(3.75,.49,1.87),mint,.22)
for x in [-4.33,-2.64]:
    box('Seat cushion',(x,2.12,1.02),(1.58,1.48,.31),mint,.13)
for x in [-5.26,-1.72]:box('Sofa arm',(x,2.25,1.17),(.42,1.93,.98),mint,.19)
pillow(bpy.context.collection,"Blush pillow",(-4.67,2.78,1.53),.401,.384,.210,-.12,-.19,"e4a4a3","bc8584")
pillow(bpy.context.collection,"Butter pillow",(-2.30,2.66,1.434),.335,.326,.174,.25,-.27,"e4be7a","bf985e")
box('Wool rug',(-.46,-1.07,.09),(6.65,5.18,.07),cream,.26)
for j in range(8):
    for y in [-3.49,1.34]:box('Rug stitched dash',(-3.31+j*.80,y,.134),(.38,.037,.011),terr,.004)
for x in [-1.73,1.48]:
    for y in [-1.76,.12]:cyl('Low table leg',(x,y,.486),.12,.72,wood,.16)
box('Tea table',(-.11,-.82,.89),(3.83,2.53,.22),honey,.22)
# A low wooden chair with a peach seat, beside the tea table.
cx, cy = -3.22, -.53
for dx in [-.46,.46]:
    for dy in [-.43,.43]:
        box('Chair leg',(cx+dx,cy+dy,.528),(.15,.15,.80),wood,.042)
box('Chair seat',(cx,cy,.94),(1.22,1.18,.16),honey,.074)
box('Chair cushion',(cx,cy-.02,1.07),(1.12,1.02,.17),pink,.105)
for dx in [-.48,.48]:
    box('Chair upright',(cx+dx,cy+.46,1.47),(.15,.145,1.15),wood,.048)
box('Chair back',(cx,cy+.46,1.88),(1.18,.18,.52),honey,.07)
book('Chair field guide',(cx+.08,cy-.06,1.155),.608,.466,.094,'a3ba9a',-.16,'leaf')
# Cabinet and accents
box('Sideboard',(3.84,2.78,.79),(3.20,1.14,1.43),wood,.12)
box('Sideboard top',(3.84,2.78,1.55),(3.38,1.31,.14),honey)
for x in [2.84,3.84,4.84]:
    box('Linen cupboard door',(x,2.19,.79),(.93,.115,1.19),cream)
    ell('Drawer pull',(x+.22,2.095,.83),(.073,.068,.073),wood)
# Four books in a short upright row, with wrapping covers and visible page tops.
for j,m in enumerate([mint,pink,blue,gold]):
    x=-.68+j*.148; y=2.89; h=.425-j*.037
    box('Upright book page block',(x,y,.071+h*.5),(.100,.37,h),book_pages,.013)
    for edge in [-.056,.056]:
        box('Upright bound cover',(x+edge,y,.065+h*.52),(.018,.40,h+.022),m,.008)
    box('Upright rounded spine',(x,y-.195,.066+h*.52),(.138,.043,h+.017),m,.018)
    for dz in [.066,h-.052]:
        box('Upright spine foil band',(x,y-.218,.066+dz),(.106,.005,.012),cream,.004)
box('Beech bookend foot',(-.84,2.89,.086),(.275,.41,.052),wood,.018)
box('Beech bookend upright',(-.789,2.89,.235),(.085,.36,.321),wood,.039)
props=scene_props()
place(props["clay_planter"],(-5.02,-.53,.064),-.22,1.07)
place(props["rubber_plant"],(-5.02,-.53,.064+.432*1.07),-.38,1.07)
place(props["celadon_planter"],(5.12,2.86,1.624),.22,.91)
place(props["lance_plant"],(5.12,2.86,1.624+.443*.91),.42,.91)
# Original sculpted room mascot, posed low on the sofa.
cat(bpy.context.collection,ell)
# Assorted non-target props: toy truck, books, slipper, basket, fruit, balloon
book('Blue storybook',(-1.34,-1.32,1.001),.765,.55,.101,'8caac0',-.24,'flower')
ell('Clementine',(.16,-.09,1.17),(.18,.18,.16),gold)
ell('Clementine leaf',(.155,-.05,1.32),(.095,.045,.023),jade)
# Different finishes remain legible at the real game camera, even without texture noise.
car_enamel=finish_material("Toy • smooth strawberry enamel","ce626c",.36,coat=.32)
car_cab=finish_material("Toy • rose enamel","df9a98",.43,coat=.2)
car_glass=finish_material("Toy • celadon windows","72929c",.30,coat=.26)
car_tire=finish_material("Toy • matte rubber","50404a",.84)
wheel_hub=finish_material("Toy • pale metal hubs","d7b89a",.44)
box('Toy car chassis',(3.39,-1.80,.31),(.91,.48,.26),car_enamel,.088)
box('Toy car cab',(3.52,-1.80,.49),(.48,.38,.29),car_cab,.083)
for y in [-2.002,-1.598]:
    for i in range(2):
        box('Toy car side window',(3.397+i*.191,y,.520),(.157,.019,.124),car_glass,.024)
box('Toy car windscreen',(3.284,-1.80,.526),(.024,.292,.135),car_glass,.027)
box('Toy car chrome front bumper',(2.94,-1.80,.266),(.066,.455,.073),wheel_hub,.030)
box('Toy car chrome rear bumper',(3.85,-1.80,.266),(.050,.437,.063),wheel_hub,.026)
for y in [-1.971,-1.629]:
    ell('Toy car headlight',(2.947,y,.354),(.024,.056,.056),cream)
for x in [3.11,3.69]:
    for y,sign in [(-2.031,-1),(-1.569,1)]:
        ell('Toy car shoulder tire',(x,y,.207),(.147,.071,.143),car_tire)
        ell('Toy car steel hub',(x,y+sign*.055,.207),(.082,.027,.081),wheel_hub)
        ell('Toy car center cap',(x,y+sign*.074,.207),(.029,.014,.029),car_cab)
for i,(x,y,m) in enumerate([(4.38,-1.30,blue),(4.92,-1.34,gold),(4.62,-1.04,pink)]):
    box('Wooden toy block',(x,y,.222),(.32,.33,.32),m,.036,.26)
    pz=.384
    if i==0:ring('Toy block printed circle',(x,y,pz),.078,.010,cream)
    elif i==1:line('Toy block printed triangle',[(x-.084,y-.052,pz),(x,y+.078,pz),(x+.084,y-.052,pz),(x-.084,y-.052,pz)],.010,cream)
    else:
        line('Toy block printed cross',[(x-.074,y-.062,pz),(x+.074,y+.062,pz)],.009,cream)
        line('Toy block printed cross',[(x-.074,y+.062,pz),(x+.074,y-.062,pz)],.009,cream)
place(props["felt_slippers"],(-4.80,-2.78,.062),.051)
# The bear is a non-interactive prop baked into the room; its paw fixes all three ribbons.
felt=finish_material("Bear • honey plush","cd996f",.88,.31)
pale=finish_material("Bear • short biscuit pile","edc8a3",.83,.28)
stitch=finish_material("Bear • chocolate embroidery","604448",.77,.20)
ribbon=finish_material("Bear • sage grosgrain ribbon","8aaa9a",.77,.26)
bx,by,bz=4.72,-.03,.064
def bear_part(name,p,scale,m):
    return ell("Plush bear • "+name,(bx+p[0],by+p[1],bz+p[2]),scale,m)
bear_part("seated rounded body",(0,.045,.335),(.38,.267,.335),felt)
bear_part("belly panel",(0,-.168,.335),(.236,.085,.231),pale)
bear_part("large head",(.014,-.005,.797),(.383,.295,.326),felt)
for sign in (-1,1):
    bear_part("round ear",(sign*.277,.012,1.037),(.146,.098,.147),felt)
    bear_part("recessed ear lining",(sign*.281,-.065,1.048),(.088,.027,.093),pale)
    bear_part("embroidered eye",(sign*.132+.014,-.271,.827),(.027,.018,.033),stitch)
    bear_part("foot",(sign*.233,-.18,.139),(.185,.204,.136),felt)
    bear_part("oval foot pad",(sign*.243,-.326,.162),(.115,.071,.078),pale)
bear_part("soft muzzle",(.016,-.254,.726),(.157,.078,.104),pale)
bear_part("stitched nose",(.015,-.325,.756),(.047,.019,.029),stitch)
line("Bear • stitched smile",[(bx-.032,by-.327,bz+.713),(bx+.014,by-.335,bz+.695),(bx+.063,by-.324,bz+.712)],.009,stitch)
o=bear_part("resting arm",(-.328,-.04,.361),(.148,.139,.25),felt);o.rotation_euler.y=.47
o=bear_part("raised holding arm",(.342,-.04,.450),(.143,.133,.249),felt);o.rotation_euler.y=-.53
bear_part("holding paw",(.443,-.119,.612),(.118,.111,.128),felt)
for sign in (-1,1):
    o=bear_part("neck bow wings",(sign*.101,-.242,.548),(.102,.040,.064),ribbon);o.rotation_euler.y=sign*.21
bear_part("neck bow knot",(0,-.279,.546),(.054,.037,.052),ribbon)
# Tiny knots and the tied band are baked; the lines above them are drawn as flexible 2D curves.
pin=(bx+.443,by-.233,bz+.642)
o=ring('Bear • ribbon tied on paw',(bx+.443,by-.124,bz+.644),.113,.013,ribbon)
o.rotation_euler.y=-.29
bear_part("ribbon knot at tether",(.443,-.233,.642),(.033,.018,.023),ribbon)
anchor=bpy.data.objects.new("Ribbon pin",None);bpy.context.scene.collection.objects.link(anchor)
anchor.location=pin;anchor["room_marker"]="tether"

# Individual latex silhouettes rendered as flat images in the shipped game.
cord_material=finish_material("Balloon • unbleached cotton cord","cdb493",.92,.22)
balloon_tips=[]
for i,(rgb,pos,scale,lean) in enumerate(BALLOON_DESIGNS):
    tip=balloon(bpy.context.collection,i,rgb,pos,scale,lean)
    balloon_tips.append(tip)
    marker=bpy.data.objects.new("Balloon string start "+str(i),None)
    bpy.context.scene.collection.objects.link(marker)
    marker.location=tip;marker["room_marker"]="balloon_"+str(i)
book('Floor picture book',(-2.67,-3.16,.128),.792,.562,.060,'a5bba4',-.18,'lines')
# Quiet room-model refinements: believable materials and furniture joinery.
for x in [2.84,3.84,4.84]:
    box('Cupboard inset panel',(x,2.119,.77),(.73,.034,.94),sand,.056)
    box('Cupboard central raised panel',(x,2.090,.77),(.62,.036,.83),cream,.056)
    ell('Turned cupboard pull',(x+.22,2.032,.84),(.062,.058,.065),wood)
for x in [2.46,5.20]:
    for y in [2.31,3.17]:
        box('Cabinet taper foot',(x,y,.14),(.23,.22,.155),wood,.045)
box('Cabinet apron',(3.84,2.20,.168),(3.07,.10,.16),wood,.045)
box('Cabinet softly rounded top lip',(3.84,2.18,1.539),(3.29,.13,.085),cream,.034)
for x in [-3.68,-2.76]:
    box('Chair side stretcher',(x,-.53,.32),(.085,.93,.11),honey,.024)
for x in [-3.40,-3.22,-3.04]:
    box('Chair curved back slat',(x,-.075,1.61),(.088,.09,.34),honey,.041)
for x in [-4.33,-2.64]:
    line('Seat front piping',[(x-.68,1.444,1.037),(x-.46,1.407,1.058),(x+.45,1.407,1.059),(x+.68,1.444,1.037)],.021,jade)
for x in [-3.77,2.85]:
    for j in range(12):
        box('Rug side embroidery',(x,-3.28+j*.38,.126),(.033,.14,.012),terr,.008)
line('Banner branch',[(-2.64,4.235,3.02),(-2.45,4.235,3.15),(-2.28,4.235,3.21)],.014,jade)
for x,z in [(-2.51,3.14),(-2.37,3.19),(-2.24,3.24)]:
    leaf=ell('Print leaf',(x,4.228,z),(.064,.015,.027),jade);leaf.rotation_euler.y=-.58
# Folded fabric napkin, clearly distinct from the thin book shapes.
napkin=finish_material("Napkin • brushed sage linen","b1c7a8",.91,.34)
napkin_hem=finish_material("Napkin • cream stitch","dfdec4",.86)
nap=Studio.__new__(Studio);nap.collection=bpy.context.collection
verts=[]; faces=[]; nx,ny=27,15
for j in range(ny):
    v=j/(ny-1)
    for i in range(nx):
        u=i/(nx-1)
        px=.65+u*.67+.035*math.sin(v*3.1)-.052*v
        py=-.12-v*.49+.063*math.sin(u*math.pi)-.09*u
        pz=1.018+.071*math.exp(-((v-.38)/.32)**2)+.019*math.cos(u*math.pi*2)*math.sin(v*math.pi)
        verts.append((px,py,pz))
for j in range(ny-1):
    for i in range(nx-1):
        a=j*nx+i;faces.append((a,a+nx,a+nx+1,a+1))
obj=nap.mesh("Sage linen draped folds",verts,faces,napkin)
obj.modifiers.new("Cloth edge thickness","SOLIDIFY").thickness=.022
line("Napkin rolled stitched hem",verts[-nx:],.013,napkin_hem)
# Magazine spines, pillow seams and stitched details maintain the quiet silhouette at full-frame.
paper=finish_material("Room • page edges","efe1c8",.91)
sofa_cloth=finish_material("Room • sage upholstery","a6cba5",.88,.33)
wood.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value=.46
honey.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value=.54
for o in bpy.context.scene.objects:
    if o.type=='MESH' and o.name.startswith(('Sofa back','Seat cushion','Sofa arm')):
        o.data.materials[0]=sofa_cloth
from tea_assets import tea_set, instance
collection=tea_set()
for key,location,yaw in [
    ('saucer',(-.88,-.39,1.004),.12),
    ('cup',(-.92,-.35,1.08),-.37),
    ('plate',(.10,-1.375,1.004),.23),
    ('fork',(1.03,-1.51,1.004),-.28),
    ('bowl',(2.92,2.43,1.625),.09),
    ('teapot',(4.08,2.78,1.625),-.24),
]:
    instance(key,collection[key],location,yaw)
# Lightweight original illustration, lit like a small set.
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(8.0,-15.6,14.4)); cam=bpy.context.object;aim(cam,(0,.06,1.10));cam.data.lens=46
sc=bpy.context.scene;sc.camera=cam
for name,p,power,size in [('Paper window',(-5,-5,10),1950,8),('Soft fill',(5,-2,7),600,7),('Sun bounce',(1,5,8),1250,6)]:
    bpy.ops.object.light_add(type='AREA',location=p);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;aim(o,(0,0,0))
sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(*color('eadceb'),1)
sc.world.node_tree.nodes['Background'].inputs[1].default_value=.42
box('Backdrop',(0,0,-.62),(200,200,.15),sand,0)
sc.render.engine='CYCLES';sc.cycles.samples=36;sc.cycles.use_denoising=False
sc.render.resolution_x=1500;sc.render.resolution_y=1120;sc.render.resolution_percentage=100
bpy.context.view_layer.update()
for i,tip in enumerate(balloon_tips):
    balloon_string(bpy.context.collection,i,pin,tip,cord_material,sc)
sc.view_settings.view_transform='AgX';sc.render.image_settings.file_format='PNG'
sc.view_settings.look='AgX - Medium High Contrast'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'art/room.blend'),compress=True)
