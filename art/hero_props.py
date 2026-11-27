"""Sculpted focal props for the afternoon room; edited with the locked camera."""
import math
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

def balloon(collection,ell,index,rgb,pos,scale,lean):
    s=maker(collection)
    mat=finish_material("Balloon • thin satin latex "+str(index),rgb,.325,coat=.19)
    bs=mat.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Coat Roughness"].default_value=.38
    bs.inputs["Subsurface Weight"].default_value=.048
    bs.inputs["Subsurface Radius"].default_value=(.66,.29,.15)
    bs.inputs["Subsurface Scale"].default_value=.09
    geometry=Euler((0,lean,0)).to_matrix()
    def world(v):
        return tuple(Vector(pos)+geometry@Vector(v)*scale)
    local=s.lathe("Balloon tensioned pear membrane",
        [(r,(h+.65)) for r,h in [(.001,-.619),(.032,-.620),(.047,-.593),(.048,-.544),(.078,-.506),
         (.132,-.466),(.206,-.385),(.282,-.309),(.348,-.211),(.394,-.118),(.426,-.009),
         (.436,.102),(.418,.220),(.378,.321),(.312,.406),(.232,.469),(.132,.512),(.001,.537)]],
        mat,steps=4,z=-.65)
    for vertex in local.data.vertices:
        x,y,z=vertex.co
        oval=1+.043*math.cos(index*1.68+z*3)
        arc=.032*(z+.16)**2*(-1 if index==2 else 1)
        vertex.co=world((x*oval+arc,y*(1-.056*index),z))
    local["room_balloon"]=index
    tip=world((0,0,-.619))
    for name,points,radii in [
      ("folded neck knot",[(0,0,-.584),(.030,-.020,-.605),(.037,-.041,-.626),(.009,-.038,-.638),(-.026,-.018,-.629)],
       [.020,.024,.022,.017,.011]),
      ("small turned knot lip",[(-.021,-.018,-.609),(-.024,.006,-.625),(0,.021,-.637),(.023,.012,-.626)],
       [.012,.012,.014,.01])]:
        o=s.tube("Balloon "+name,[world(p) for p in points],[r*scale for r in radii],mat,sections=12)
        o["room_balloon"]=index
    return tip
