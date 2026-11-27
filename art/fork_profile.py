"""Fork profiles traced from front artwork and the supplied side photograph.

Front coordinates are artwork pixels. Side coordinates follow the visible
lower edge of the near side, rather than the projected width of the fork face.
The final tine segment follows a single rising tangent in the side plane.
"""
import math

LEN=.938/745
FACE_START=86.
FACE_END=1446.
SPLIT=1066.
FRONT=(
 (86,392,396),(92,369,420),(110,352,435),(140,340,450),(177,334,455),
 (223,334,455),(300,338,450),(420,348,439),(550,356,430),
 (680,362,423),(759,362,423),(814,360,426),(852,355,431),
 (880,347,440),(899,337,450),(922,319,469),(944,302,487),
 (965,291,497),(990,285,503),(1026,282,507),(1066,282.5,506)
)
# Object length fraction from the handle cap. Units for lower edge are
# reference pixels relative to the lowest rim. Fork points left in the photo.
SIDE=(
 (0,49),(.028,49),(.075,48),(.24,54),(.44,63),(.55,68),
 (.583,66),(.619,55),(.656,31),(.693,8),(.727,0),
 (.755,2.5),(.79,13),(.815,24),(.87,56.34),(1,132.78)
)

def spline(points,x,axis):
    sec=[(b[axis]-a[axis])/(b[0]-a[0]) for a,b in zip(points,points[1:])]
    tang=[sec[0]]+[2*a*b/(a+b) if a*b>0 else 0 for a,b in zip(sec,sec[1:])]+[sec[-1]]
    for i,(a,b) in enumerate(zip(points,points[1:])):
        if x<=b[0]:
            d=b[0]-a[0];t=max(0,(x-a[0])/d)
            return ((2*t**3-3*t**2+1)*a[axis]+(-2*t**3+3*t**2)*b[axis]
                     +(t**3-2*t*t+t)*d*tang[i]+(t**3-t*t)*d*tang[i+1])
    return points[-1][axis]

def smooth(t):
    t=max(0,min(1,t))
    return t*t*(3-2*t)

def section(row,finger):
    u=(780-row)/745
    x=FACE_START+(FACE_END-FACE_START)*u
    if x<=SPLIT:
        top=spline(FRONT,x,1); bottom=spline(FRONT,x,2)
        # Slot roots are at the seam between bands. Converge gradually
        # toward the slightly asymmetric spacing of the reference.
        seams=(top,333.,394.5,454.,bottom)
        t=smooth((x-1000)/66)
        lines=[(1-t)*(top+(bottom-top)*k/4)+t*seams[k] for k in range(5)]
        lo,hi=lines[finger:finger+2]
    else:
        t=(x-SPLIT)/(FACE_END-SPLIT)
        cap=math.sqrt(max(.0001,1-(max(0,(x-1431)/15))**2))
        g=math.sqrt(max(0,1-(1-min(1,(x-SPLIT)/16))**2))
        starts=((282.5,333.),(333.,394.5),(394.5,454.),(454.,506.))
        ends=((294,316),(352.5,375),(412.5,435),(472,495))
        a,b=starts[finger];c,d=ends[finger]
        left_open=0 if finger==0 else 13.
        right_open=0 if finger==3 else 13.
        lo=(1-t)*a+t*c+(1-t)*left_open*g
        hi=(1-t)*b+t*d-(1-t)*right_open*g
        mid=(lo+hi)/2
        lo,hi=mid+(lo-mid)*cap,mid+(hi-mid)*cap
    # The room transform uses a consistent transverse scale and centered grip.
    return row,143+(lo-394.5)*.632,143+(hi-394.5)*.632

def mesh_xy(p,q):
    return ((p-143)*LEN,-.457+(780-q)*LEN)

def mesh_z(p,q):
    u=(780-q)/745
    # The lower rim reaches the table at the leading bowl of the fork;
    # the two ascending edges are made from one real swept steel surface.
    height=.016+spline(SIDE,u,1)*.938/1400
    t=min(1,abs(p-143)/44)
    crown=.003*(1-t*t)*(1-smooth((u-.61)/.14))
    return height+crown
