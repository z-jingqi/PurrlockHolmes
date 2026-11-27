"""Exact object-index picking from the saved scene. Run inside Blender."""
import bpy, struct, zlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def bake(path):
    scene = bpy.context.scene
    deps = bpy.context.evaluated_depsgraph_get()
    verts, polys, ids = [], [], []
    for obj in scene.objects:
        if obj.type not in {'MESH','CURVE'} or obj.hide_render:
            continue
        ev = obj.evaluated_get(deps)
        mesh = ev.to_mesh()
        start = len(verts)
        verts.extend(ev.matrix_world @ p.co for p in mesh.vertices)
        for p in mesh.polygons:
            polys.append(tuple(start+j for j in p.vertices))
            ids.append(obj.get('pick_id',0))
        ev.to_mesh_clear()
    bvh = BVHTree.FromPolygons(verts, polys)
    w,h = scene.render.resolution_x, scene.render.resolution_y
    camera = scene.camera
    frame = camera.data.view_frame(scene=scene)
    left,right = min(p.x for p in frame),max(p.x for p in frame)
    bottom,top = min(p.y for p in frame),max(p.y for p in frame)
    rot = camera.matrix_world.to_3x3()
    origin = camera.matrix_world.translation
    x_axis = rot @ Vector(((right-left)/w,0,0))
    start = rot @ Vector((left+(right-left)*.5/w,top-(top-bottom)*.5/h,frame[0].z))
    y_axis = rot @ Vector((0,(bottom-top)/h,0))
    rays = [x*x_axis for x in range(w)]
    buf = bytearray((w*3+1)*h)
    for y in range(h):
        base = start + y*y_axis
        for x, dx in enumerate(rays):
            _,_,face,_ = bvh.ray_cast(origin,base+dx)
            if face is not None:
                buf[y*(w*3+1)+1+3*x] = ids[face]*32
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag+data))
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(buf,9))+chunk(b'IEND',b''))
if __name__=='__main__':
    bake(Path(bpy.data.filepath).resolve().parents[1]/'assets/pick.png')
