"""Build the editable Purrlock Holmes diorama. Blender 4.3+."""
from pathlib import Path
import bpy, math
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
def color(h):
    return tuple((v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4) for v in [int(h[i:i+2],16)/255 for i in (0,2,4)])
def mat(name,h):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color(h),1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Roughness'].default_value=.82
    return m
cream=mat('Milk','fff0da'); wood=mat('Honey beech','d99c68'); honey=mat('Pale oak','edbf86'); dark=mat('Cocoa ink','52394a'); mint=mat('Pistachio','a6cba5'); jade=mat('Leaf','659879'); pink=mat('Peach','ee9e9d'); red=mat('Berry','d96066'); blue=mat('Cloud blue','83abc7'); gold=mat('Butterscotch','edb95f'); sand=mat('Rice paper','e8d3b6'); silver=mat('Soft pewter','a5b8bd'); terr=mat('Terracotta','d58c6d'); glass=mat('Window blue','bbdce3'); wall=mat('Barley wall','eee1c6')
active=None
def finish(o,name,m):
    o.name=name;o.data.materials.append(m)
    if active is not None:
        o.parent=active;o['pick_id']=active['pick_id']
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
def item(i,n):
    global active
    active=bpy.data.objects.new(n,None);bpy.context.collection.objects.link(active);active['pick_id']=i
def end():
    global active
    active=None
def cup(x,y,z,m):
    cyl('Cup body',(x,y,z+.21),.245,.41,m,.29);ring('Cup lip',(x,y,z+.42),.258,.033,m);ell('Cup inner shadow',(x,y,z+.412),(.232,.232,.012),dark);ring('Cup handle',(x+.33,y,z+.23),.145,.039,m,True)
def dish(x,y,z,m,r=.44):
    ell('Dish',(x,y,z+.078),(r,r,.10),m);ring('Dish rim',(x,y,z+.14),r*.84,.032,m)
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
for x in [.53,4.18]:
    for j in range(5):box('Linen curtain fold',(x+j*.082-.17,4.07,3.19),(.12,.19,1.75+(j%2)*.10),cream,.05)
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
def plant(x,y,z):
    cyl('Plant pot',(x,y,z+.26),.27,.51,terr,.39)
    cyl('Pot earth',(x,y,z+.51),.33,.024,dark)
    for j in range(7):
        a=j*2.4;r=.24+.09*(j%2);endp=(x+math.cos(a)*r,y+math.sin(a)*r,z+.87+.16*(j%3))
        line('Plant stalk',[(x,y,z+.51),endp],.019,jade)
        o=ell('Rubber plant leaf',endp,(.27,.12,.077),[mint,jade][j%2]);o.rotation_euler=(.1,.3,a)
plant(5.12,2.86,1.63);plant(-5.02,-.53,.10)
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
box('Toy car chassis',(3.39,-1.80,.31),(.91,.48,.28),red,.10)
box('Toy car cab',(3.53,-1.80,.51),(.46,.39,.27),pink,.10)
for x in [3.11,3.69]:
    for y in [-2.03,-1.57]:ell('Toy car wheel',(x,y,.23),(.14,.08,.14),dark)
for x,y,m in [(4.38,-1.18,blue),(4.92,-1.18,gold),(4.62,-.84,pink),(-3.78,-2.18,mint)]:
    box('Wooden toy block',(x,y,.23),(.32,.33,.32),m,.056,.26)
for x in [-5.05,-4.55]:
    ell('House slipper',(x,-2.78,.15),(.20,.36,.09),pink);ell('Slipper upper',(x,-2.64,.24),(.18,.20,.13),pink)
cyl('Basket',(4.63,-.02,.36),.54,.55,sand,.67)
ring('Basket piping',(4.63,-.02,.63),.63,.066,wood)
for z in [.22,.35,.48]:ring('Reed bands',(4.63,-.02,z),.54+(z-.15)*.22,.024,wood)
ell('Basket fabric',(4.66,-.02,.62),(.48,.44,.17),blue)
ell('Red balloon',(5.05,.16,2.47),(.42,.38,.50),red)
ell('Balloon knot',(5.05,.16,1.96),(.072,.060,.088),red)
line('Balloon thread',[(5.05,.16,1.94),(5,.16,1.61),(4.88,.15,1.23),(4.65,.13,.72)],.014,dark)
box('Floor magazine',(-2.67,-3.46,.162),(.80,.58,.048),mint,.034,-.18)
box('Magazine art',(-2.67,-3.46,.190),(.46,.24,.008),cream,.022,-.18)
# Seven uniquely clickable dishware groups. All sub-meshes share their parent ID.
item(1,'01 · Blue cup');cup(-.85,-.39,.997,blue);end()
item(2,'02 · Shell plate');dish(.08,-1.30,1.0,cream,.53);end()
item(3,'03 · Fork'); 
box('Fork handle',(.60,-.97,1.067),(.093,.56,.05),silver,.024,-.50)
box('Fork head',(.77,-.65,1.068),(.27,.18,.048),silver,.022,-.50)
for j in range(4):box('Fork tine',(.75+j*.055,-.55+j*.029,1.068),(.032,.19,.047),silver,.014,-.50)
end()
# Fabric masks the fork handle so the teeth remain a clue.
box('Folded linen',(.46,-1.18,1.125),(.48,.44,.085),mint,.075,-.38)
item(4,'04 · Peach bowl')
ell('Bowl body',(3.14,2.39,1.82),(.38,.38,.23),pink)
ring('Bowl rim',(3.14,2.39,1.99),.353,.042,pink)
ell('Bowl inner',(3.14,2.39,1.978),(.317,.317,.025),terr)
end()
item(5,'05 · Teaspoon')
ell('Spoon bowl',(-3.09,-2.30,.174),(.139,.191,.035),silver)
box('Spoon handle',(-3.09,-2.62,.176),(.075,.51,.05),silver,.028)
end()
item(6,'06 · Teapot')
ell('Teapot belly',(2.19,-2.91,.43),(.47,.42,.36),mint)
ring('Teapot handle',(2.66,-2.91,.49),.21,.059,jade,True)
line('Teapot spout',[(1.91,-2.91,.41),(1.70,-2.92,.50),(1.52,-2.92,.73)],.103,mint)
cyl('Teapot lid',(2.19,-2.91,.74),.27,.074,jade);ell('Teapot knob',(2.19,-2.91,.83),(.076,.076,.072),cream)
end()
item(7,'07 · Saucer');dish(-5.17,.42,.079,blue,.41);end()
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
