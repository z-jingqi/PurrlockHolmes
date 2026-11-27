extends MeshInstance3D
## Lightweight 3D cloth: Verlet, structural, shear and bend constraints.
const COLS := 10
const ROWS := 18
const TOP := 1.016
const FLOOR := .143
const EDGE := 2.075
const WIDTH := .68
const LENGTH := 1.28
var supported := true
var elapsed := 0.0
var points := PackedVector3Array()
var previous := PackedVector3Array()
var anchors := PackedVector3Array()
var links: Array[Vector4] = []
var vertices := PackedInt32Array()
var fibers := PackedColorArray()
var bounds := AABB()

func _ready() -> void:
	var m := StandardMaterial3D.new()
	m.vertex_color_use_as_albedo = true
	m.roughness = .97
	m.metallic_specular = .13
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	material_override = m
	var dx := WIDTH / (COLS-1)
	var dz := LENGTH / (ROWS-1)
	for j in range(ROWS):
		for i in range(COLS):
			var p := Vector3(-.86+i*dx+.025*sin(float(j)*.55),TOP+.008*sin(i*.73),1.48+j*dz)
			points.append(p)
			previous.append(p)
			anchors.append(p)
			var k := j*COLS+i
			if i>0: links.append(Vector4(k,k-1,dx,.90))
			if j>0: links.append(Vector4(k,k-COLS,dz,.92))
			if j>0 and i>0: links.append(Vector4(k,k-COLS-1,sqrt(dx*dx+dz*dz),.65))
			if j>0 and i<COLS-1: links.append(Vector4(k,k-COLS+1,sqrt(dx*dx+dz*dz),.65))
			if i>1: links.append(Vector4(k,k-2,dx*2.0,.36))
			if j>1: links.append(Vector4(k,k-2*COLS,dz*2.0,.55))
			var stripe := j in [2,3,14,15]
			var col := Color("#a6c8c4") if not stripe else Color("#e3efdf")
			if i==0 or i==COLS-1 or j==0 or j==ROWS-1: col = Color("#8caeab")
			fibers.append(col)
			if j>0 and i>0:
				vertices.append_array(PackedInt32Array([k-COLS-1,k-COLS,k,k-COLS-1,k,k-1]))
	update_mesh()

func release_support() -> void:
	supported = false
	elapsed = 0.0

func advance(dt: float) -> void:
	elapsed += dt
	if elapsed > (1.4 if supported else 2.6):return
	var step := minf(dt, 1.0/30.0)
	for k in range(points.size()):
		if supported and k < COLS:
			points[k]=anchors[k]
			previous[k]=points[k]
			continue
		var p := points[k]
		points[k] += (p-previous[k])*.973 + Vector3(0,-9.81*step*step,0)
		previous[k] = p
	for it in range(7):
		for l in links:
			var a := int(l.x)
			var b := int(l.y)
			var d := points[a]-points[b]
			var distance := d.length()
			if distance < .0001: continue
			var c := d*((distance-l.z)/distance)*l.w
			var f_a := 0.0 if supported and a<COLS else 1.0
			var f_b := 0.0 if supported and b<COLS else 1.0
			if f_a+f_b > 0.0:
				points[a]-=c*f_a/(f_a+f_b)
				points[b]+=c*f_b/(f_a+f_b)
		for k in range(points.size()):
			var p := points[k]
			if p.y < FLOOR: p.y=FLOOR
			if supported and p.z < EDGE+.014 and p.x > -2.05 and p.x < 1.84 and p.y<TOP:
				if previous[k].y > .91 or p.z < EDGE-.078: p.y=TOP
				else: p.z=EDGE+.014
			points[k]=p
	update_mesh()

func update_mesh() -> void:
	bounds=AABB(points[0],Vector3.ZERO)
	for p in points: bounds=bounds.expand(p)
	if DisplayServer.get_name() == "headless": return
	var mesh_surface := SurfaceTool.new()
	mesh_surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for k in vertices:
		mesh_surface.set_color(fibers[k])
		mesh_surface.add_vertex(points[k])
	mesh_surface.generate_normals()
	mesh = mesh_surface.commit()

func blocks_ray(from: Vector3, direction: Vector3, distance: float) -> bool:
	if not bounds.grow(.005).intersects_segment(from,from+direction*distance): return false
	for k in range(0,vertices.size(),3):
		var hit = Geometry3D.ray_intersects_triangle(from,direction,points[vertices[k]],points[vertices[k+1]],points[vertices[k+2]])
		if hit is Vector3 and from.distance_squared_to(hit)<distance*distance:
			return true
	return false
