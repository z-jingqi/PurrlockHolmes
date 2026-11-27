"""Build the editable Purrlock Holmes diorama. Blender 4.3+."""
from pathlib import Path
import bpy, math, sys
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'art'))
from room_props import scene_props, place, finish_material
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
box('Blush pillow',(-4.66,2.78,1.54),(.77,.38,.75),pink,.17,-.12)
box('Butter pillow',(-2.31,2.69,1.43),(.60,.35,.62),gold,.16,.24)
box('Wool rug',(-.46,-1.07,.09),(6.65,5.18,.07),cream,.26)
for j in range(8):
    for y in [-3.49,1.34]:box('Rug stitched dash',(-3.31+j*.80,y,.134),(.38,.037,.011),terr,.004)
for x in [-1.73,1.48]:
    for y in [-1.76,.12]:cyl('Low table leg',(x,y,.46),.12,.72,wood,.16)
box('Tea table',(-.11,-.82,.89),(3.83,2.53,.22),honey,.22)
# A low wooden chair with a peach seat, beside the tea table.
cx, cy = -3.22, -.53
for dx in [-.46,.46]:
    for dy in [-.43,.43]:
        box('Chair leg',(cx+dx,cy+dy,.49),(.15,.15,.89),wood,.042)
box('Chair seat',(cx,cy,.94),(1.22,1.18,.16),honey,.074)
box('Chair cushion',(cx,cy-.02,1.07),(1.12,1.02,.17),pink,.105)
for dx in [-.48,.48]:
    box('Chair upright',(cx+dx,cy+.46,1.47),(.15,.145,1.15),wood,.048)
box('Chair back',(cx,cy+.46,1.88),(1.18,.18,.52),honey,.07)
box('Chair book',(cx+.08,cy-.06,1.20),(.59,.48,.085),mint,.055,-.16)
box('Chair book label',(cx+.08,cy-.06,1.246),(.27,.19,.013),cream,.019,-.16)
# Cabinet and accents
box('Sideboard',(3.84,2.78,.79),(3.20,1.14,1.43),wood,.12)
box('Sideboard top',(3.84,2.78,1.55),(3.38,1.31,.14),honey)
for x in [2.84,3.84,4.84]:
    box('Linen cupboard door',(x,2.19,.79),(.93,.115,1.19),cream)
    ell('Drawer pull',(x+.22,2.095,.83),(.073,.068,.073),wood)
for x in [3.31,4.66]:
    cyl('Bookend',(x,2.69,1.75),.13,.28,cream)
for j,m in enumerate([mint,pink,blue,gold]):
    box('Little book',(3.57+j*.18,2.78,1.84),(.14,.49,.47-j*.04),m,.035)
props=scene_props()
place(props["clay_planter"],(-5.02,-.53,.064),-.22,1.07)
place(props["rubber_plant"],(-5.02,-.53,.064+.432*1.07),-.38,1.07)
place(props["celadon_planter"],(5.12,2.86,1.624),.22,.91)
place(props["lance_plant"],(5.12,2.86,1.624+.443*.91),.42,.91)
# Room mascot: original cream detective cat
ell('Cat body',(-3.53,2.13,1.40),(.56,.37,.33),cream)
ell('Cat head',(-3.52,1.95,1.83),(.59,.43,.47),cream)
for x,sgn in [(-3.91,-1),(-3.13,1)]:
    bpy.ops.mesh.primitive_cone_add(vertices=32,radius1=.24,radius2=.065,depth=.47,location=(x,1.99,2.19))
    o=bpy.context.object;o.rotation_euler.y=sgn*.20;k=o.modifiers.new('Soft tip','BEVEL');k.width=.068;k.segments=4;finish(o,'Cat ear',cream)
    ell('Cat ear blush',(x,1.82,2.18),(.10,.055,.14),pink)
for x in [-3.72,-3.31]:
    ell('Cat dot eye',(x,1.571,1.85),(.046,.024,.050),dark)
    ell('Cat blush',(x-.04,1.59,1.735),(.075,.029,.035),pink)
ell('Cat little nose',(-3.52,1.532,1.77),(.040,.024,.028),dark)
for x in [-3.85,-3.24]:ell('Cat little paw',(x,1.75,1.24),(.17,.19,.10),cream)
line('Cat tail',[(-3.03,2.23,1.44),(-2.89,2.33,1.45),(-2.83,2.37,1.57),(-2.88,2.39,1.70)],.085,cream)
# Assorted non-target props: toy truck, books, slipper, basket, fruit, balloon
box('Storybook',(-1.34,-1.32,1.05),(.76,.55,.085),blue,.047,-.24)
box('Book label',(-1.34,-1.32,1.098),(.32,.21,.012),cream,.034,-.24)
box('Notebook',(.83,.00,1.055),(.73,.49,.09),pink,.046,.12)
ell('Clementine',(.90,-1.46,1.17),(.18,.18,.16),gold)
ell('Clementine leaf',(.89,-1.42,1.32),(.095,.045,.023),jade)
# Different finishes remain legible at the real game camera, even without texture noise.
car_enamel=finish_material("Toy • smooth strawberry enamel","ce626c",.36,coat=.32)
car_cab=finish_material("Toy • rose enamel","df9a98",.43,coat=.2)
car_glass=finish_material("Toy • celadon windows","72929c",.30,coat=.26)
car_tire=finish_material("Toy • matte rubber","50404a",.84)
wheel_hub=finish_material("Toy • pale metal hubs","d7b89a",.44)
latex=finish_material("Balloon • rose latex","dc7c87",.27,coat=.23)
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
for x,y,m in [(4.38,-1.18,blue),(4.92,-1.18,gold),(4.62,-.84,pink),(-3.78,-2.18,mint)]:
    box('Wooden toy block',(x,y,.226),(.32,.33,.32),m,.037,.26)
    badge=ring('Block inlay',(x,y,.386),.079,.010,cream)
    badge.scale.y=.82
place(props["felt_slippers"],(-4.80,-2.78,.062),.051)
place(props["reed_basket"],(4.63,-.02,.063),.08,1.08)
# Balloon pole mesh: pear-shaped membrane tapers into the latex neck, not a sphere plus oval.
balloon_col=bpy.context.collection
shaper=Studio.__new__(Studio);shaper.collection=balloon_col
o=shaper.lathe("Balloon membrane",[(r,h+.55) for r,h in [(.001,-.537),(.040,-.533),(.043,-.492),
    (.083,-.454),(.164,-.410),(.280,-.339),(.371,-.229),(.413,-.098),
    (.433,.046),(.425,.170),(.383,.288),(.315,.386),(.217,.458),(.105,.493),(.001,.504)]],latex,z=-.55)
o.location=(5.05,.16,2.47)
o.rotation_euler.y=.11
ell('Balloon knot',(5.00,.16,1.936),(.049,.040,.040),latex)
shaper.tube('Balloon folded tie',[(4.97,.15,1.933),(4.999,.12,1.934),(5.043,.16,1.948)],
    [.016,.024,.016],latex)
shaper.tube('Balloon thread',[(4.998,.157,1.915),(4.958,.156,1.71),(4.948,.15,1.51),
    (4.841,.12,1.26),(4.833,.124,1.075),(4.751,.12,.89),(4.653,.13,.634)],
    [.010,.010,.010,.0095,.0095,.0095,.009],dark,axis=(0,1,0))
box('Floor magazine',(-2.67,-3.46,.162),(.80,.58,.048),mint,.034,-.18)
box('Magazine art',(-2.67,-3.46,.190),(.46,.24,.008),cream,.022,-.18)
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
for x in [-4.55,-4.20]:
    ell('Pillow covered button',(x,2.572,1.60),(.040,.023,.040),terr)
for x in [-3.77,2.85]:
    for j in range(12):
        box('Rug side embroidery',(x,-3.28+j*.38,.126),(.033,.14,.012),terr,.008)
line('Banner branch',[(-2.64,4.235,3.02),(-2.45,4.235,3.15),(-2.28,4.235,3.21)],.014,jade)
for x,z in [(-2.51,3.14),(-2.37,3.19),(-2.24,3.24)]:
    leaf=ell('Print leaf',(x,4.228,z),(.064,.015,.027),jade);leaf.rotation_euler.y=-.58
ell('Cat little bow knot',(-3.51,1.681,1.325),(.083,.048,.06),terr)
for x in [-3.64,-3.38]:
    ell('Cat little bow fold',(x,1.689,1.33),(.12,.045,.072),pink)
# Move cabinet books out of the tea service grouping.
for o in bpy.context.scene.objects:
    if o.name.startswith(('Bookend','Little book')):
        o.location.x-=4.28; o.location.y+=.11; o.location.z-=1.56
# Table linen, sewn edging and a fold. It stays on the table in the tableware level.
box('Folded sage linen',(.97,-.37,1.063),(.55,.36,.105),mint,.065,-.16)
for i in range(8):
    box('Linen stitched hem',(.744+i*.058,-.503-(i*.009),1.117),(.033,.016,.006),cream,.005,-.16)
# Magazine spines, pillow seams and stitched details maintain the quiet silhouette at full-frame.
paper=finish_material("Room • page edges","efe1c8",.91)
sofa_cloth=finish_material("Room • sage upholstery","a6cba5",.88,.33)
wood.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value=.46
honey.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value=.54
for o in bpy.context.scene.objects:
    if o.type=='MESH' and o.name.startswith(('Sofa back','Seat cushion','Sofa arm')):
        o.data.materials[0]=sofa_cloth
for x,z,m in [(-4.66,1.54,terr),(-2.31,1.43,honey)]:
    w=.32 if x < -4 else .245
    pts=[(x+w*math.copysign(abs(math.cos(a))**.58,math.cos(a)),2.598 if x < -4 else 2.522,
          z+w*.92*math.copysign(abs(math.sin(a))**.58,math.sin(a))) for a in [math.tau*i/48 for i in range(49)]]
    line('Pillow softly corded seam',pts,.013,m)
for x,y,z,w,d,ang in [(-1.34,-1.32,1.063,.724,.520,-.24),(.83,0,1.063,.695,.460,.12),
                       (-2.67,-3.46,.168,.763,.551,-.18),(cx+.08,cy-.06,1.202,.555,.448,-.16)]:
    box('Book sewn paper block',(x,y,z),(w,d,.052 if z>.2 else .027),paper,.019,ang)
    # Put a few edges just inside the wrap so the spine and page block read separately.
    for dz in [-.012,.002,.014]:
        px=x+math.sin(ang)*d*.49;py=y-math.cos(ang)*d*.49
        box('Quiet book page edge',(px,py,z+dz),(w*.89,.010,.003),sand,.002,ang)
for sx in [-1,1]:
    for j in range(3):
        x=-3.52+sx*(.25+.028*j);z=1.764-.034*j
        line('Cat muzzle whisker',[(x,1.567,z),(x+sx*.082,1.546,z+.009*(1-j))],.007,terr)
ell('Cat muzzle left',(-3.574,1.563,1.744),(.095,.038,.052),cream)
ell('Cat muzzle right',(-3.466,1.563,1.744),(.095,.038,.052),cream)
for x in [-3.85,-3.24]:
    for dx in [-.055,.052]:
        line('Little paw seam',[(x+dx,1.591,1.265),(x+dx,1.578,1.237)],.007,sand)
from tea_assets import tea_set, instance
collection=tea_set()
for key,location,yaw in [
    ('saucer',(-.88,-.39,1.004),.12),
    ('cup',(-.92,-.35,1.08),-.37),
    ('plate',(.10,-1.375,1.004),.23),
    ('fork',(1.01,-1.30,1.004),-.62),
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
sc.view_settings.view_transform='AgX';sc.render.image_settings.file_format='PNG'
sc.view_settings.look='AgX - Medium High Contrast'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'art/room.blend'),compress=True)
