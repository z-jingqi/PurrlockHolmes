"""Editable handmade props for Case 01. Coordinates are Z-up, with feet at zero."""
import math
import bpy
from mathutils import Vector
from tea_assets import Studio, glaze

TAU=math.tau

def finish_material(name, hex_color, roughness, sheen=0, coat=0):
    mat=glaze(name,hex_color,roughness)
    bs=mat.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Coat Weight"].default_value=coat
    bs.inputs["Sheen Weight"].default_value=sheen
    return mat

class RoomProps(Studio):
    def __init__(self):
        self.clay=finish_material("Unglazed earthenware","cb8065",.69)
        self.clay_line=finish_material("Tooled warm clay","b86c55",.63)
        self.celadon=finish_material("Crème celadon glazed stoneware","e1d9b6",.32,coat=.32)
        self.celadon_line=finish_material("Sage slip glaze","9fae9a",.39,coat=.16)
        self.soil=finish_material("Potting mix","695142",.94)
        self.grit=[finish_material("Potting mix • aggregate "+str(i),h,.87) for i,h in enumerate(("94745b","5f483a","baa486"))]
        self.stem=finish_material("Plant stems","779455",.58)
        self.vein=finish_material("Young leaf ribs","9db384",.53)
        self.leaves=[finish_material("Leaf • "+name,h,.49,coat=.13) for name,h in [
            ("sage","80a377"),("olive","61875a"),("spring","a5b780"),("jade","739980")]]
        self.rubber=finish_material("Slipper • gum rubber","bd846b",.76)
        self.lining=finish_material("Slipper • brushed fleece","f4d4ba",.84,.35)
        self.textile=finish_material("Slipper • rose felt","dc9c99",.82,.28)
        self.binding=finish_material("Slipper • edge binding","b97a77",.79,.2)
        self.thread=finish_material("Slipper • ivory thread","f6dac9",.85,.19)
        self.reed=[finish_material("Basket • rattan "+str(i),h,.71) for i,h in enumerate(("bd9063","e0b98b","d3a477"))]
        self.linen=finish_material("Basket • blue linen","8baeb7",.83,.35)

    def asset(self, key, name, category, mass, description, make):
        c=bpy.data.collections.new(name)
        c.use_fake_user=True
        self.collection=c
        make()
        c.asset_mark()
        c.asset_data.description=description
        for tag in ("Purrlock Holmes","Tea room",category):
            c.asset_data.tags.new(tag)
        c["asset_id"]=key
        c["category"]=category
        c["mass_kg"]=mass
        return c

    def pot(self, stoneware):
        # One connected ceramic shell: foot, curved body, rolled mouth, deep well.
        profile=[(.001,.017),(.20,.017),(.218,.005),(.251,.006),(.268,.032),
                 (.258,.065),(.283,.102),(.314,.205),(.345,.358),(.354,.443),
                 (.371,.458),(.379,.482),(.368,.505),(.345,.511),(.323,.494),
                 (.316,.468),(.308,.390),(.276,.233),(.238,.128),(.196,.089),(.001,.089)]
        body,accent=(self.celadon,self.celadon_line) if stoneware else (self.clay,self.clay_line)
        self.lathe("Planter • formed lip, interior and foot",profile,body)
        for z,r in ((.102,.282),(.125,.293),(.425,.353)):
            self.band("Turned decorative line",r,z,.008,accent)
        if not stoneware:
            self.lathe("Drainage tray • rounded rim",[(.001,.006),(.259,.006),(.308,.012),
                       (.324,.033),(.33,.056),(.322,.072),(.305,.076),(.294,.060),(.28,.033),(.001,.033)],
                       self.clay_line)

    def leaf(self, name, start, direction, pitch, length, width, mat, phase, lance):
        # A cambered, tapered blade with a thin underside, plus its own bowed midrib.
        axis=Vector((math.cos(direction),math.sin(direction),0))
        side=Vector((-axis.y,axis.x,0))
        root=Vector(start)
        def point(t,v):
            span=width*max(0,math.sin(math.pi*t))**(.83 if lance else .53)*(1.06-.23*t)
            center=root+axis*(length*t)+side*(.055*length*math.sin(math.pi*t))
            center.z+=length*(pitch*t+.40*math.sin(math.pi*t)-.27*t*t)
            p=center+side*(v*max(.002,span))
            p.z+=.12*v*span*math.sin(phase+3*t)-(.24*v*v)*span
            return p
        rows,cols=21,9
        verts=[tuple(point(i/(rows-1),-1+2*j/(cols-1))) for i in range(rows) for j in range(cols)]
        faces=[(i*cols+j,(i+1)*cols+j,(i+1)*cols+j+1,i*cols+j+1) for i in range(rows-1) for j in range(cols-1)]
        blade=self.mesh(name,verts,faces,mat)
        thick=blade.modifiers.new("Thin living blade","SOLIDIFY");thick.thickness=.008
        q=[tuple(point(t,0)+Vector((0,0,.006))) for t in (0,.14,.36,.59,.79,.93)]
        self.tube("Leaf midrib",q,[.012,.010,.008,.006,.004,.0015],self.vein,axis=(0,0,1),samples=2,sections=8)
        if not lance:
            for t in (.33,.55,.72):
                for sign in (-1,1):
                    vein=[tuple(point(t+u*.14,sign*u*.77)+Vector((0,0,.004))) for u in (0,.34,.68,1)]
                    self.tube("Subtle branching vein",vein,[.004,.003,.002,.001],self.vein,axis=(0,0,1),samples=2,sections=8)

    def plant(self, lance):
        self.lathe("Soil • shallow soft mound",[(.002,.000),(.306,.000),(.315,.010),(.308,.022),(.21,.040),(.001,.044)],self.soil)
        # Geometry, not noisy masks, gives the soil surface depth.
        for i in range(16):
            a=i*2.39996323;r=.281*math.sqrt((i+.5)/16)
            sx=.014+.004*(i%4)
            self.el("Soil aggregate",(r*math.cos(a),r*math.sin(a),.040-.075*r),(sx,sx*.67,.011),self.grit[i%3])
        for i,(a,h,reach,L,W,pitch) in enumerate([
          (.15,.48,.17,.34,.115,.34),(1.24,.60,.16,.38,.126,.49),(2.30,.38,.19,.41,.128,.25),
          (3.47,.55,.17,.39,.122,.43),(4.42,.31,.17,.44,.113,.20),(5.55,.45,.22,.34,.11,.35),
          (2.81,.68,.06,.26,.082,.66),(5.02,.64,.075,.30,.071,.60)]):
            d=Vector((math.cos(a),math.sin(a),0))
            end=d*reach+Vector((0,0,h*(1.03 if lance else .89)))
            start=d*.041
            bend=d*(reach*.43)+Vector((0,0,h*.42))
            self.tube("Curved stem",[tuple(start),tuple(bend),tuple(end)],[.019,.014,.009],self.stem,axis=(0,0,1))
            self.leaf("Sculpted tapered leaf",end,a,pitch,L*(1.08 if lance else 1),W*(.67 if lance else 1),self.leaves[i%4],i,lance)

    def slippers(self):
        for side,x,y,yaw in [(-1,-.251,-.021,-.14),(1,.244,.029,.19)]:
            self.slipper(side,x,y,yaw)

    def slipper(self,side,x,y,yaw):
        def transform(p):
            a,b,c=p
            return (x+math.cos(yaw)*a-math.sin(yaw)*b,y+math.sin(yaw)*a+math.cos(yaw)*b,c)
        def sole_loop(n,w,l,z):
            pts=[]
            for k in range(n):
                a=TAU*k/n
                t=math.sin(a)
                width=w*(.89+.17*t-.08*math.exp(-((t+.22)/.3)**2))
                pts.append(transform((math.cos(a)*width+side*.025*t,t*l,z+.026*max(t,0)**4)))
            return pts
        # Outsole, welt and footbed share the same asymmetric last.
        sections=[(.18,.326,.006),(.199,.355,.019),(.205,.361,.044),(.199,.354,.077),(.186,.338,.091),(.173,.323,.096)]
        n=56
        pts=sum((sole_loop(n,w,l,z) for w,l,z in sections),[])
        faces=[tuple(range(n-1,-1,-1))]
        for r in range(len(sections)-1):
            faces.extend((r*n+i,r*n+(i+1)%n,(r+1)*n+(i+1)%n,(r+1)*n+i) for i in range(n))
        faces.append(tuple(range((len(sections)-1)*n,len(sections)*n)))
        o=self.mesh("Shaped gum sole and fleece footbed",pts,faces,self.rubber)
        o.data.materials.append(self.binding);o.data.materials.append(self.lining)
        for poly in o.data.polygons:
            poly.material_index=0 if poly.index<=n*2 else 1 if poly.index<=n*4 else 2
        # Domed fabric vamp, open at the heel. The lining is exposed at the rim.
        def vamp(t,a,inner=False):
            yy=-.082+.427*t
            radius=max(.006, .198*(.91+.11*t)*math.sqrt(max(.0001,1-t**3.2)))
            rise=.191*(1-.21*t)*math.sqrt(max(.0001,1-t**4))
            return transform((side*.025*(yy/.35)+math.cos(a)*radius*(.93 if inner else 1),
                    yy+.057*math.sin(a)*(1-t)**2-(.014 if inner else 0),
                    .076+.035*t**3+math.sin(a)*(rise-(.017 if inner else 0))))
        nr,nc=23,25
        for inner,mat in [(False,self.textile),(True,self.lining)]:
            verts=[vamp(i/(nr-1),math.pi*j/(nc-1),inner) for i in range(nr) for j in range(nc)]
            faces=[(i*nc+j,(i+1)*nc+j,(i+1)*nc+j+1,i*nc+j+1) for i in range(nr-1) for j in range(nc-1)]
            self.mesh("Padded felt toe" if not inner else "Inner fleece vamp",verts,[f[::-1] for f in faces] if inner else faces,mat)
        arc=[vamp(0,math.pi*j/14) for j in range(15)]
        self.tube("Rolled textile opening seam",arc,[.012]*len(arc),self.binding,axis=(0,1,0))
        for j in range(2,22,2):
            a=math.pi*j/23
            sew=[Vector(vamp(.047,a+p)) for p in (-.023,.023)]
            for p in sew:
                p.z+=.0035
            self.tube("Small running stitch",sew,[.004,.004],self.thread,axis=(0,1,0))
        for dx,dy,r in [(-.04,.194,.028),(-.001,.152,.034),(.04,.194,.028)]:
            src=Vector(vamp((dy+.082)/.427,math.acos(max(-.95,min(.95,dx/.182)))))
            src.z+=.007
            self.el("Embroidered paw appliqué",tuple(src),(r,r*.78,.009),self.thread)

    def basket(self):
        # The liner hides the structural core inside, leaving visible woven geometry outside.
        self.lathe("Basket core",[(.001,.013),(.39,.013),(.47,.025),(.498,.083),(.538,.24),
                   (.577,.46),(.584,.523),(.553,.546),(.531,.511),(.492,.337),(.446,.093),(.001,.070)],self.reed[0])
        for i in range(11):
            z=.059+i*.042
            radius=.493+(z-.059)*.20
            pts=[]
            for j in range(145):
                a=TAU*j/144
                r=radius+.011*math.cos(24*a+math.pi*i)
                pts.append((r*math.cos(a),r*math.sin(a),z+.005*math.sin(24*a+math.pi*i)))
            self.tube("Over-under rattan weft",pts,[.022]*len(pts),self.reed[1+i%2],axis=(0,0,1),samples=1,sections=8)
        for j in range(48):
            a=TAU*j/48
            pts=[]
            for i in range(12):
                z=.045+i*.043
                r=.489+.204*(z-.059)+.014*math.cos(math.pi*(j+i+1))
                pts.append((r*math.cos(a),r*math.sin(a),z))
            self.tube("Woven upright reed",pts,[.012]*len(pts),self.reed[j%3],axis=(-math.sin(a),math.cos(a),0),samples=1,sections=8)
        self.lathe("Basket rolled reed rim",[(.557,.496),(.585,.494),(.612,.510),(.619,.536),
                   (.603,.554),(.571,.558),(.547,.542),(.546,.519),(.557,.496)],self.reed[1])
        self.lathe("Blue linen lining with scalloped drop",[(.002,.080),(.399,.080),(.453,.121),
                   (.481,.242),(.515,.419),(.535,.533),(.555,.548),(.578,.545),(.592,.525),(.589,.499)],
                   self.linen,wave=.008,wave_n=14)

def scene_props():
    art=RoomProps()
    return {key:art.asset(key,title,category,mass,desc,build) for key,title,category,mass,desc,build in [
        ("clay_planter","Room · Terracotta planter","ceramic",.82,"Real interior and rolled lip over a separate drainage tray.",lambda:art.pot(False)),
        ("celadon_planter","Room · Celadon planter","ceramic",.73,"Glazed stoneware with a curved interior and incised bands.",lambda:art.pot(True)),
        ("rubber_plant","Room · Rubber plant","botanical",.29,"Cambered broad leaves, midribs and branching veins.",lambda:art.plant(False)),
        ("lance_plant","Room · Lanceleaf plant","botanical",.23,"Narrow spring leaves on asymmetric curved stems.",lambda:art.plant(True)),
        ("felt_slippers","Room · Felt slippers","textile",.34,"A mirrored pair with padded open vamps, fleece, outsole and stitches.",art.slippers),
        ("reed_basket","Room · Linen-lined rattan basket","wicker",.57,"Woven over-under rattan with a rolled rim and cloth lining.",art.basket),
    ]}

def place(collection,location,yaw=0,scale=1):
    obj=bpy.data.objects.new("Room asset | "+collection["asset_id"],None)
    bpy.context.scene.collection.objects.link(obj)
    obj.instance_type='COLLECTION'
    obj.instance_collection=collection
    obj.location=location
    obj.rotation_euler.z=yaw
    obj.scale=(scale,)*3
    return obj
