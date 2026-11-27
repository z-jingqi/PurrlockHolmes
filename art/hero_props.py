"""Sculpted focal props for the afternoon room; edited with the locked camera."""
import math
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Euler,Vector
from room_props import finish_material
from tea_assets import Studio

T=math.tau

def maker(collection):
    s=Studio.__new__(Studio);s.collection=collection
    return s

def shell(s,name,shape,mat,rows=35,cols=64):
    points=[shape(i/(rows-1),T*j/cols) for i in range(rows) for j in range(cols)]
    faces=[(i*cols+j,(i+1)*cols+j,(i+1)*cols+(j+1)%cols,i*cols+(j+1)%cols)
           for i in range(rows-1) for j in range(cols)]
    return s.mesh(name,points,faces,mat)

def pillow(collection,name,center,w,h,depth,yaw,pitch,body_hex,seam_hex):
    s=maker(collection)
    fabric=finish_material(name+" • cotton cover",body_hex,.84,.28)
    seam=finish_material(name+" • bound fabric edge",seam_hex,.81,.18)
    M=Euler((pitch,-.08,yaw)).to_matrix()
    def point(t,a):
        r=max(.0001,math.sin(math.pi*t))
        bulge=math.cos(math.pi*t)
        x=math.copysign(abs(math.cos(a))**.57,math.cos(a))
        z=math.copysign(abs(math.sin(a))**.57,math.sin(a))
        pinch=.984+.014*math.cos(4*a+.12)+.013*math.sin(3*a)
        # One continuous pair of sewn panels: flattened corners and fullness in the middle.
        px=w*r*x*pinch
        pz=h*r*z*(1+.045*math.sin(a+.3))-.028*r*abs(x)
        crease=(.014*math.sin(11*a+.2)+.009*math.cos(17*a))*r**5*abs(bulge)
        py=-depth*bulge*(1+.055*r*math.cos(2*a)) + crease
        return tuple(Vector(center)+M@Vector((px,py,pz)))
    # The seam is evaluated from the same surface, not floated in front of it.
    shell(s,name+" • sewn curved panels",point,fabric)
    curve=[point(.473,T*i/80) for i in range(81)]
    s.tube(name+" • in-seam piping",curve,[.010]*len(curve),seam,axis=(0,1,0),samples=1,sections=10)
    return fabric

def cat(collection,ell):
    s=maker(collection)
    fur=finish_material("Cat • warm mochi cream","fff0d9",.76,.27)
    underside=finish_material("Cat • warm coat shadow","eddbc0",.81,.23)
    mask=finish_material("Cat • muzzle milk","fff5e5",.78,.22)
    inner=finish_material("Cat • soft ear rose","eab0aa",.78,.21)
    cheeks=finish_material("Cat • peach blush","eeb5ad",.79,.22)
    dark=finish_material("Cat • cocoa features","574047",.49,coat=.13)
    ink=finish_material("Cat • gentle embroidered whiskers","a67e72",.81)
    bow=finish_material("Cat • muted pink ribbon","c77e84",.68,.2)
    highlight=finish_material("Cat • eye glint","ffedda",.45)
    center=Vector((-3.51,1.93,1.78))
    rot=Euler((-.03,0,.28)).to_matrix()
    def world(p):
        return tuple(center+rot@Vector(p))
    def bulb(name,p,scale,m):
        o=ell("Cat "+name,world(p),scale,m)
        o.rotation_euler=(-.03,0,.28)
        return o
    def band(name,p,r,m,axis=(0,1,0)):
        return s.tube("Cat "+name,[world(q) for q in p],r,m,axis=axis,sections=10,samples=4)
    # Crouched loaf with relaxed asymmetric paws and a tapering, rounded curled tail.
    bulb("body loft",(.006,.255,-.383),(.535,.468,.275),fur)
    bulb("body chest",(0,-.087,-.389),(.325,.288,.228),fur)
    for sign in (-1,1):
        px=.205*sign
        p=bulb("little paw weight", (px,-.302+sign*.027,-.548),(.152,.204,.088),fur)
        p.rotation_euler.z+=sign*.13
        for shift in (-.038,.035):
            band("little paw toe seam",[(px+shift,-.483+sign*.026,-.538),(px+shift,-.495+sign*.026,-.551)],
                 [.0052,.003],underside)
    band("tail curled soft tip",[(.34,.36,-.405),(.53,.43,-.405),(.715,.40,-.364),(.798,.37,-.265),(.754,.34,-.178),(.697,.31,-.183)],
         [.132,.118,.093,.072,.059,.029],fur,axis=(0,1,0))
    bulb("tail closed tip",(.689,.306,-.187),(.033,.037,.035),fur)
    def head(t,a):
        u=math.cos(math.pi*t);r=max(.0001,math.sin(math.pi*t))
        w=.542*(1+.16*math.exp(-((u+.26)/.32)**2)-.065*max(u,0))
        return world((w*r*math.cos(a),.410*r*math.sin(a)*(1-.056*max(u,0)),
                      .426*u-.018*r*math.sin(a)))
    shell(s,"Cat sculpted head",head,fur,rows=43)
    # Puffy triangular ears with inner surfaces that follow their own rim.
    for sign in (-1,1):
        shape=[(-.167,-.094),(-.153,.045),(-.103,.193),(-.034,.298),(.018,.326),(.077,.301),
               (.125,.23),(.175,.10),(.181,-.038),(.108,-.10),(.01,-.125),(-.10,-.12)]
        location=Vector((sign*.353,.025,.257))
        ear_center=Vector((.025,0,.073))
        def ear_coord(x,z,r,y):
            p=ear_center+Vector(((x-ear_center.x)*r,y,(z-ear_center.z)*r))
            return world(location+Vector((p.x*sign,p.y+.075*p.z,p.z)))
        loops=[(.001,.086),(.56,.093),(.89,.064),(1,.008),(.96,-.055),(.81,-.096),(.60,-.111),(.26,-.093),(.001,-.083)]
        pts=[ear_coord(x,z,r,y) for r,y in loops for x,z in shape]
        n=len(shape)
        faces=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(loops)-1) for i in range(n)]
        if sign<0:faces=[f[::-1] for f in faces]
        ear=s.mesh("Cat rounded triangle ear",pts,faces,fur);ear.data.materials.append(inner)
        for polygon in ear.data.polygons:
            if polygon.index//n>=5:polygon.material_index=1
        ear.modifiers.new("Rounded rim and ear bowl","SUBSURF").levels=2
    for sign in (-1,1):
        x=sign*.202
        bulb("dot eye",(x,-.390,.006),(.048,.018,.056),dark)
        bulb("eye glint",(x-.013,-.407,.023),(.012,.004,.014),highlight)
        bulb("blush",(sign*.303,-.341,-.095),(.070,.013,.032),cheeks)
        bulb("soft muzzle",(sign*.071,-.397,-.100),(.101,.026,.058),mask)
        for j in range(2):
            z=-.093-j*.027
            band("muzzle whisker",[(sign*.229,-.370,z),(sign*(.309+j*.024),-.342,z+.014-j*.016),
                                  (sign*(.410+j*.025),-.277,z+.012-j*.021)],[.005,.005,.0022],ink)
        band("little smile",[(0,-.426,-.125),(sign*.035,-.427,-.157),(sign*.088,-.416,-.145)],
             [.007,.008,.0045],dark)
    bulb("rose button nose",(0,-.430,-.102),(.039,.019,.025),dark)
    for sign in (-1,1):
        o=bulb("little bow folded lobe",(sign*.079,-.306,-.385),(.092,.035,.054),bow)
        o.rotation_euler.y=.24*sign
    bulb("little bow wrapped knot",(0,-.337,-.385),(.044,.030,.041),inner)

# Same soft colors as the room's crockery; a warmer matte latex than the old glossy shapes.
BALLOON_DESIGNS=(
    ("e2a6a7",(5.43,-.13,2.44),.755,-.07),
    ("ecd096",(5.80,.11,2.83),.795,.13),
    ("9abeb2",(6.27,-.64,2.47),.725,.17),
)

def balloon(collection,index,rgb,pos,scale,lean):
    s=maker(collection)
    mat=finish_material("Balloon • powdery latex "+str(index),rgb,.58,coat=0)
    bs=mat.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Specular IOR Level"].default_value=.21
    bs.inputs["Subsurface Weight"].default_value=.062
    bs.inputs["Subsurface Radius"].default_value=(.66,.29,.15)
    bs.inputs["Subsurface Scale"].default_value=.09
    geometry=Euler((0,lean,0)).to_matrix()
    def world(v):
        return tuple(Vector(pos)+geometry@Vector(v)*scale)
    local=s.lathe("Balloon • softly inflated pear membrane",
        [(r,(h+.66)) for r,h in [(.001,-.591),(.031,-.583),(.049,-.553),(.081,-.519),
         (.145,-.477),(.199,-.414),(.251,-.348),(.313,-.259),(.361,-.166),(.394,-.06),
         (.409,.055),(.403,.17),(.378,.27),(.337,.365),(.267,.452),(.174,.512),(.083,.547),(.001,.558)]],
        mat,steps=4,z=-.66)
    for vertex in local.data.vertices:
        x,y,z=vertex.co
        oval=1+.031*math.cos(index*1.68+z*3)
        arc=.027*(z+.16)**2*(-1 if index==0 else 1)
        vertex.co=world((x*oval+arc,y*(1-.056*index),z))
    local["room_balloon"]=index
    tip=world((.006,-.009,-.626))
    for name,points,radii in [
      ("folded latex knot",[(0,0,-.568),(.018,-.013,-.593),(.026,-.022,-.613),(.006,-.021,-.629),(-.020,-.009,-.627)],
       [.024,.027,.027,.018,.012]),
      ("turned latex cuff",[(-.026,-.014,-.611),(-.029,.007,-.625),(0,.026,-.637),(.026,.012,-.625)],
       [.015,.015,.017,.013])]:
        o=s.tube("Balloon "+name,[world(p) for p in points],[r*scale for r in radii],mat,sections=12)
        o["room_balloon"]=index
    return tip


def balloon_string(collection,index,anchor,tip,material,scene):
    """Independent cotton cord for Blender inspection; the game draws its dynamic counterpart."""
    data=bpy.data.curves.new("Balloon cord • flexible centerline",type="CURVE")
    data.dimensions="3D"
    data.resolution_u=24
    data.bevel_depth=.0065
    data.bevel_resolution=3
    data.materials.append(material)
    o=bpy.data.objects.new("Balloon • separate cotton string "+str(index+1),data)
    collection.objects.link(o)
    o["room_balloon_string"]=index
    # The source cord and membrane are real independent objects, sharing only the tie point.
    # Sprite renders exclude this curve so it never doubles the game's independently animated one.
    o.hide_render=True
    root,end=Vector(anchor),Vector(tip)
    cam=scene.camera
    frame=cam.data.view_frame(scene=scene)
    w,h=1200,896
    u0,u1=min(v.x for v in frame),max(v.x for v in frame)
    v0,v1=min(v.y for v in frame),max(v.y for v in frame)
    r2,e2=[world_to_camera_view(scene,cam,p) for p in (root,end)]
    inverse=cam.matrix_world.inverted()
    depths=[(inverse@p).z for p in (root,end)]
    drape=((-11.0,5.5),(-9.4,6.8),(-7.0,9.2))[index]
    spline=data.splines.new("BEZIER");spline.bezier_points.add(8)
    for i,pt in enumerate(spline.bezier_points):
        t=i/8
        slack=math.sin(math.pi*t)
        # Draw the same relaxed shape as the game at rest, in true local 3D at
        # interpolated depth. Keep physical endpoints exact at the knots.
        x=r2.x+(e2.x-r2.x)*t+slack*(drape[0]+7.7*math.sin(T*t+.46*index)+2*math.sin(1.54*index-t*2.5))/w
        y=r2.y+(e2.y-r2.y)*t-slack*drape[1]/h
        z=depths[0]+(depths[1]-depths[0])*t
        scale=z/frame[0].z if cam.data.type=="PERSP" else 1.0
        local=Vector(((u0+(u1-u0)*x)*scale,(v0+(v1-v0)*y)*scale,z))
        pt.co=root if i==0 else end if i==8 else cam.matrix_world@local
        pt.handle_left_type=pt.handle_right_type="AUTO"
    return o
