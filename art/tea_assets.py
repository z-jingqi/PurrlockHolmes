"""Reusable Blender collection assets for the Afternoon Tea set. Z-up, feet at z=0."""
import bmesh, bpy, math
from mathutils import Vector
TAU=math.tau

def glaze(name,color,roughness=.27,metal=0.0):
    mat = bpy.data.materials.new(name); mat.use_nodes=True
    rgb=tuple(e/12.92 if e<=.04045 else ((e+.055)/1.055)**2.4 for e in [int(color[i:i+2],16)/255 for i in (0,2,4)])
    mat.diffuse_color=(*rgb,1)
    shader=mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value=mat.diffuse_color
    shader.inputs["Roughness"].default_value=roughness
    shader.inputs["Metallic"].default_value=metal
    if not metal:
        shader.inputs["Coat Weight"].default_value=.24
        shader.inputs["Coat Roughness"].default_value=.26
    return mat

def smooth_profile(points, steps=4):
    """Interpolate a radial cross-section without beveling away thin lip and foot details."""
    out=[]
    for i in range(len(points)-1):
        a,b,c,d=map(Vector,[points[max(0,i-1)],points[i],points[i+1],points[min(i+2,len(points)-1)]])
        for j in range(steps):
            t=j/steps
            p=.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
            out.append((max(p.x,.0001),max(p.y,0)))
    return out+[tuple(points[-1])]

class Studio:
    def __init__(self):
        self.ivory=glaze("Tea • rice porcelain","f5e6d1")
        self.sky=glaze("Tea • celadon blue","a4c6cd")
        self.blue=glaze("Tea • blue underglaze","749ca5",.30)
        self.peach=glaze("Tea • blush glaze","e6a99d")
        self.rose=glaze("Tea • blush rim","cc887f")
        self.honey=glaze("Tea • tea stain accent","c89965",.32)
        self.tea=glaze("Tea • amber infusion","a36c49",.20)
        self.steel=glaze("Tea • satin stainless steel","d5d6d7",.26,1.0)
        self.gray=glaze("Tea • low contrast engraving","adbbbf",.49,.30)

    def mesh(self,name,verts,faces,material):
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
        obj=bpy.data.objects.new(name,mesh);self.collection.objects.link(obj);mesh.materials.append(material)
        for p in mesh.polygons:p.use_smooth=True
        return obj

    def lathe(self,name,profile,material,steps=4,z=0,wave=0,wave_n=10,cap=True):
        profile=smooth_profile(profile,steps)
        vertices=[]; faces=[]; detail=80
        max_r=max(max(p[0] for p in profile),.1)
        for r,h in profile:
            for i in range(detail):
                a=TAU*i/detail
                rim=wave*(r/max_r)**5*math.cos(a*wave_n)
                vertices.append(((r+rim)*math.cos(a),(r+rim)*math.sin(a),h+z))
        for row in range(len(profile)-1):
            for j in range(detail):
                i=row*detail+j;k=row*detail+(j+1)%detail
                faces.append((i,k,k+detail,i+detail))
        if cap:faces.extend([tuple(range(detail-1,-1,-1)),tuple((len(profile)-1)*detail+i for i in range(detail))])
        return self.mesh(name,vertices,faces,material)

    def tube(self,name,centers,radii,material,axis=(0,1,0),hollow=0,sections=24,samples=6):
        # Smooth centerline, taper rings and skin thickness; used for handles and spouts.
        pts=[Vector(p) for p in centers]; args=[]
        for i in range(len(pts)-1):
            a,b,c,d=pts[max(i-1,0)],pts[i],pts[i+1],pts[min(i+2,len(pts)-1)]
            for j in range(samples):
                t=j/samples
                p=.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
                args.append((p,(1-t)*radii[i]+t*radii[i+1]))
        args.append((pts[-1],radii[-1]))
        verts=[]; faces=[]; section=sections
        for i,(center,r) in enumerate(args):
            direction=(args[min(i+1,len(args)-1)][0]-args[max(i-1,0)][0]).normalized()
            ref=Vector(axis).cross(direction).normalized()
            second=direction.cross(ref).normalized()
            for k in range(section):
                a=TAU*k/section; verts.append(tuple(center+ref*r*math.cos(a)+second*r*math.sin(a)))
        for i in range(len(args)-1):
            for k in range(section):
                j=i*section+k;l=i*section+(k+1)%section
                faces.append((j,l,l+section,j+section))
        if hollow:
            center,r=args[-1]
            direction=(args[-1][0]-args[-2][0]).normalized()
            last=len(verts)-section; old=[Vector(p) for p in verts[last:]]
            for depth,fac in [(0.006,1-hollow),(.10,1-hollow)]:
                for p in old:verts.append(tuple(center+(p-center)*fac-direction*depth))
            for i in range(2):
                for k in range(section):
                    j=last+i*section+k;l=last+i*section+(k+1)%section
                    faces.append((j,l,l+section,j+section))
        faces.append(tuple(range(section-1,-1,-1)))
        return self.mesh(name,verts,faces,material)

    def el(self,name,p,scale,mat):
        # Local sphere; collection is independent of the level.
        rings,cols=16,32;verts=[];faces=[]
        for i in range(rings+1):
            phi=math.pi*i/rings
            for j in range(cols):
                a=TAU*j/cols
                verts.append((p[0]+scale[0]*math.sin(phi)*math.cos(a),p[1]+scale[1]*math.sin(phi)*math.sin(a),p[2]+scale[2]*math.cos(phi)))
        for i in range(rings):
            for j in range(cols):
                a=i*cols+j;b=i*cols+(j+1)%cols;faces.append((a,a+cols,b+cols,b))
        return self.mesh(name,verts,faces,mat)

    def band(self,name,r,z,w,mat):
        return self.lathe(name,[(r-.001,z-w),(r+.005,z-w*.55),(r+.006,z+w*.55),(r-.003,z+w)],mat,3,cap=False)

    def fork(self):
        # Four connected bands follow the curvature of a single stamping.
        # They share vertices through the shank, separating only at the slots.
        def ease(x,lo,hi):
            t=max(0,min(1,(x-lo)/(hi-lo)))
            return t*t*(3-2*t)

        def half_width(y):
            return (.056+.010*ease(y,-.448,-.412)-.034*ease(y,-.40,-.094)
                    +.084*ease(y,-.008,.174))

        bm=bmesh.new();weld={}
        rows=112; cols=6
        start,tip=-.448,.478
        for finger in range(4):
            rows_here=[]
            for j in range(rows+1):
                v=start+(tip-start)*j/rows
                y=v-.021*abs(finger-1.5)*ease(v,.245,tip)
                w=half_width(v)
                slot=ease(v,.229,.304)
                band_center=(finger-1.5)*w*.5
                reach=w*.25*(1-.34*slot)*(1-.66*ease(v,tip-.023,tip))
                row=[]
                for k in range(cols+1):
                    u=2*k/cols-1
                    x=band_center+u*reach
                    spine=(.024+.019*ease(y,-.431,-.116)+.083*ease(y,-.075,.163)
                           -.026*ease(y,.167,.331)+.027*ease(y,.306,.475))
                    grip=.009*(1-ease(y,.013,.122))*(1-min(1,(x/max(w,.01))**2))
                    scoop=.012*ease(y,.064,.184)*(1-ease(y,.242,.311))*(x/w)**2
                    rounded=.0031*slot*(1-u*u)
                    z=spine+grip+scoop+rounded
                    key=tuple(round(f,7) for f in (x,y,z))
                    if key not in weld:weld[key]=bm.verts.new((x,y,z))
                    row.append(weld[key])
                if j:
                    prev=rows_here[-1]
                    for k in range(cols):
                        bm.faces.new((prev[k],prev[k+1],row[k+1],row[k]))
                rows_here.append(row)
        mesh=bpy.data.meshes.new("Curved four-tine stamping")
        bm.to_mesh(mesh);bm.free();mesh.update()
        obj=bpy.data.objects.new("Swept steel handle, neck and scooped tines",mesh)
        self.collection.objects.link(obj);mesh.materials.append(self.steel)
        for f in mesh.polygons:f.use_smooth=True
        solid=obj.modifiers.new("Real steel stock thickness","SOLIDIFY")
        solid.thickness=.017;solid.offset=-1
        bevel=obj.modifiers.new("Polished edges","BEVEL")
        bevel.width=.0030;bevel.segments=3;bevel.angle_limit=.53
        return obj

    def dish(self,r,material,rim,wave=0):
        profile=[(.002,.023),(.37,.023),(.41,.006),(.48,.006),(.52,.025),(.74,.035),(.91,.085),(.99,.114),(1,.132),(.97,.146),(.92,.134),(.80,.096),(.61,.073),(.002,.073)]
        self.lathe("Curved foot, underside and food well",[(x*r,y) for x,y in profile],material,wave=wave)
        self.lathe("Glazed rim inlay",[(.911*r,.135),(.939*r,.142),(.956*r,.141),(.922*r,.134)],rim,wave=wave*.84,cap=False)

    def make(self,key,title,details):
        collection=bpy.data.collections.new(title); collection.use_fake_user=True
        self.collection=collection
        if key=="cup":
            self.lathe("Thrown cup • foot to inner wall",[(.004,.034),(.14,.034),(.151,.007),(.19,.007),(.207,.031),(.239,.136),(.261,.29),(.267,.392),(.254,.411),(.232,.409),(.223,.374),(.221,.294),(.191,.12),(.14,.071),(.002,.071)],self.sky)
            self.band("Fine blue lip",.254,.401,.006,self.blue)
            self.lathe("Tea in the deep well",[(.002,.245),(.216,.245),(.218,.248),(.002,.250)],self.tea,2)
            self.tube("Pulled porcelain handle",[(.22,0,.327),(.36,0,.343),(.425,0,.268),(.40,0,.174),(.30,0,.125),(.218,0,.133)],[.047,.042,.039,.040,.044,.052],self.sky)
        elif key=="saucer":
            self.dish(.43,self.ivory,self.blue)
        elif key=="plate":
            self.dish(.55,self.ivory,self.rose,.012)
            self.lathe("Fine blush ring in the well",[(.344,.077),(.350,.079),(.356,.079),(.359,.075)],self.peach,2,cap=False)
        elif key=="bowl":
            self.lathe("Scalloped dessert bowl • hollow wall",[(.002,.029),(.137,.029),(.15,.008),(.206,.010),(.22,.033),(.29,.11),(.352,.212),(.379,.314),(.375,.343),(.354,.348),(.333,.325),(.316,.246),(.276,.153),(.19,.082),(.002,.067)],self.peach,wave=.012)
            self.lathe("Porcelain glaze line",[(.361,.336),(.375,.34),(.372,.35),(.355,.347)],self.ivory,wave=.012,cap=False)
        elif key=="teapot":
            self.lathe("Thrown vessel • foot, belly and neck",[(.002,.030),(.25,.030),(.261,.009),(.308,.013),(.35,.064),(.436,.20),(.456,.343),(.423,.47),(.34,.574),(.242,.611),(.229,.597),(.23,.557),(.338,.482),(.394,.34),(.375,.19),(.29,.103),(.002,.103)],self.ivory)
            self.band("Quiet celadon band",.428,.448,.010,self.sky)
            self.tube("Curved pouring spout • open lip",[(-.34,0,.24),(-.49,0,.266),(-.592,0,.38),(-.67,0,.53),(-.77,0,.591)],[.126,.106,.084,.058,.066],self.ivory,hollow=.28)
            self.tube("Tapered swept handle",[(.361,0,.46),(.50,0,.51),(.646,0,.44),(.671,0,.315),(.585,0,.206),(.384,0,.189)],[.068,.052,.052,.049,.060,.07],self.sky)
            self.lathe("Seated lid with glaze line",[(.002,.591),(.216,.591),(.243,.609),(.246,.626),(.223,.647),(.158,.676),(.002,.686)],self.sky)
            self.el("Rounded porcelain finial",(0,0,.718),(.071,.071,.044),self.ivory)
        elif key=="fork":
            self.fork()
        collection.asset_mark()
        collection.asset_data.description=details
        for tag in ['Purrlock Holmes','Tableware','Afternoon Tea']:collection.asset_data.tags.new(tag)
        collection["asset_id"]=key
        collection["category"]="tableware"
        for obj in collection.objects:obj["asset_id"]=key
        return collection

def tea_set():
    studio=Studio()
    return {key:studio.make(key,title,description) for key,title,description in [
      ("cup","Tea · Celadon cup","Hollow glazed porcelain, sculpted foot and pulled handle."),
      ("saucer","Tea · Porcelain saucer","Ivory glaze, low rim and celadon hairline."),
      ("plate","Tea · Petal plate","Shallow dessert plate with a subtle scalloped edge."),
      ("fork","Tea · Satin dessert fork","Curved stainless steel with a raised neck, scooped head and four tapered tines."),
      ("bowl","Tea · Blush bowl","Hollow scalloped porcelain with a fitted footring."),
      ("teapot","Tea · Moon teapot","Separate glazed lid, swept handle and an open pouring spout.")
    ]}

def instance(key,collection,location,yaw):
    obj=bpy.data.objects.new("Tea asset | "+key,None);bpy.context.scene.collection.objects.link(obj)
    obj.instance_type='COLLECTION';obj.instance_collection=collection
    obj.location=location;obj.rotation_euler.z=yaw
    obj["tea_key"]=key
    return obj
