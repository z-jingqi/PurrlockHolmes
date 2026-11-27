extends Control
## Standalone live 3D contact experiment. The camera never moves.
const MODEL := preload("res://physics/room.glb")
const CLOTH_SCRIPT := preload("res://physics/towel.gd")
const TAKE := ["table","cup","plate","fork"]
const WORLD := 1
const ITEMS := 2
const SELECT := 32
const CLOSED := WORLD | ITEMS | SELECT | 4 | 8 | 16
const EXPOSURE := .25
const RENDER_SIZE := Vector2(1320, 980)
const TOP := 74.0
const FOOTER := 92.0
const BOX := preload("res://assets/paw-box.svg")
const UI_FONT := preload("res://physics/ui-zh.otf")

var view: SubViewport
var world: Node3D
var camera: Camera3D
var cloth: MeshInstance3D
var table: StaticBody3D
var groups: Dictionary = {}
var configs: Dictionary = {
	"cup": [Vector3(-.79,1.23,.39),Vector3(.65,.43,.52),4,.24],
	"plate": [Vector3(.08,1.10,1.30),Vector3(.99,.19,.99),8,.32],
	"fork": [Vector3(.70,1.067,.73),Vector3(.45,.050,.71),16,.12],
	"book": [Vector3(-1.34,1.052,1.32),Vector3(.82,.09,.71),ITEMS,.28],
	"notebook": [Vector3(.83,1.055,0),Vector3(.80,.09,.58),ITEMS,.25],
	"orange": [Vector3(.90,1.164,1.46),Vector3(.36,.34,.36),ITEMS,.16],
}
var taken: Dictionary = {}
var corrections: Dictionary = {}
var settle := -1.0
var visibility_wait := 0.0
var pending_tap := Vector2(-1,-1)
var pan := Vector2.ZERO
var start := Vector2.ZERO
var start_pan := Vector2.ZERO
var pointer := -2
var dragged := false
var hud: Label
var caption: Label
var progress: Label
var smoke := false
var ticks := 0
var starting_y := 0.0
var covered_case := false
var blocked_before := -1.0
var nominal_ok := false
var draped_max := 0.0

func _ready() -> void:
	_build_view()
	_build_ui()
	smoke="--test-physics" in OS.get_cmdline_user_args()
	covered_case="--test-covered" in OS.get_cmdline_user_args()
	if smoke:
		starting_y = groups["cup"].position.y
		_log_start()

func _build_view() -> void:
	view = SubViewport.new()
	view.size = Vector2i(RENDER_SIZE)
	view.own_world_3d = true
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	view.msaa_3d = Viewport.MSAA_2X
	add_child(view)
	world = Node3D.new()
	view.add_child(world)
	var env := WorldEnvironment.new()
	env.environment=Environment.new()
	env.environment.background_mode=Environment.BG_COLOR
	env.environment.background_color=Color("#ebdcc8")
	env.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color=Color("#ffeddf")
	env.environment.ambient_light_energy=.68
	world.add_child(env)
	_light(Vector3(-5,9,7),1.30,Color("#fff2db"),true)
	_light(Vector3(5,7,-4),.48,Color("#deefff"),false)
	camera=Camera3D.new()
	world.add_child(camera)
	camera.position=Vector3(8.0,14.4,15.6)
	camera.look_at(Vector3(0,1.1,-.06))
	camera.keep_aspect=Camera3D.KEEP_WIDTH
	camera.fov=42.7
	camera.current=true
	var stage := Node3D.new()
	world.add_child(stage)
	table=StaticBody3D.new()
	table.set_meta("item","table")
	table.collision_layer=WORLD|SELECT
	table.position=Vector3(-.11,.89,.82)
	world.add_child(table)
	_add_box(table,Vector3(3.83,.22,2.53))
	for x in [-1.62,1.59]:
		for z in [-.94,.94]:
			_add_box(table,Vector3(.21,.74,.21),Vector3(x,-.43,z))
	groups["table"]=table
	for k in configs:
		var config: Array=configs[k]
		var body := RigidBody3D.new()
		body.name=k
		body.set_meta("item",k)
		body.position=config[0]
		body.mass=config[3]
		body.collision_layer=config[2]
		body.collision_mask=CLOSED
		body.freeze=true
		body.linear_damp=1.8
		body.angular_damp=3.7
		body.continuous_cd=true
		var material := PhysicsMaterial.new()
		material.friction=.67 if k in ["book","notebook"] else .43
		material.bounce=.21 if k=="orange" else .035
		body.physics_material_override=material
		world.add_child(body)
		if k=="cup": _add_cylinder(body,.286,.43,Vector3(-.058,-.016,0))
		elif k=="plate": _add_cylinder(body,.49,.18)
		elif k=="orange": _add_sphere(body,.17)
		elif k=="fork":
			_add_box(body,Vector3(.095,.052,.55),Vector3(-.093,0,.23),-.50)
			_add_box(body,Vector3(.29,.052,.225),Vector3(.085,0,-.13),-.50)
		else: _add_box(body,config[1])
		groups[k]=body
	var imported := MODEL.instantiate() as Node3D
	stage.add_child(imported)
	_reparent_meshes(imported)
	_floor_block(Vector3(0,-.08,0), Vector3(12.7,.28,9.5))
	_floor_block(Vector3(-.46,.106,1.07), Vector3(6.65,.072,5.18))
	_floor_block(Vector3(-3.49,.65,-2.35), Vector3(3.78,1.13,2.1))
	_floor_block(Vector3(3.84,.79,-2.78), Vector3(3.23,1.57,1.19))
	_floor_block(Vector3(0,2.02,-4.56),Vector3(12.5,4.3,.24))
	_floor_block(Vector3(-6.18,2.02,-2.58),Vector3(.22,4.3,4.0))
	cloth = MeshInstance3D.new()
	cloth.set_script(CLOTH_SCRIPT)
	world.add_child(cloth)

func _light(pos: Vector3,energy: float,tint: Color,use_shadow: bool) -> void:
	var light := DirectionalLight3D.new()
	world.add_child(light)
	light.position=pos
	light.look_at(Vector3.ZERO)
	light.light_energy=energy
	light.light_color=tint
	light.shadow_enabled=use_shadow

func _add_box(body: CollisionObject3D, dims: Vector3, at := Vector3.ZERO, yaw := 0.0) -> void:
	var c:=CollisionShape3D.new()
	var shape:=BoxShape3D.new()
	shape.size=dims
	c.shape=shape
	c.position=at
	c.rotation.y=yaw
	body.add_child(c)

func _add_cylinder(body: CollisionObject3D,radius: float,height: float,at:=Vector3.ZERO) -> void:
	var c:=CollisionShape3D.new()
	var shape:=CylinderShape3D.new()
	shape.radius=radius
	shape.height=height
	c.position=at
	c.shape=shape
	body.add_child(c)

func _add_sphere(body: CollisionObject3D,radius: float) -> void:
	var c:=CollisionShape3D.new()
	var shape:=SphereShape3D.new()
	shape.radius=radius
	c.shape=shape
	body.add_child(c)

func _floor_block(pos: Vector3,dims: Vector3) -> void:
	var block:=StaticBody3D.new()
	block.collision_layer=WORLD
	block.position=pos
	world.add_child(block)
	_add_box(block,dims)

func _reparent_meshes(node: Node) -> void:
	for child in node.get_children():
		_reparent_meshes(child)
	if node is MeshInstance3D:
		var key := String(node.name).get_slice("__",0)
		if groups.has(key):
			node.reparent(groups[key],true)
			_material_detail(node,key)

func _material_detail(node: MeshInstance3D,key: String) -> void:
	for i in range(node.mesh.get_surface_count()):
		var source := node.mesh.surface_get_material(i) as StandardMaterial3D
		if not source: continue
		var m:=source.duplicate() as StandardMaterial3D
		if key in ["cup","plate"]:
			m.roughness=.24
			m.metallic=.0
			m.metallic_specular=.61
			m.clearcoat_enabled=true
			m.clearcoat=.35
		elif key=="fork":
			m.roughness=.31
			# A restrained metallic blend stays readable even without an HDRI.
			m.metallic=.48
			m.metallic_specular=.78
		elif key=="table": m.roughness=.72
		node.set_surface_override_material(i,m)

func _label(s: String,sz: int,pos: Vector2) -> Label:
	var l:=Label.new()
	l.text=s
	l.position=pos
	l.mouse_filter=Control.MOUSE_FILTER_IGNORE
	l.add_theme_font_override("font",UI_FONT)
	l.add_theme_font_size_override("font_size",sz)
	l.add_theme_color_override("font_color",Color("#51382f"))
	add_child(l)
	return l

func _button(s: String, callback: Callable)->Button:
	var b:=Button.new()
	b.text=s
	b.add_theme_font_override("font",UI_FONT)
	b.pressed.connect(callback)
	add_child(b)
	return b

func _build_ui() -> void:
	hud=_label("福尔猫斯 · 物理试验",25,Vector2(17,8))
	caption=_label("先点走桌子，再收起落地的餐具。",14,Vector2(19,45))
	progress=_label("桌面四件   0/4",17,Vector2.ZERO)
	var restart:=_button("重来",func():get_tree().reload_current_scene())
	var back:=_button("原版",_back)
	var fit:=func():
		_clamp_pan()
		progress.position=Vector2(maxf(0,(size.x-progress.get_minimum_size().x)*.5),size.y-FOOTER+3)
		restart.position=Vector2(size.x-65,size.y-46)
		back.position=Vector2(16,size.y-46)
		queue_redraw()
	resized.connect(fit)
	fit.call()

func _back() -> void:
	if OS.has_feature("web"):
		JavaScriptBridge.get_interface("location").assign("/")
	else:
		get_tree().change_scene_to_file("res://main.tscn")

func _refresh_caption() -> void:
	progress.text="桌面四件   %d/4"%taken.size()
	progress.position.x=(size.x-progress.get_minimum_size().x)*.5
	caption.text="四件都收好了！" if taken.size()==4 else "桌子移开了，收起落地的餐具。"
	queue_redraw()

func _field() -> Rect2:
	return Rect2(0,TOP,size.x,maxf(1.0,size.y-TOP-FOOTER))

func _scale() -> float:
	var bounds:=_field().size
	return maxf(bounds.x/RENDER_SIZE.x,bounds.y/RENDER_SIZE.y)*1.12

func _origin() -> Vector2:
	var field:=_field()
	return field.position+(field.size-RENDER_SIZE*_scale())*.5+pan

func _clamp_pan() -> void:
	var limit:=(RENDER_SIZE*_scale()-_field().size)*.5
	pan=pan.clamp(-limit,limit)

func _draw() -> void:
	if not view:return
	draw_texture_rect(view.get_texture(),Rect2(_origin(),RENDER_SIZE*_scale()),false)
	draw_rect(Rect2(0,0,size.x,TOP),Color("#fff7e9"))
	draw_rect(Rect2(0,size.y-FOOTER,size.x,FOOTER),Color("#fff7e9"))
	draw_texture_rect(BOX,Rect2(size.x*.5-45,size.y-63,90,63),false)
	draw_line(Vector2(0,TOP),Vector2(size.x,TOP),Color("#dec3a8"))
	draw_line(Vector2(0,size.y-FOOTER),Vector2(size.x,size.y-FOOTER),Color("#dec3a8"))

func _begin(id: int, at: Vector2) -> void:
	if pointer!=-2 or not _field().has_point(at):return
	start=at
	start_pan=pan
	pointer=id
	dragged=false

func _move(id: int,at: Vector2) -> void:
	if pointer!=id:return
	if at.distance_to(start)>7:dragged=true
	if dragged:
		pan=start_pan+at-start
		_clamp_pan()
		queue_redraw()

func _end(id: int,at: Vector2,canceled: bool) -> void:
	if pointer!=id:return
	if not canceled:
		_move(id,at)
		if not dragged and _field().has_point(at):pending_tap=(at-_origin())/_scale()
	pointer=-2

func _notification(what:int) -> void:
	if what==NOTIFICATION_WM_WINDOW_FOCUS_OUT:
		pointer=-2
		pending_tap=Vector2(-1,-1)

func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.device!=InputEvent.DEVICE_ID_EMULATION and event.button_index==MOUSE_BUTTON_LEFT:
		if event.pressed: _begin(-1,event.position)
		else: _end(-1,event.position,event.canceled)
	elif event is InputEventMouseMotion and event.device!=InputEvent.DEVICE_ID_EMULATION:
		_move(-1,event.position)
	elif event is InputEventScreenTouch:
		if event.pressed and not event.canceled: _begin(event.index,event.position)
		else: _end(event.index,event.position,event.canceled)
	elif event is InputEventScreenDrag:
		_move(event.index,event.position)

func _ray(pixel: Vector2, mask: int, selective: bool=false) -> Dictionary:
	var a:=camera.project_ray_origin(pixel)
	var d:=camera.project_ray_normal(pixel)
	var q:=PhysicsRayQueryParameters3D.create(a,a+d*55.0,mask)
	var hit:=view.find_world_3d().direct_space_state.intersect_ray(q)
	if selective and not hit.is_empty() and cloth.blocks_ray(a,d,a.distance_to(hit.position)):
		return {}
	return hit

func _pick_scene(pixel: Vector2) -> void:
	var hit:=_ray(pixel,CLOSED,true)
	if hit.is_empty():return
	var item: String=hit.collider.get_meta("item","")
	if item=="table" and not taken.has("table"):_release_table()
	elif item in TAKE and item!="table" and taken.has("table") and settle>.36:
		_take_item(item)

func _disable_support(node: CollisionObject3D) -> void:
	node.collision_layer=0
	node.collision_mask=0
	for c in node.get_children():
		if c is CollisionShape3D:c.set_deferred("disabled",true)

func _release_table() -> void:
	taken["table"]=true
	_disable_support(table)
	# The support vanishes now; shrink only the outgoing visual.
	var tween:=create_tween().set_parallel(true)
	tween.tween_property(table,"position",table.position+Vector3(0,.72,-.20),.31).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tween.tween_property(table,"scale",Vector3.ONE*.055,.31).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN)
	tween.chain().tween_callback(table.hide)
	for k in configs:
		var body:=groups[k] as RigidBody3D
		body.freeze=false
		body.sleeping=false
	cloth.release_support()
	settle=0.0
	_refresh_caption()

func _take_item(item: String) -> void:
	if taken.has(item):return
	taken[item]=true
	var body:=groups[item] as RigidBody3D
	body.freeze=true
	_disable_support(body)
	var anim:=create_tween().set_parallel(true)
	anim.tween_property(body,"position",body.position+Vector3(0,.38,0),.22).set_trans(Tween.TRANS_CUBIC)
	anim.tween_property(body,"scale",Vector3.ONE*.04,.22)
	anim.chain().tween_callback(body.hide)
	_refresh_caption()

func _project_target(body: RigidBody3D) -> Rect2:
	var out:=Rect2()
	var primed:=false
	for c in body.get_children():
		if not c is MeshInstance3D:continue
		var bounds: AABB=c.get_aabb()
		for k in range(8):
			var p:=camera.unproject_position(c.global_transform * bounds.get_endpoint(k))
			if not primed:
				out=Rect2(p,Vector2.ZERO)
				primed=true
			else: out=out.expand(p)
	return out

func _coverage(body: RigidBody3D) -> Dictionary:
	var bound:=_project_target(body)
	var samples:=0
	var clear_count:=0
	var blockers: Dictionary={}
	for y in range(14):
		for x in range(14):
			var p:=bound.position+bound.size*Vector2((x+.5)/14.0,(y+.5)/14.0)
			var solo:=_ray(p,body.collision_layer)
			if solo.is_empty() or solo.collider!=body:continue
			samples+=1
			if not Rect2(Vector2.ZERO,RENDER_SIZE).has_point(p):continue
			var actual:=_ray(p,CLOSED)
			if actual.is_empty():continue
			if actual.collider==body:
				var eye:=camera.project_ray_origin(p)
				if not cloth.blocks_ray(eye,camera.project_ray_normal(p),eye.distance_to(actual.position)):
					clear_count+=1
			elif actual.collider is RigidBody3D:
				var key:String=actual.collider.get_meta("item","")
				blockers[key]=int(blockers.get(key,0))+1
	return {"ratio":float(clear_count)/maxi(1,samples),"blockers":blockers}

func _safe_spot(body: RigidBody3D,k: String) -> Vector3:
	var floor_y: float=.145+configs[k][1].y*.5
	var best:=Vector3.INF
	var distance:=INF
	for z in [.1,.77,1.48,2.33,3.25]:
		for x in [-3.6,-2.8,-2.1,-1.4,-.55,.2,.92,1.66,2.45,3.30]:
			var spot := Vector3(x,floor_y,z)
			var p:=camera.unproject_position(spot)
			if not Rect2(135,145,RENDER_SIZE.x-270,RENDER_SIZE.y-270).has_point(p):continue
			if cloth.bounds.grow(.35).has_point(spot):continue
			var clear_space:=true
			for other in configs:
				if other!=k and not taken.has(other):
					var d:Vector3=groups[other].global_position-spot
					if Vector2(d.x,d.z).length()<.80:
						clear_space=false
						break
			if not clear_space:continue
			# Verify a visible ray to the proposed location. The hit may be floor, but not before the proxy center.
			var estimate:=Vector3(configs[k][1].x,configs[k][1].y,configs[k][1].z)
			for off in [Vector3.ZERO,Vector3(estimate.x*.32,0,0),Vector3(-estimate.x*.32,0,0),
					Vector3(0,0,estimate.z*.34),Vector3(0,0,-estimate.z*.34),Vector3(0,estimate.y*.36,0)]:
				var aim: Vector3=spot+off
				var sample:=camera.unproject_position(aim)
				var eye:=camera.project_ray_origin(sample)
				var facing:=camera.project_ray_normal(sample)
				var depth:=eye.distance_to(aim)
				var existing:=_ray(sample,CLOSED)
				if cloth.blocks_ray(eye,facing,depth) or (not existing.is_empty() and existing.collider!=body and eye.distance_to(existing.position)<depth-.04):
					clear_space=false
					break
			if not clear_space:continue
			var d:=body.global_position.distance_squared_to(spot)
			if d<distance:
				best=spot
				distance=d
	return best

func _correct(k: String) -> void:
	var body:=groups[k] as RigidBody3D
	var sample:=_coverage(body)
	if sample.ratio>=EXPOSURE:return
	var n:=int(corrections.get(k,0))
	corrections[k]=n+1
	var list: Dictionary=sample.blockers
	if n<2 and not list.is_empty():
		var key = list.keys()[0]
		for candidate in list:
			if list[candidate]>list[key]:key=candidate
		var blocker:=groups.get(key) as RigidBody3D
		if blocker and not taken.has(key):
			var d:=blocker.global_position-body.global_position
			d.y=0
			if d.length_squared()<.005:d=Vector3(.5,0,-1)
			blocker.sleeping=false
			blocker.apply_central_impulse((d.normalized()*.70+Vector3.UP*.12)*blocker.mass)
			return
	if not body.freeze or n<4:
		# Failsafe after an unhelpful contact, not the normal landing path.
		var spot:=_safe_spot(body,k)
		if not spot.is_finite():return
		body.freeze=true
		body.linear_velocity=Vector3.ZERO
		body.angular_velocity=Vector3.ZERO
		var slide:=create_tween().set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)
		slide.tween_property(body,"global_transform",Transform3D(Basis.IDENTITY,spot),.22).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)

func _physics_process(dt: float) -> void:
	ticks+=1
	cloth.advance(dt)
	if pending_tap.x>=0:
		_pick_scene(pending_tap)
		pending_tap=Vector2(-1,-1)
	if settle>=0.0:
		settle+=dt
		visibility_wait-=dt
		if settle>.75 and visibility_wait<=0.0 and taken.size()<4:
			visibility_wait=.35
			for k in ["cup","plate","fork"]:
				if not taken.has(k):_correct(k)
	if smoke:_smoke_frame()

func _log_start() -> void:
	print("PHYS_TEST started at cup=%.3f; meshes=%d" % [starting_y,groups.cup.get_child_count()])

func _smoke_frame() -> void:
	if ticks==55:
		draped_max = cloth.points[-1].y
		if draped_max>=.89:
			push_error("Towel did not drape off the table")
			get_tree().quit(1)
			return
		_pick_scene(camera.unproject_position(Vector3(-.15,1.0,.57)))
		if not taken.has("table"):
			push_error("Could not click visible table plane")
			get_tree().quit(1)
			return
	if ticks==175:
		var ratios: Dictionary={}
		for key in ["cup","plate","fork"]:ratios[key]=_coverage(groups[key]).ratio
		var ok: bool=groups.cup.position.y<starting_y-.45 and groups.cup.position.y>.10 and cloth.bounds.end.y<.35
		for key in ratios: ok=ok and ratios[key]>=EXPOSURE
		print("PHYS_TEST actual_drop=%s towel_edge_y=%.3f towel_floor_y=%.3f coverage=%s corrections=%s" % [ok,draped_max,cloth.bounds.end.y,ratios,corrections])
		if not covered_case or not ok:
			get_tree().quit(0 if ok else 1)
			return
		nominal_ok=ok
		var book:=groups.notebook as RigidBody3D
		var cup:=groups.cup as RigidBody3D
		var d:=cup.global_position.direction_to(camera.global_position)
		book.freeze=true
		book.global_transform=Transform3D(Basis.looking_at(-d)*Basis(Vector3.RIGHT,PI/2),cup.global_position+d*.46)
		visibility_wait=.15
	if covered_case and ticks==179:
		blocked_before=_coverage(groups.cup).ratio
	if covered_case and ticks==315:
		var after: float=_coverage(groups.cup).ratio
		var ok:=nominal_ok and blocked_before>=0 and blocked_before<EXPOSURE and after>=EXPOSURE
		print("PHYS_TEST forced_cover before=%.3f recovered=%.3f corrections=%s pass=%s" % [blocked_before,after,corrections,ok])
		get_tree().quit(0 if ok else 1)
