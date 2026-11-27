extends Control
## Case 01. Only tableware is collectible. Every view shares the fixed Blender camera.
const MODEL := preload("res://assets/room.glb")
const BACKDROP := preload("res://assets/room.webp")
const ATLAS := preload("res://assets/tea-sprites.webp")
const FRAMES := preload("res://game/tea_frames.gd").FRAMES
const PROP_DYNAMICS := preload("res://game/prop_dynamics.gd")
const BOX := preload("res://assets/paw-box.svg")
const HINT_RAY := preload("res://assets/hint-ray.png")
const UI_FONT := preload("res://game/ui-zh.otf")
const TARGETS := ["saucer","cup","plate","fork","bowl","teapot"]
const DRAW_ORDER := ["bowl","teapot","saucer","cup","plate","fork"]
const ART_DECOYS := ["rubber_plant","lance_plant","felt_slippers"]
const FOLIAGE := ["rubber_plant","lance_plant"]
# Times and screen motion are authored feedback, not simulated rigid-body forces.
const FEEDBACK := {
	"car":[.29,11.0,.079], "blocks":[.25,13.0,.068], "block":[.25,13.0,.068],
	"balloon":[1.30,1.30,.076], "rubber_plant":[.84,2.8,6.6],
	"lance_plant":[.84,3.25,6.0], "felt_slippers":[.37,8.0,5.2]
}
const BALLOON_TETHER := Vector3(-.397,-1.836,.03)
const CATEGORY := "餐具"
const RENDER_SIZE := Vector2(1200,896)
const TOP := 76.0
const FOOTER := 94.0
const LIFT := .14
const DURATION := .58
const HINT_SECONDS := 3.0
const WORLD := 1
const ITEMS := 2
const DECOYS := {
	"car":[Vector3(3.40,.32,1.80),Vector3(.94,.61,.65)],
	"blocks":[Vector3(4.63,.23,1.01),Vector3(.88,.34,.72)],
	"block":[Vector3(-3.78,.23,2.18),Vector3(.34,.33,.34)],
	"balloon":[Vector3(5.05,2.47,-.16),Vector3(.85,.98,.77)]
}

var view: SubViewport
var live_layer: Node2D
var hud_layer: Node2D
var world: Node3D
var camera: Camera3D
var cup: RigidBody3D
var cup_home := Vector3(-.92,1.08,.35)
var cup_reference := Vector2.ZERO
var saucer_support: StaticBody3D
var groups: Dictionary={}
var visuals: Dictionary={}
var sprites: Dictionary={}
var atlas_image: Image
var shadow: GradientTexture2D
var taken: Dictionary={}
var flights: Dictionary={}
var shakes: Dictionary={}
var hint_key:=""
var hint_age:=0.0
var hint_next:=0
var bump:=0.0
var pending_tap:=Vector2(-1,-1)
var pan:=Vector2.ZERO
var start:=Vector2.ZERO
var start_pan:=Vector2.ZERO
var pointer:=-2
var dragged:=false
var progress: Label
var hint_button: Button
var win: PanelContainer
var smoke:=false
var test_fail:=false
var test_order: Array[String]=[]
var ticks:=0

func _ready() -> void:
	_build_world()
	atlas_image=ATLAS.get_image()
	for key in TARGETS + ART_DECOYS:
		var sprite:=AtlasTexture.new()
		sprite.atlas=ATLAS
		sprite.region=FRAMES[key][0]
		sprite.filter_clip=true
		sprites[key]=sprite
	shadow=GradientTexture2D.new()
	shadow.width=80
	shadow.height=80
	shadow.fill=GradientTexture2D.FILL_RADIAL
	shadow.fill_from=Vector2(.5,.5)
	shadow.fill_to=Vector2(1,.5)
	var gradient:=Gradient.new()
	gradient.set_color(0,Color("#503c2479"))
	gradient.set_color(1,Color("#503c2400"))
	gradient.add_point(.44,Color("#503c2432"))
	shadow.gradient=gradient
	_build_ui()
	var args:=OS.get_cmdline_user_args()
	smoke="--test-level" in args
	test_order.assign(TARGETS)
	if "--cup-first" in args:
		test_order[0]="cup"
		test_order[1]="saucer"

func _build_world() -> void:
	view=SubViewport.new()
	view.size=Vector2i(RENDER_SIZE)
	view.own_world_3d=true
	view.transparent_bg=true
	view.render_target_update_mode=SubViewport.UPDATE_ONCE
	view.msaa_3d=Viewport.MSAA_4X
	add_child(view)
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
	env.environment.ambient_light_energy=.37
	world.add_child(env)
	_light(Vector3(-5,10,5),.36,Color("#fff3df"),false)
	_light(Vector3(5,7,2),.16,Color("#e9f2ff"),false)
	_light(Vector3(1,8,-5),.15,Color("#ffecda"),false)
	camera=Camera3D.new()
	world.add_child(camera)
	camera.position=Vector3(8.0,14.4,15.6)
	camera.look_at(Vector3(0,1.1,-.06))
	camera.keep_aspect=Camera3D.KEEP_WIDTH
	camera.fov=rad_to_deg(2.0*atan(36.0/92.0))
	camera.current=true
	for key in DECOYS:
		_add_box(_static(key,DECOYS[key][0],ITEMS),DECOYS[key][1])
	var model:=MODEL.instantiate() as Node3D
	world.add_child(model)
	_reparent_meshes(model)
	_floor_block(Vector3(-.11,.89,.82),Vector3(3.83,.22,2.53))
	saucer_support=StaticBody3D.new()
	saucer_support.collision_layer=WORLD
	world.add_child(saucer_support)
	saucer_support.position=Vector3(-.88,1.04,.39)
	_add_cylinder(saucer_support,.30,.078)
	cup=RigidBody3D.new()
	cup.mass=.31
	cup.freeze=true
	cup.continuous_cd=true
	cup.collision_layer=ITEMS
	cup.collision_mask=WORLD
	PROP_DYNAMICS.configure(cup,"ceramic")
	world.add_child(cup)
	cup.position=cup_home
	_add_cylinder(cup,.20,.415,Vector3(0,.208,0))
	cup_reference=camera.unproject_position(cup_home)
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
			if DisplayServer.get_name()=="headless":return
			for i in range(node.mesh.get_surface_count()):
				var original := node.mesh.surface_get_material(i) as StandardMaterial3D
				if not original:continue
				var mat:=original.duplicate() as StandardMaterial3D
				mat.albedo_color=mat.albedo_color.lerp(Color("#fff7ed"),.26)
				# Preserve the material-specific finish from Blender (latex, rubber, enamel…).
				# A small warm lift still matches the baked afternoon lighting.
				mat.roughness=original.roughness
				node.set_surface_override_material(i,mat)

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


func _button_skin(button: Button) -> void:
	for mode in ["normal","hover","pressed","disabled"]:
		var style:=StyleBoxFlat.new()
		style.bg_color=Color("#f6e8d2") if mode in ["hover","pressed"] else Color("#fffaf0")
		style.border_color=Color("#d5bca0")
		style.set_corner_radius_all(18)
		style.set_border_width_all(1)
		button.add_theme_stylebox_override(mode,style)
	for state in ["font_color","font_hover_color","font_pressed_color","font_focus_color"]:
		button.add_theme_color_override(state,Color("#654835"))
	button.add_theme_color_override("font_disabled_color",Color("#baa38c"))

func _build_ui() -> void:
	_label("福尔猫斯",28,Vector2(18,7))
	_label("案卷 01  ·  茶点过后",14,Vector2(19,45))
	progress=_label("餐具   0/6",17,Vector2.ZERO)
	var restart:=_button("重来",func():get_tree().reload_current_scene())
	hint_button=_button("提示",_hint_target)
	for button in [restart,hint_button]:
		_button_skin(button)
		button.custom_minimum_size=Vector2(72,38)
		button.size=button.custom_minimum_size
	win=PanelContainer.new()
	var panel:=StyleBoxFlat.new()
	panel.bg_color=Color("#fffaef")
	panel.border_color=Color("#dac0a1")
	panel.set_corner_radius_all(22)
	panel.set_border_width_all(1)
	panel.shadow_color=Color("#55362735")
	panel.shadow_size=12
	for side in [SIDE_LEFT,SIDE_RIGHT,SIDE_TOP,SIDE_BOTTOM]:panel.set_content_margin(side,18)
	win.add_theme_stylebox_override("panel",panel)
	add_child(win)
	win.mouse_filter=Control.MOUSE_FILTER_STOP
	var stack:=VBoxContainer.new()
	stack.add_theme_constant_override("separation",10)
	win.add_child(stack)
	for copy in [["茶点收好啦",23],["六件餐具都找齐了",14]]:
		var l:=Label.new()
		l.text=copy[0]
		l.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
		l.add_theme_font_override("font",UI_FONT)
		l.add_theme_font_size_override("font_size",copy[1])
		l.add_theme_color_override("font_color",Color("#654835"))
		stack.add_child(l)
	var again:=Button.new()
	again.text="再玩一局"
	again.add_theme_font_override("font",UI_FONT)
	again.custom_minimum_size=Vector2(156,37)
	again.pressed.connect(func():get_tree().reload_current_scene())
	_button_skin(again)
	stack.add_child(again)
	win.hide()
	var fit:=func():
		_clamp_pan()
		restart.position=Vector2(14,size.y-64)
		hint_button.position=Vector2(size.x-86,size.y-64)
		_refresh_progress()
	resized.connect(fit)
	fit.call()

func _refresh_progress() -> void:
	progress.text="%s   %d/%d"%[CATEGORY,taken.size(),TARGETS.size()]
	progress.position=Vector2(maxf(0.0,(size.x-progress.get_minimum_size().x)*.5),size.y-FOOTER+6)
	hint_button.disabled=taken.size()+flights.size()>=TARGETS.size()
	if taken.size()==TARGETS.size():
		win.size=win.get_combined_minimum_size()
		win.position=_field().get_center()-win.size*.5
		win.show()
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

func _static(key: String,center: Vector3,layer: int) -> StaticBody3D:
	var body:=StaticBody3D.new()
	body.collision_layer=layer
	body.position=center
	body.set_meta("item",key)
	world.add_child(body)
	var model:=Node3D.new()
	body.add_child(model)
	groups[key]=body
	visuals[key]=model
	return body

func _start_pixel(key: String) -> Vector2:
	var pixel: Vector2=FRAMES[key][1]
	if key=="cup":pixel+=camera.unproject_position(cup.position)-cup_reference
	return pixel

func _prop_center(key: String) -> Vector2:
	var sprite: AtlasTexture=sprites[key]
	return _origin()+(_start_pixel(key)+sprite.get_size()*.5)*_scale()

func _zoom(key: String) -> float:
	if hint_key!=key:return 1.0
	var a:=minf(hint_age/.12,1.0)*(1.0-smoothstep(HINT_SECONDS-.32,HINT_SECONDS,hint_age))
	return 1.0+(.5+.5*sin(hint_age*TAU*1.12))*.09*a

func _draw() -> void:
	if not view or not camera:return
	var f:=_scale()
	draw_texture_rect(BACKDROP,Rect2(_origin(),RENDER_SIZE*f),false)
	for key in ART_DECOYS:
		if sprites.has(key):_draw_art_decoy(key,f)
	for key in DRAW_ORDER:
		if not sprites.has(key) or taken.has(key) or flights.has(key):continue
		if key==hint_key:_draw_hint(key)
		var sprite: AtlasTexture=sprites[key]
		var center:=_prop_center(key)
		var d:=sprite.get_size()*f*_zoom(key)
		if shadow:
			var width:=d.x*.86
			var skid:=Vector2(width,maxf(5.0,width*.31))
			var bottom:=center+Vector2(0,d.y*.29)
			draw_texture_rect(shadow,Rect2(bottom-skid*.5,skid),false,Color(1,1,1,.54))
		draw_texture_rect(sprite,Rect2(center-d*.5,d),false)

func _wave(key: String,phase := 0.0) -> float:
	if not shakes.has(key):return 0.0
	var age: float=shakes[key]
	var stats: Array=FEEDBACK[key]
	var t:=clampf(age/float(stats[0]),0.0,1.0)
	return sin(age*TAU*float(stats[1])+phase)*smoothstep(0.0,.13,t)*pow(1.0-t,1.45)*float(stats[2])

func _plant_offset(key: String,v: float) -> float:
	# Taper to zero at the soil. The strips at different heights follow a slight phase lag.
	var flex:=pow(maxf(0.0,1.0-v/.73),1.37)
	return (_wave(key)+.32*_wave(key,(1.0-v)*2.8))*flex

func _draw_art_decoy(key: String,f: float) -> void:
	var sprite: AtlasTexture=sprites[key]
	var d:=sprite.get_size()
	var origin:=_origin()+_start_pixel(key)*f
	if key=="felt_slippers":
		if shadow:
			draw_texture_rect(shadow,Rect2(origin+Vector2(4,d.y*.51)*f,Vector2(d.x-8,d.y*.56)*f),false,Color(1,1,1,.34))
		draw_texture_rect(sprite,Rect2(origin+Vector2(_wave(key)*f,0),d*f),false)
		return
	if not shakes.has(key):
		draw_texture_rect(sprite,Rect2(origin,d*f),false)
		return
	var tex_size:=ATLAS.get_size()
	var r: Rect2=sprite.region
	# Warp the baked curving leaves vertically in a continuous strip mesh to keep
	# their Blender shading. The ceramic pot is on the separate static backdrop.
	const ROWS := 12
	for j in range(ROWS):
		var a:=float(j)/ROWS
		var b:=float(j+1)/ROWS
		var va:=Vector2(_plant_offset(key,a),d.y*a)
		var vb:=Vector2(_plant_offset(key,b),d.y*b)
		var horizontal:=Vector2(d.x,0)
		var left_a:=r.position+Vector2(0,d.y*a)
		var left_b:=r.position+Vector2(0,d.y*b)
		draw_primitive(
			PackedVector2Array([origin+va*f,origin+(va+horizontal)*f,origin+(vb+horizontal)*f,origin+vb*f]),
			PackedColorArray([Color.WHITE]),
			PackedVector2Array([left_a/tex_size,(left_a+horizontal)/tex_size,(left_b+horizontal)/tex_size,left_b/tex_size]),ATLAS)

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
		zoom=lerpf(float(flight.zoom),1.12,t)
	else:
		t=clampf((age-LIFT)/(DURATION-LIFT),0.0,1.0)
		p=lift.bezier_interpolate(lift+Vector2((aperture.x-lift.x)*.26,-40),aperture+Vector2((lift.x-aperture.x)*.26,-73),aperture,t*t*(3.0-2.0*t))
		zoom=lerpf(1.12,.12,t*t)
	var d:=sprite.get_size()*float(flight.factor)*zoom
	hud_layer.draw_texture_rect(sprite,Rect2(p-d*.5,d),false,Color(1,1,1,1.0-smoothstep(.83,1.0,t) if age>=LIFT else 1.0))

func _hint_target() -> void:
	hint_key=""
	for offset in range(TARGETS.size()):
		var i:=(hint_next+offset)%TARGETS.size()
		var key: String=TARGETS[i]
		if taken.has(key) or flights.has(key):continue
		hint_key=key
		hint_next=(i+1)%TARGETS.size()
		break
	if hint_key.is_empty():return
	hint_age=0.0
	var wanted:=_prop_center(hint_key)
	if not _field().grow(-minf(37.0,_field().size.y*.39)).has_point(wanted):
		pan+=_field().get_center()-wanted
		_clamp_pan()
	_redraw()

func _draw_hint(key: String) -> void:
	var a:=minf(hint_age/.12,1.0)*(1.0-smoothstep(HINT_SECONDS-.32,HINT_SECONDS,hint_age))
	var c:=_prop_center(key)
	var dim: Vector2=sprites[key].get_size()*_scale()
	var radius:=clampf(maxf(dim.x,dim.y)*1.25,30.0,124.0)
	var spin:=hint_age*TAU*.42
	var lengths: Array[float]=[1.04,.76,1.0,.83,.92,.73,1.0]
	for i in range(7):
		var angle:=spin+float(i)*TAU/7.0
		var length:=radius*lengths[i]
		var bloom:=clampf(length*.38,13.0,41.0)
		draw_set_transform(c,angle,Vector2.ONE)
		draw_texture_rect(HINT_RAY,Rect2(0,-bloom*.5,length,bloom),false,Color(1,1,1,a*.94))
		draw_set_transform(c,angle+.20,Vector2.ONE)
		draw_texture_rect(HINT_RAY,Rect2(0,-bloom*.25,length*.78,bloom*.5),false,Color(1,1,1,a*.60))
	draw_set_transform(Vector2.ZERO,0,Vector2.ONE)

func _alpha_hit(key: String,pixel: Vector2) -> bool:
	var bounds: Rect2=FRAMES[key][0]
	var scale:=_zoom(key)
	var rel:=(pixel-_start_pixel(key)-bounds.size*.5)/scale+bounds.size*.5
	if key=="felt_slippers":
		rel.x-=_wave(key)
	elif key in FOLIAGE:
		rel.x-=_plant_offset(key,clampf(rel.y/bounds.size.y,0.0,1.0))
	if not Rect2(Vector2.ZERO,bounds.size).has_point(rel):return false
	return atlas_image.get_pixelv(Vector2i(bounds.position+rel)).a>.22

func _item_at(pixel: Vector2,tolerance := true) -> String:
	# Match the actual alpha silhouette. Topmost object wins, e.g. cup over saucer.
	for i in range(DRAW_ORDER.size()-1,-1,-1):
		var key: String=DRAW_ORDER[i]
		if not taken.has(key) and not flights.has(key) and _alpha_hit(key,pixel):return key
	if tolerance:
		for offset: Vector2 in [Vector2(3,0),Vector2(-3,0),Vector2(0,3),Vector2(0,-3)]:
			var key:=_item_at(pixel+offset,false)
			if not key.is_empty():return key
	return ""

func _pick_scene(pixel: Vector2) -> void:
	if win.visible:return
	var key:=_item_at(pixel)
	if not key.is_empty():
		_take(key)
		return
	for prop: String in ART_DECOYS:
		if _alpha_hit(prop,pixel):
			shakes[prop]=0.0
			return
	var origin:=camera.project_ray_origin(pixel)
	var ray:=PhysicsRayQueryParameters3D.create(origin,origin+camera.project_ray_normal(pixel)*55.0,ITEMS)
	var hit:=view.find_world_3d().direct_space_state.intersect_ray(ray)
	if not hit.is_empty():
		var decoy: String=hit.collider.get_meta("item","")
		if decoy in DECOYS:shakes[decoy]=0.0

func _take(key: String) -> void:
	if taken.has(key) or flights.has(key):return
	flights[key]={"age":0.0,"source":_prop_center(key),"factor":_scale(),"zoom":_zoom(key)}
	if hint_key==key:hint_key=""
	if key=="cup":
		cup.freeze=true
		cup.collision_layer=0
		cup.collision_mask=0
	if key=="saucer":
		saucer_support.collision_layer=0
		if not taken.has("cup") and not flights.has("cup"):
			cup.freeze=false
			cup.sleeping=false
	_refresh_progress()

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
			_refresh_progress()
	for key in shakes.keys():
		shakes[key]+=dt
		var finished: bool=shakes[key]>=FEEDBACK[key][0]
		if visuals.has(key):
			view.render_target_update_mode=SubViewport.UPDATE_ONCE
			var model: Node3D=visuals[key]
			if key=="balloon":
				model.rotation=Vector3(_wave(key,1.8)*.36,0,_wave(key))
				# Small damped arc with the string's basket contact kept in place.
				model.position=BALLOON_TETHER-model.basis*BALLOON_TETHER
			else:
				model.position.x=_wave(key)
		if finished:shakes.erase(key)
	bump=move_toward(bump,0.0,dt*3.7)
	_redraw()

func _physics_process(_dt: float) -> void:
	ticks+=1
	if not cup.freeze and not cup.sleeping:
		PROP_DYNAMICS.apply_air_drag(cup,Vector3(.55,.42,.52),"ceramic")
	if pending_tap.x>=0:
		_pick_scene(pending_tap)
		pending_tap=Vector2(-1,-1)
	if smoke:_test_frame()

func _test(condition: bool,message: String) -> void:
	if not condition:
		push_error(message)
		test_fail=true

func _tap_point(key: String) -> Dictionary:
	var d: Vector2=FRAMES[key][0].size
	var corner:=_start_pixel(key)
	var center:=corner+d*.5
	var whole:=0
	var visible:=0
	var nearest:=INF
	var point:=Vector2(-1,-1)
	for iy in range(1,int(d.y),2):
		for ix in range(1,int(d.x),2):
			var test_pixel:=corner+Vector2(ix,iy)
			if not _alpha_hit(key,test_pixel):continue
			whole+=1
			if _item_at(test_pixel,false)!=key:continue
			visible+=1
			var distance:=test_pixel.distance_squared_to(center)
			if distance<nearest:
				nearest=distance
				point=test_pixel
	return {"ratio":float(visible)/maxi(whole,1),"point":point}

func _test_frame() -> void:
	if ticks==10:
		for key in TARGETS:
			_test(_tap_point(key).ratio>=.25,"Insufficient visible area: "+key)
		_hint_target()
		_test(hint_key in TARGETS and taken.is_empty(),"Hint must not collect a target")
		var pose:=camera.global_transform
		pan+=Vector2(90,90)
		_clamp_pan()
		pan=Vector2.ZERO
		_test(pose==camera.global_transform,"Pan changed camera transform")
		var car_pixel:=camera.unproject_position(DECOYS.car[0])
		_pick_scene(car_pixel)
		_test(shakes.has("car") and flights.is_empty(),"Decoy should shake but never advance progress")
		for prop: String in ART_DECOYS:
			var pixel: Vector2=FRAMES[prop][1]+FRAMES[prop][0].size*.5
			var hit:=false
			for j in range(-12,13,2):
				for i in range(-12,13,2):
					var sample:=pixel+Vector2(i,j)
					if not _alpha_hit(prop,sample):continue
					_pick_scene(sample)
					hit=true
					break
				if hit:break
			_test(hit and shakes.has(prop),"Art decoy isn't interactable: "+prop)
		_pick_scene(camera.unproject_position(DECOYS.balloon[0]))
		_test(shakes.has("balloon") and taken.is_empty(),"Balloon interaction collected an object")
	if ticks==18:
		_test(absf(_plant_offset("rubber_plant",.15))>.1 and is_zero_approx(_plant_offset("rubber_plant",1.0)),"Foliage should move at the leaves and stay at the soil")
		var model: Node3D=visuals.balloon
		_test(absf(model.rotation.z)>.001 and (model.transform*BALLOON_TETHER).distance_to(BALLOON_TETHER)<.0001,"Balloon should sway around a fixed tether")
		_test(taken.is_empty() and flights.is_empty(),"Decorative actions must not affect the objective")
	for i in range(TARGETS.size()):
		var phase:=24+i*63
		var key: String=test_order[i]
		if ticks==phase:
			var candidate:=_tap_point(key)
			_test(candidate.ratio>=.25,"Item became unclickable: "+key)
			var p: Vector2=_origin()+candidate.point*_scale()
			pan+=_field().get_center()-p
			_clamp_pan()
			p=_origin()+candidate.point*_scale()
			if i%2==0:
				var ev:=InputEventMouseButton.new()
				ev.button_index=MOUSE_BUTTON_LEFT
				ev.position=p;ev.pressed=true;_input(ev)
				ev.pressed=false;_input(ev)
			else:
				var ev:=InputEventScreenTouch.new()
				ev.position=p;ev.pressed=true;_input(ev)
				ev.pressed=false;_input(ev)
		if ticks==phase+2:
			_test(flights.has(key) and not taken.has(key),"Must count after the flight: "+key)
		if ticks==phase+57:
			_test(taken.has(key) and progress.text.begins_with(CATEGORY),"Category changed or count failed: "+key)
			if key=="saucer":
				if taken.has("cup"):_test(cup.freeze,"An already collected cup must stay out of the simulation")
				else:_test(cup.position.y<cup_home.y-.035,"Cup did not settle after its saucer was collected")
			print("TEA_TEST ",key," count=",taken.size()," category=",CATEGORY)
	if ticks==417:
		_test(taken.size()==TARGETS.size() and win.visible,"Missing end-of-level state")
		print("TEA_TEST complete=",not test_fail)
		get_tree().quit(1 if test_fail else 0)
