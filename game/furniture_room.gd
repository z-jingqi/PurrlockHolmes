extends Control
## Fixed-camera artwork + 3D contact bodies for the pieces that can move.
const MODEL := preload("res://assets/room.glb")
const BACKDROP := preload("res://assets/room.webp")
const CLOTH_SCRIPT := preload("res://game/towel.gd")
const PROP_DYNAMICS := preload("res://game/prop_dynamics.gd")
const BOX := preload("res://assets/paw-box.svg")
const HINT_RAY := preload("res://assets/hint-ray.png")
const UI_FONT := preload("res://game/ui-zh.otf")
const TARGETS := ["table","chair","cabinet"]
const ART := {
	"table":preload("res://assets/flight-table.webp"),
	"chair":preload("res://assets/flight-chair.webp"),
	"cabinet":preload("res://assets/flight-cabinet.webp")
}
const WORLD := 1
const ITEMS := 2
const SELECT := [4, 8, 16]
const CLOSED := 31
const RENDER_SIZE := Vector2(1200, 896)
const TOP := 74.0
const FOOTER := 94.0
const LIFT := .14
const DURATION := .58
const HINT_SECONDS := 3.0
const EXPOSURE := .25
const SUPPORTS := {
	"table":["cup","plate","fork","book","notebook","orange"],
	"chair":["chair_book"],
	"cabinet":["bowl","plant","cab_book0","cab_book1","cab_book2","cab_book3","cab_stop0","cab_stop1"]
}
# Each entry: model center, collision extents, kg, contact/aerodynamic preset.
const PROPS := {
	"cup": [Vector3(-.79,1.23,.39),Vector3(.60,.43,.52),.31,"ceramic"],
	"plate": [Vector3(.08,1.10,1.30),Vector3(.99,.19,.99),.48,"ceramic"],
	"fork": [Vector3(.70,1.067,.73),Vector3(.45,.050,.71),.07,"steel"],
	"book": [Vector3(-1.34,1.052,1.32),Vector3(.76,.09,.55),.31,"paper"],
	"notebook": [Vector3(.83,1.055,0),Vector3(.73,.09,.49),.105,"paper"],
	"orange": [Vector3(.90,1.164,1.46),Vector3(.36,.34,.36),.155,"fruit"],
	"chair_book": [Vector3(-3.14,1.20,.59),Vector3(.59,.084,.48),.22,"paper"],
	"bowl": [Vector3(3.14,1.83,-2.39),Vector3(.74,.41,.74),.43,"ceramic"],
	"plant": [Vector3(5.12,1.90,-2.86),Vector3(.65,.53,.63),.83,"plant"],
	"cab_book0": [Vector3(3.57,1.855,-2.78),Vector3(.14,.47,.49),.21,"paper"],
	"cab_book1": [Vector3(3.75,1.835,-2.78),Vector3(.14,.43,.49),.16,"paper"],
	"cab_book2": [Vector3(3.93,1.815,-2.78),Vector3(.14,.39,.49),.12,"paper"],
	"cab_book3": [Vector3(4.11,1.795,-2.78),Vector3(.14,.35,.49),.10,"paper"],
	"cab_stop0": [Vector3(3.31,1.75,-2.69),Vector3(.26,.28,.26),.24,"wood"],
	"cab_stop1": [Vector3(4.66,1.75,-2.69),Vector3(.26,.28,.26),.24,"wood"],
}
const DECOYS := {
	"car":[Vector3(3.40,.32,1.80),Vector3(.94,.61,.65)],
	"blocks":[Vector3(4.63,.23,1.01),Vector3(.88,.34,.72)],
	"block":[Vector3(-3.78,.23,2.18),Vector3(.34,.33,.34)],
	"balloon":[Vector3(5.05,2.47,-.16),Vector3(.85,.98,.77)]
}

var view: SubViewport
var live_layer: Node2D
var hud_layer: Node2D
var live_was_active := true
var world: Node3D
var camera: Camera3D
var cloth: MeshInstance3D
var groups: Dictionary = {}
var visuals: Dictionary = {}
var sprites: Dictionary = {}
var taken: Dictionary = {}
var flights: Dictionary = {}
var shakes: Dictionary = {}
var shadow: GradientTexture2D
var hint_key := ""
var hint_age := 0.0
var hint_next := 0
var bump := 0.0
var pending_tap := Vector2(-1,-1)
var pan := Vector2.ZERO
var start := Vector2.ZERO
var start_pan := Vector2.ZERO
var pointer := -2
var dragged := false
var progress: Label
var caption: Label
var hint_button: Button
var audit_wait := -1.0
var ticks := 0
var smoke := false
var test_order := ["table","chair","cabinet"]
var test_baseline: Dictionary = {}
var test_failed := false

func _ready() -> void:
	_build_world()
	_build_ui()
	for key in TARGETS:
		var source: Texture2D = ART[key]
		var sprite := AtlasTexture.new()
		sprite.atlas=source
		sprite.region=source.get_image().get_used_rect()
		sprites[key]=sprite
	shadow=GradientTexture2D.new()
	shadow.width=96
	shadow.height=96
	shadow.fill=GradientTexture2D.FILL_RADIAL
	shadow.fill_from=Vector2(.5,.5)
	shadow.fill_to=Vector2(1,.5)
	var gradient:=Gradient.new()
	gradient.set_color(0,Color("#56382173"))
	gradient.set_color(1,Color("#56382100"))
	gradient.add_point(.56,Color("#5638213b"))
	shadow.gradient=gradient
	var args:=OS.get_cmdline_user_args()
	smoke="--test-furniture" in args
	for arg in args:
		if arg.begins_with("--order="):
			test_order.assign(arg.trim_prefix("--order=").split(","))
	for key in PROPS:
		test_baseline[key]=groups[key].position.y

func _build_world() -> void:
	view=SubViewport.new()
	view.size=Vector2i(RENDER_SIZE)
	view.own_world_3d=true
	view.transparent_bg=true
	view.render_target_update_mode=SubViewport.UPDATE_ONCE
	view.msaa_3d=Viewport.MSAA_4X
	add_child(view)
	# Transparent SubViewport textures already have premultiplied edges.
	# Blending them as a regular texture darkens the antialiased silhouette.
	live_layer=Node2D.new()
	var blend:=CanvasItemMaterial.new()
	blend.blend_mode=CanvasItemMaterial.BLEND_MODE_PREMULT_ALPHA
	live_layer.material=blend
	live_layer.draw.connect(_draw_live)
	add_child(live_layer)
	hud_layer=Node2D.new()
	hud_layer.draw.connect(_draw_hud)
	add_child(hud_layer)
	world=Node3D.new()
	view.add_child(world)
	var env:=WorldEnvironment.new()
	env.environment=Environment.new()
	env.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color=Color("#ffeddf")
	env.environment.ambient_light_energy=.39
	world.add_child(env)
	_light(Vector3(-5,10,5),.34,Color("#fff3df"),false)
	_light(Vector3(5,7,2),.14,Color("#e9f2ff"),false)
	_light(Vector3(1,8,-5),.14,Color("#ffecda"),false)
	camera=Camera3D.new()
	world.add_child(camera)
	camera.position=Vector3(8.0,14.4,15.6)
	camera.look_at(Vector3(0,1.1,-.06))
	camera.keep_aspect=Camera3D.KEEP_WIDTH
	camera.fov=rad_to_deg(2.0*atan(36.0/92.0))
	camera.current=true

	var table:=_static("table",Vector3(-.11,.89,.82),SELECT[0])
	_add_box(table,Vector3(3.83,.22,2.53))
	for x in [-1.62,1.59]:
		for z in [-.94,.94]:
			_add_box(table,Vector3(.23,.74,.23),Vector3(x,-.43,z))
	var chair:=_static("chair",Vector3(-3.22,.94,.53),SELECT[1])
	_add_box(chair,Vector3(1.22,.16,1.18))
	_add_box(chair,Vector3(1.12,.17,1.02),Vector3(0,.13,.02))
	_add_box(chair,Vector3(1.18,.52,.18),Vector3(0,.94,-.46))
	for x in [-.46,.46]:
		_add_box(chair,Vector3(.16,1.15,.15),Vector3(x,.53,-.46))
		for z in [-.43,.43]:
			_add_box(chair,Vector3(.15,.89,.15),Vector3(x,-.45,z))
	var cabinet:=_static("cabinet",Vector3(3.84,.79,-2.78),SELECT[2])
	_add_box(cabinet,Vector3(3.21,1.43,1.27),Vector3(0,0,.05))
	_add_box(cabinet,Vector3(3.38,.14,1.31),Vector3(0,.76,0))
	for key in DECOYS:
		_add_box(_static(key,DECOYS[key][0],ITEMS),DECOYS[key][1])
	for key in PROPS:
		_add_prop(key)

	var model:=MODEL.instantiate() as Node3D
	world.add_child(model)
	_reparent_meshes(model)
	_floor_block(Vector3(0,-.08,0),Vector3(12.7,.28,9.5))
	_floor_block(Vector3(-.46,.106,1.07),Vector3(6.65,.072,5.18))
	_floor_block(Vector3(-3.49,.65,-2.35),Vector3(3.78,1.13,2.1))
	_floor_block(Vector3(0,2.02,-4.56),Vector3(12.5,4.3,.24))
	_floor_block(Vector3(-6.18,2.02,-2.58),Vector3(.22,4.3,4.0))
	# Limit rolling props to the visible room floor without drawing any walls.
	for x in [-6.25,6.25]:
		_boundary(Vector3(x,.48,0),Vector3(.12,1.0,9.44))
	_boundary(Vector3(0,.48,4.66),Vector3(12.6,1.0,.12))
	cloth=MeshInstance3D.new()
	cloth.set_script(CLOTH_SCRIPT)
	world.add_child(cloth)

func _boundary(center: Vector3,dims: Vector3) -> void:
	var block:=StaticBody3D.new()
	block.collision_layer=32
	world.add_child(block)
	block.position=center
	_add_box(block,dims)

func _register(key: String, body: CollisionObject3D, center: Vector3, layer: int) -> void:
	body.name=key
	body.position=center
	body.collision_layer=layer
	body.set_meta("item",key)
	world.add_child(body)
	var visual:=Node3D.new()
	body.add_child(visual)
	groups[key]=body
	visuals[key]=visual

func _static(key: String,center: Vector3,layer: int) -> StaticBody3D:
	var body:=StaticBody3D.new()
	_register(key,body,center,layer)
	return body

func _add_prop(key: String) -> void:
	var config: Array=PROPS[key]
	var body:=RigidBody3D.new()
	body.mass=config[2]
	body.collision_mask=CLOSED|32
	body.freeze=true
	body.continuous_cd=true
	PROP_DYNAMICS.configure(body,config[3])
	_register(key,body,config[0],ITEMS)
	match key:
		"cup": _add_cylinder(body,.286,.43,Vector3(-.058,-.016,0))
		"plate": _add_cylinder(body,.49,.18)
		"bowl": _add_cylinder(body,.36,.40)
		"plant": _add_cylinder(body,.295,.53)
		"cab_stop0","cab_stop1": _add_cylinder(body,.13,.28)
		"orange": _add_sphere(body,.17)
		"fork":
			_add_box(body,Vector3(.095,.052,.55),Vector3(-.093,0,.23),-.50)
			_add_box(body,Vector3(.29,.052,.225),Vector3(.085,0,-.13),-.50)
		_: _add_box(body,config[1])
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
			node.reparent(visuals[key],true)
			node.visible=key not in TARGETS
			_material_detail(node,key)

func _material_detail(node: MeshInstance3D,key: String) -> void:
	for i in range(node.mesh.get_surface_count()):
		var source := node.mesh.surface_get_material(i) as StandardMaterial3D
		if not source: continue
		var m:=source.duplicate() as StandardMaterial3D
		# The AgX-baked room has pastel highlights; retain that palette for live pieces.
		m.albedo_color=m.albedo_color.lerp(Color("#fff7ed"),.27)
		m.metallic_specular=.28
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
		_redraw()

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
	_label("福尔猫斯",27,Vector2(18,7))
	caption=_label("午后客厅 · 拖动看房间，点按收集",14,Vector2(19,43))
	progress=_label("家具   0/3",17,Vector2.ZERO)
	var restart:=_button("重来",func():get_tree().reload_current_scene())
	hint_button=_button("提示",_hint_target)
	for b in [restart,hint_button]:
		b.custom_minimum_size=Vector2(71,37)
		for mode in ["normal","hover","pressed","disabled"]:
			var style:=StyleBoxFlat.new()
			style.bg_color=Color("#f6e8d2") if mode in ["hover","pressed"] else Color("#fffaf0")
			style.border_color=Color("#d5bca0")
			style.set_corner_radius_all(18)
			style.set_border_width_all(1)
			b.add_theme_stylebox_override(mode,style)
		for state in ["font_color","font_hover_color","font_pressed_color","font_focus_color"]:
			b.add_theme_color_override(state,Color("#654835"))
		b.add_theme_color_override("font_disabled_color",Color("#baa38c"))
		b.size=b.custom_minimum_size
	var fit:=func():
		_clamp_pan()
		restart.position=Vector2(14,size.y-64)
		hint_button.position=Vector2(size.x-85,size.y-64)
		_refresh_caption()
	resized.connect(fit)
	fit.call()

func _refresh_caption() -> void:
	progress.text="家具   %d/%d"%[taken.size(),TARGETS.size()]
	progress.position=Vector2(maxf(0.0,(size.x-progress.get_minimum_size().x)*.5),size.y-FOOTER+6)
	caption.text="家具收齐了！" if taken.size()==TARGETS.size() else "午后客厅 · 拖动看房间，点按收集"
	hint_button.disabled=taken.size()+flights.size()>=TARGETS.size()
	_redraw()

func _field() -> Rect2:
	return Rect2(0,TOP,size.x,maxf(1.0,size.y-TOP-FOOTER))

func _scale() -> float:
	var d:=_field().size
	# Portrait keeps a useful object size and pans the same image horizontally.
	return maxf(d.x/RENDER_SIZE.x,d.y/RENDER_SIZE.y)*1.04

func _origin() -> Vector2:
	var field:=_field()
	return field.position+(field.size-RENDER_SIZE*_scale())*.5+pan

func _clamp_pan() -> void:
	var limit:=(RENDER_SIZE*_scale()-_field().size)*.5
	pan=pan.clamp(-limit,limit)

func _box_center() -> Vector2:
	return Vector2(size.x*.5,size.y-34)

func _redraw() -> void:
	queue_redraw()
	if live_layer:live_layer.queue_redraw()
	if hud_layer:hud_layer.queue_redraw()

func _draw() -> void:
	if not view or not camera:return
	var r:=Rect2(_origin(),RENDER_SIZE*_scale())
	draw_texture_rect(BACKDROP,r,false)
	if shadow:_draw_shadows()
	if not hint_key.is_empty():_draw_hint()
	# The actual furniture shell uses the exact same Blender texture before
	# and during the flight; its 3D body stays intact for contact/ray tests.
	for key in TARGETS:
		if taken.has(key) or flights.has(key) or not sprites.has(key):continue
		var sprite: AtlasTexture=sprites[key]
		var scale:=_scale()
		var zoom:=_hint_zoom(key)
		var center:=r.position+sprite.region.get_center()*scale
		var dims:=sprite.get_size()*scale*zoom
		draw_texture_rect(sprite,Rect2(center-dims*.5,dims),false)
	if shadow:_draw_prop_shadows()

func _hint_zoom(key: String) -> float:
	if key!=hint_key:return 1.0
	var fade:=minf(hint_age/.12,1.0)*(1.0-smoothstep(HINT_SECONDS-.32,HINT_SECONDS,hint_age))
	return 1.0+(.5+.5*sin(hint_age*TAU*1.12))*.07*fade

func _draw_live() -> void:
	live_layer.draw_texture_rect(view.get_texture(),Rect2(_origin(),RENDER_SIZE*_scale()),false)

func _draw_hud() -> void:
	hud_layer.draw_rect(Rect2(0,0,size.x,TOP),Color("#fff7e9"))
	hud_layer.draw_rect(Rect2(0,size.y-FOOTER,size.x,FOOTER),Color("#fff7e9"))
	hud_layer.draw_line(Vector2(0,TOP),Vector2(size.x,TOP),Color("#dec3a8"))
	hud_layer.draw_line(Vector2(0,size.y-FOOTER),Vector2(size.x,size.y-FOOTER),Color("#dec3a8"))
	var box_size:=Vector2(92,64)*(1.0+bump*.10)
	hud_layer.draw_texture_rect(BOX,Rect2(_box_center()-box_size*.5,box_size),false)
	for key in flights:_draw_flight(key)

func _draw_shadows() -> void:
	var f:=_scale()
	var spots:={"table":Vector2(272,118),"chair":Vector2(126,62),"cabinet":Vector2(249,88)}
	for key in TARGETS:
		if taken.has(key) or flights.has(key):continue
		var center: Vector3=groups[key].position
		center.y=.13
		var p:=_origin()+camera.unproject_position(center)*f
		var d: Vector2=spots[key]*f
		draw_texture_rect(shadow,Rect2(p-d*.5,d),false,Color(1,1,1,.65))

func _draw_prop_shadows() -> void:
	var f:=_scale()
	var origin:=_origin()
	for key in PROPS:
		var body:=groups[key] as RigidBody3D
		var config: Array=PROPS[key]
		var center:=body.position
		var height: float=config[1].y*.5
		var opacity:=.38
		if body.freeze:
			center.y-=height
		else:
			var rug:=Rect2(-3.785,-1.52,6.65,5.18)
			center.y=.142 if rug.has_point(Vector2(center.x,center.z)) else .062
			opacity*=lerpf(.35,1.0,1.0-clampf(body.position.y-center.y-height,0.0,1.0))
		var p:=origin+camera.unproject_position(center)*f
		var d:=Vector2(config[1].x*76,config[1].z*44)*f
		draw_texture_rect(shadow,Rect2(p-d*.5,d),false,Color(1,1,1,opacity))

func _draw_flight(key: String) -> void:
	var flight: Dictionary=flights[key]
	var age: float=flight.age
	var source: Vector2=flight.source
	var aperture:=_box_center()+Vector2(0,-9)
	var sprite: AtlasTexture=sprites[key]
	var lift:=source+Vector2(0,-26)
	var p:=source
	var t:=0.0
	var zoom:=1.0
	if age<LIFT:
		t=clampf(age/LIFT,0.0,1.0)
		p=source.lerp(lift,1.0-pow(1.0-t,3.0))
		zoom=lerpf(float(flight.start_zoom),1.12,t)
	else:
		t=clampf((age-LIFT)/(DURATION-LIFT),0.0,1.0)
		p=lift.bezier_interpolate(lift+Vector2((aperture.x-lift.x)*.26,-40),aperture+Vector2((lift.x-aperture.x)*.26,-73),aperture,t*t*(3.0-2.0*t))
		zoom=lerpf(1.12,.12,t*t)
	var d:=sprite.get_size()*float(flight.factor)*zoom
	hud_layer.draw_texture_rect(sprite,Rect2(p-d*.5,d),false,Color(1,1,1,1.0-smoothstep(.83,1.0,t) if age>=LIFT else 1.0))

func _hint_target() -> void:
	hint_key=""
	var origin:=_origin()
	var f:=_scale()
	var selected:=""
	for offset in range(TARGETS.size()):
		var key: String=TARGETS[(hint_next+offset)%TARGETS.size()]
		if taken.has(key) or flights.has(key):continue
		if selected.is_empty():selected=key
		var sprite: AtlasTexture=sprites[key]
		if _field().grow(-minf(13.0,_field().size.y*.45)).has_point(origin+sprite.region.get_center()*f):
			selected=key
			break
	if selected.is_empty():return
	hint_key=selected
	hint_next=(TARGETS.find(hint_key)+1)%TARGETS.size()
	hint_age=0.0
	var wanted:=_origin()+(sprites[hint_key] as AtlasTexture).region.get_center()*f
	if not _field().grow(-minf(44.0,_field().size.y*.45)).has_point(wanted):
		pan+=_field().get_center()-wanted
		_clamp_pan()
	_redraw()

func _draw_hint() -> void:
	var a:=minf(hint_age/.12,1.0)*(1.0-smoothstep(HINT_SECONDS-.32,HINT_SECONDS,hint_age))
	var sprite: AtlasTexture=sprites[hint_key]
	var c:=_origin()+sprite.region.get_center()*_scale()
	var d:=sprite.get_size()*_scale()
	var radius:=clampf(maxf(d.x,d.y)*.86,45.0,245.0)
	var spin:=hint_age*TAU*.42
	var lengths: Array[float]=[1.04,.76,1.0,.83,.92,.73,1.0]
	for i in range(7):
		var angle:=spin+float(i)*TAU/7.0
		var length:=radius*lengths[i]
		var bloom:=clampf(length*.38,13.0,55.0)
		draw_set_transform(c,angle,Vector2.ONE)
		draw_texture_rect(HINT_RAY,Rect2(0,-bloom*.5,length,bloom),false,Color(1,1,1,a*.94))
		draw_set_transform(c,angle+.20,Vector2.ONE)
		draw_texture_rect(HINT_RAY,Rect2(0,-bloom*.25,length*.78,bloom*.5),false,Color(1,1,1,a*.60))
	draw_set_transform(Vector2.ZERO,0,Vector2.ONE)

func _ray(pixel: Vector2,mask: int,cloth_check := false) -> Dictionary:
	var a:=camera.project_ray_origin(pixel)
	var direction:=camera.project_ray_normal(pixel)
	var query:=PhysicsRayQueryParameters3D.create(a,a+direction*55.0,mask)
	var hit:=view.find_world_3d().direct_space_state.intersect_ray(query)
	if cloth_check and not hit.is_empty() and cloth.blocks_ray(a,direction,a.distance_to(hit.position)):
		return {}
	return hit

func _pick_scene(pixel: Vector2) -> void:
	var hit:=_ray(pixel,CLOSED,true)
	if hit.is_empty():return
	var key: String=hit.collider.get_meta("item","")
	if key in TARGETS:
		_take(key)
	elif key in DECOYS or key in PROPS:
		shakes[key]=0.0

func _take(key: String) -> void:
	if flights.has(key) or taken.has(key):return
	var body:=groups[key] as StaticBody3D
	var start_zoom:=_hint_zoom(key)
	if hint_key==key:hint_key=""
	body.collision_layer=0
	body.collision_mask=0
	for child in body.get_children():
		if child is CollisionShape3D:child.set_deferred("disabled",true)
	body.hide()
	var sprite: AtlasTexture=sprites[key]
	flights[key]={"age":0.0,"source":_origin()+sprite.region.get_center()*_scale(),"factor":_scale(),"start_zoom":start_zoom}
	for held in SUPPORTS[key]:
		var prop:=groups[held] as RigidBody3D
		prop.freeze=false
		prop.sleeping=false
	if key=="table":cloth.release_support()
	audit_wait=1.15
	_refresh_caption()

func _process(dt: float) -> void:
	if not hint_key.is_empty():
		hint_age+=dt
		if hint_age>=HINT_SECONDS:hint_key=""
	for key in flights.keys():
		flights[key].age+=dt
		if flights[key].age>=DURATION:
			flights.erase(key)
			taken[key]=true
			bump=1.0
			_refresh_caption()
	if not shakes.is_empty():view.render_target_update_mode=SubViewport.UPDATE_ONCE
	for key in shakes.keys():
		shakes[key]+=dt
		var age: float=shakes[key]
		visuals[key].position.x=sin(age*TAU*13.0)*.085*maxf(0.0,1.0-age/.28)
		if age>=.28:shakes.erase(key)
	bump=move_toward(bump,0.0,dt*3.7)
	_redraw()

func _coverage(key: String) -> Dictionary:
	var body:=groups[key] as StaticBody3D
	var sprite: AtlasTexture=sprites[key]
	var bounds:=sprite.region.grow(8.0)
	var total:=0
	var count:=0
	var blockers: Dictionary={}
	var tap:=Vector2(-1,-1)
	var best:=INF
	for y in range(16):
		for x in range(16):
			var p:=bounds.position+bounds.size*Vector2((x+.5)/16.0,(y+.5)/16.0)
			if _ray(p,body.collision_layer).get("collider")!=body:continue
			total+=1
			var hit:=_ray(p,CLOSED,true)
			if hit.get("collider")==body:
				count+=1
				var distance:=p.distance_squared_to(bounds.get_center())
				if distance<best:
					best=distance
					tap=p
			elif hit.get("collider") is RigidBody3D:
				var key_id: String=hit.collider.get_meta("item","")
				blockers[key_id]=int(blockers.get(key_id,0))+1
	return {"ratio":float(count)/maxi(total,1),"tap":tap,"blockers":blockers}

func _audit_furniture() -> void:
	for key in TARGETS:
		if taken.has(key) or flights.has(key):continue
		var result:=_coverage(key)
		if result.ratio>=EXPOSURE:continue
		for blocked in result.blockers:
			var prop:=groups[blocked] as RigidBody3D
			if prop.freeze:continue
			var away: Vector3=prop.position-groups[key].position
			away.y=0.0
			if away.length_squared()<.005:away=Vector3.RIGHT
			prop.sleeping=false
			prop.apply_central_impulse((away.normalized()*.7+Vector3.UP*.15)*prop.mass)
			audit_wait=.55

func _physics_process(dt: float) -> void:
	ticks+=1
	var active: bool=cloth.advance(dt)
	for key in PROPS:
		var body:=groups[key] as RigidBody3D
		if not body.freeze and not body.sleeping:
			active=true
			PROP_DYNAMICS.apply_air_drag(body,PROPS[key][1],PROPS[key][3])
	if active or live_was_active:view.render_target_update_mode=SubViewport.UPDATE_ONCE
	live_was_active=active
	if pending_tap.x>=0:
		_pick_scene(pending_tap)
		pending_tap=Vector2(-1,-1)
	if audit_wait>=0.0:
		audit_wait-=dt
		if audit_wait<0.0:_audit_furniture()
	if smoke:_test_frame()

func _test_assert(condition: bool, message: String) -> void:
	if not condition:
		push_error(message)
		test_failed=true

func _test_frame() -> void:
	if ticks==25:
		var rotation:=camera.global_transform
		_begin(-1,_field().get_center())
		_move(-1,_field().get_center()+Vector2(86,-28))
		_end(-1,_field().get_center()+Vector2(86,-28),false)
		_test_assert(pending_tap.x<0 and rotation==camera.global_transform,"Drag must pan, never aim the camera or take furniture")
		pan=Vector2.ZERO
		_hint_target()
		_test_assert(hint_key in TARGETS,"Hint should select remaining furniture")
	for i in range(TARGETS.size()):
		var phase:=55+i*135
		var key: String=test_order[i]
		if ticks==phase:
			var state:=_coverage(key)
			_test_assert(state.ratio>=EXPOSURE and state.tap.x>=0,"Target not sufficiently clickable: "+key)
			var p: Vector2=_origin()+state.tap*_scale()
			if not _field().has_point(p):
				pan+=_field().get_center()-p
				_clamp_pan()
				p=_origin()+state.tap*_scale()
			if i%2==0:
				var mouse:=InputEventMouseButton.new()
				mouse.button_index=MOUSE_BUTTON_LEFT
				mouse.position=p
				mouse.pressed=true
				_input(mouse)
				mouse.pressed=false
				_input(mouse)
			else:
				var touch:=InputEventScreenTouch.new()
				touch.position=p
				touch.pressed=true
				_input(touch)
				touch.pressed=false
				_input(touch)
		if ticks==phase+2:
			_test_assert(flights.has(key) and not taken.has(key),"Furniture must only count on entering the basket: "+key)
			for future in test_order.slice(i+1):
				for prop in SUPPORTS[future]:
					_test_assert(groups[prop].freeze,"Removing one support cannot release "+prop)
		if key=="table" and ticks==phase+18:
			var fork_speed: float=-groups.fork.linear_velocity.y
			var paper_speed: float=-groups.notebook.linear_velocity.y
			_test_assert(fork_speed>paper_speed+.17 and paper_speed>1.0,"Fork and notebook should not share identical air speed")
			print("FURNITURE_TEST in_air_fork=",fork_speed," in_air_notebook=",paper_speed)
		if ticks==phase+117:
			_test_assert(taken.has(key),"Flight did not finish: "+key)
			var heights: Dictionary={}
			for prop in SUPPORTS[key]:
				heights[prop]=groups[prop].position.y
				_test_assert(groups[prop].position.y<test_baseline[prop]-.36 and groups[prop].position.y>.07,"Prop did not settle after removing "+key+": "+prop)
			if key=="table":_test_assert(cloth.bounds.end.y<.35,"Towel did not fall")
			for future in test_order.slice(i+1):
				_test_assert(_coverage(future).ratio>=EXPOSURE,"Remaining target is blocked: "+future)
			print("FURNITURE_TEST removed=",key," count=",taken.size()," settled_y=",heights)
	if ticks==465:
		_test_assert(taken.size()==3 and flights.is_empty(),"Expected a completed run")
		print("FURNITURE_TEST complete=",not test_failed," order=",test_order)
		get_tree().quit(1 if test_failed else 0)
