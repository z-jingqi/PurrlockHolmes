extends Control
## Case 01. Only tableware is collectible. Every view shares the fixed Blender camera.
const TEDDY := preload("res://game/room_teddy.gd")
const CAT := preload("res://game/room_cat.gd")
const BACKDROP := preload("res://assets/room.webp")
const FORK_DETAIL := preload("res://assets/fork-detail.png")
const FORK_SHADOW := preload("res://assets/fork-shadow.png")
const ATLAS := preload("res://assets/tea-sprites.webp")
const ART := preload("res://game/tea_frames.gd")
const FRAMES := ART.FRAMES
const CLIPS := ART.CLIPS
const MARKERS := ART.MARKERS
const BOX := preload("res://assets/paw-box.svg")
const HINT_RAY := preload("res://assets/hint-ray.png")
const UI_FONT := preload("res://game/ui-zh.otf")
const TARGETS := ["saucer","cup","plate","fork","bowl","teapot"]
const DRAW_ORDER := ["bowl","teapot","saucer","cup","plate","fork"]
const PLANTS := ["rubber_plant","lance_plant"]
const BALLOONS := ["balloon_0","balloon_1","balloon_2"]
const COTTON_WARM := Color("#9e8062bb")
const COTTON_LIGHT := Color("#d1b797ce")
const CORD_DRAPE := [Vector2(-11.0,5.5),Vector2(-9.4,6.8),Vector2(-7.0,9.2)]
const CUP_SETTLE := .27
const CATEGORY := "餐具"
const RENDER_SIZE := Vector2(1200,896)
const TOP := 76.0
const FOOTER := 94.0
const LIFT := .14
const DURATION := .58
const HINT_SECONDS := 3.0
var backdrop_layer: Node2D
var teddy: Node2D
var cat: Node2D
var hud_layer: Node2D
var cup_age := -1.0
var elapsed := 0.0
var balloon_tapped := -1
var decor: Dictionary={}
var sprites: Dictionary={}
var atlas_image: Image
var shadow: GradientTexture2D
var taken: Dictionary={}
var flights: Dictionary={}
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
	backdrop_layer=Node2D.new()
	backdrop_layer.show_behind_parent=true
	backdrop_layer.draw.connect(_draw_backdrop)
	add_child(backdrop_layer)
	teddy=TEDDY.new()
	add_child(teddy)
	cat=CAT.new()
	add_child(cat)
	hud_layer=Node2D.new()
	hud_layer.draw.connect(_draw_hud)
	add_child(hud_layer)
	atlas_image=ATLAS.get_image()
	for key in FRAMES:
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
	if backdrop_layer:backdrop_layer.queue_redraw()
	if teddy:
		teddy.position=_origin()
		teddy.scale=Vector2.ONE*_scale()
	if cat:
		cat.position=_origin()
		cat.scale=Vector2.ONE*_scale()
	if hud_layer:hud_layer.queue_redraw()

func _start_pixel(key: String) -> Vector2:
	var pixel: Vector2=FRAMES[key][1]
	if key=="cup" and cup_age>=0:
		var t:=minf(cup_age/CUP_SETTLE,1.0)
		# A very short authored settle: this level no longer requires a 3D world.
		var fall:=minf(1.0,pow(t/.69,2.0)) if t<.69 else 1.0-.12*sin((t-.69)/.31*PI)
		pixel+=MARKERS["cup_drop"]*fall
	return pixel

func _prop_center(key: String) -> Vector2:
	var sprite: AtlasTexture=sprites[key]
	return _origin()+(_start_pixel(key)+sprite.get_size()*.5)*_scale()

func _zoom(key: String) -> float:
	if hint_key!=key:return 1.0
	var a:=minf(hint_age/.12,1.0)*(1.0-smoothstep(HINT_SECONDS-.32,HINT_SECONDS,hint_age))
	return 1.0+(.5+.5*sin(hint_age*TAU*1.12))*.09*a

func _draw_backdrop() -> void:
	backdrop_layer.draw_texture_rect(BACKDROP,Rect2(_origin(),RENDER_SIZE*_scale()),false)

func _draw() -> void:
	if sprites.is_empty():return
	var f:=_scale()
	_draw_decor(f)
	_draw_balloon_bunch(f)
	for key in DRAW_ORDER:
		if not sprites.has(key) or taken.has(key) or flights.has(key):continue
		if key==hint_key:_draw_hint(key)
		var sprite: AtlasTexture=sprites[key]
		var center:=_prop_center(key)
		var d:=sprite.get_size()*f*_zoom(key)
		if key=="fork":
			var shade_size:=d+Vector2(12,12)*f*_zoom(key)
			draw_texture_rect(FORK_SHADOW,Rect2(center-shade_size*.5,shade_size),false)
		elif shadow:
			var width:=d.x*.86
			var skid:=Vector2(width,maxf(5.0,width*.31))
			var bottom:=center+Vector2(0,d.y*.29)
			draw_texture_rect(shadow,Rect2(bottom-skid*.5,skid),false,Color(1,1,1,.54))
		draw_texture_rect(FORK_DETAIL if key=="fork" else sprite,Rect2(center-d*.5,d),false)

func _clip_frame(key: String) -> String:
	var age: float=decor.get(key,-1.0)
	var frames: Array=CLIPS[key]
	return frames[clampi(roundi(maxf(0,age)*20),0,frames.size()-1)]

func _draw_decor(f: float) -> void:
	for key: String in PLANTS:
		var frame:=_clip_frame(key)
		if frame.is_empty():continue
		var spr: AtlasTexture=sprites[frame]
		var p: Vector2=FRAMES[frame][1]
		draw_texture_rect(spr,Rect2(_origin()+p*f,spr.get_size()*f),false)

func _balloon_pose(index: int) -> Vector3:
	var phase:=float(index)*1.69
	var clock:=elapsed*(.99+index*.103)
	var a:=clock+phase
	var drift:=Vector2(2.6*sin(a)+.55*sin(a*1.71),2.0*cos(a*.87+phase))
	var twist:=.029*sin(a*.69)
	if decor.has("balloons"):
		var lag:=0.057*absf(index-balloon_tapped)
		var t:=float(decor["balloons"])-lag
		if t>0:
			var drive:=sin(minf(t/.20,1.0)*PI*.5)*exp(-t*1.45)*(1.0-smoothstep(1.45,1.85,t))
			var direction:=1.0 if balloon_tapped==0 else -1.0
			var power:=1.0 if index==balloon_tapped else .63
			drift.x+=direction*11.5*power*sin(t*(6.6+index*.66)+.60+phase*.24)*drive
			drift.y-=6.5*power*cos(t*(4.4+index*.54)+phase*.42)*drive
			twist+=direction*.073*sin(t*6.25+.60+phase*.21)*drive*power
	return Vector3(drift.x,drift.y,twist)

func _balloon_geometry(index: int,pose: Vector3) -> Array[Vector2]:
	var key: String=BALLOONS[index]
	var center: Vector2=FRAMES[key][1]+FRAMES[key][0].size*.5
	var tip: Vector2=MARKERS[key]
	var displaced:=center+Vector2(pose.x,pose.y)
	return [displaced,displaced+(tip-center).rotated(pose.z)]

func _cotton_curve(index: int,tip: Vector2,age: float) -> PackedVector2Array:
	var root: Vector2=MARKERS["tether"]
	var delta:=tip-root
	var phase:=1.54*index
	var lagged:=0.0
	if decor.has("balloons"):
		var t:=maxf(0.0,float(decor["balloons"])-.12-index*.033)
		lagged=sin(t*8.3)*exp(-t*1.9)*5.0
	var drape: Vector2=CORD_DRAPE[index]
	var points:=PackedVector2Array()
	for j in range(35):
		var t:=float(j)/34.0
		var slack:=sin(PI*t)
		# Gravity bows the warm cotton cord. A weaker wave follows the moving
		# envelope, not the endpoints; both knots therefore stay fully attached.
		var shape:=drape*slack
		shape.x+=slack*(7.7*sin(TAU*t+.46*index)+(2.0+lagged)*sin(age*1.13+phase-t*2.5))
		shape.y+=slack*lagged*.31
		points.append(root+delta*t+shape)
	points[0]=root
	points[points.size()-1]=tip
	return points

func _draw_cotton(points: PackedVector2Array,f: float) -> void:
	# The narrow, soft edge is the fiber silhouette, not a shiny outline. The
	# subtle variation in the core reads as cotton at room scale, without stripes.
	draw_polyline(points,COTTON_WARM,maxf(.82,f*1.13),true)
	var fibers:=PackedColorArray()
	for j in range(points.size()):
		var tint:=.67+.09*sin(float(j)*2.21)
		fibers.append(COTTON_LIGHT.lerp(Color("#f0d8b88c"),tint))
	draw_polyline_colors(points,fibers,maxf(.49,f*.69),true)

func _draw_balloon_bunch(f: float) -> void:
	var origin:=_origin()
	var drawn: Array=[]
	for i in range(BALLOONS.size()):
		var pose:=_balloon_pose(i)
		var geom:=_balloon_geometry(i,pose)
		var points:=_cotton_curve(i,geom[1],elapsed)
		for j in range(points.size()):points[j]=origin+points[j]*f
		_draw_cotton(points,f)
		drawn.append([geom[0],pose.z])
	# Back balloon first; the front shapes naturally cover any cord behind them.
	for i in [1,0,2]:
		var spr: AtlasTexture=sprites[BALLOONS[i]]
		var d:=spr.get_size()*f
		draw_set_transform(origin+drawn[i][0]*f,drawn[i][1],Vector2.ONE)
		draw_texture_rect(spr,Rect2(-d*.5,d),false)
	draw_set_transform(Vector2.ZERO,0,Vector2.ONE)

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
	hud_layer.draw_texture_rect(FORK_DETAIL if key=="fork" else sprite,Rect2(p-d*.5,d),false,Color(1,1,1,1.0-smoothstep(.83,1.0,t) if age>=LIFT else 1.0))

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

func _art_alpha(key: String,rel: Vector2,threshold := .22) -> bool:
	var bounds: Rect2=FRAMES[key][0]
	return Rect2(Vector2.ZERO,bounds.size).has_point(rel) and atlas_image.get_pixelv(Vector2i(bounds.position+rel)).a>threshold

func _alpha_hit(key: String,pixel: Vector2) -> bool:
	var bounds: Rect2=FRAMES[key][0]
	var rel:=(pixel-_start_pixel(key)-bounds.size*.5)/_zoom(key)+bounds.size*.5
	return _art_alpha(key,rel)

func _decor_at(pixel: Vector2) -> String:
	if cat.contains(pixel):return "cat"
	for key in PLANTS:
		var frame:=_clip_frame(key)
		var top: Vector2=FRAMES[frame][1]
		var d: Vector2=FRAMES[frame][0].size
		# Do not turn the pot/soil into another button. Only the green silhouette reacts.
		var rel:=pixel-top
		if rel.y<d.y*.77 and _art_alpha(frame,rel,.26):return key
	for i in [2,0,1]:
		var pose:=_balloon_pose(i)
		var key: String=BALLOONS[i]
		var center:=_balloon_geometry(i,pose)[0]
		var rel: Vector2=(pixel-center).rotated(-pose.z)+FRAMES[key][0].size*.5
		if _art_alpha(key,rel,.26):return key
	return ""

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
	var prop:=_decor_at(pixel)
	if prop.is_empty():return
	if prop in BALLOONS:
		if decor.has("balloons"):return
		balloon_tapped=BALLOONS.find(prop)
		decor["balloons"]=0.0
	elif not decor.has(prop):
		decor[prop]=0.0

func _take(key: String) -> void:
	if taken.has(key) or flights.has(key):return
	flights[key]={"age":0.0,"source":_prop_center(key),"factor":_scale(),"zoom":_zoom(key)}
	if hint_key==key:hint_key=""
	if key=="saucer" and not taken.has("cup") and not flights.has("cup"):
		cup_age=0.0
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
	elapsed+=dt
	if cup_age>=0 and cup_age<CUP_SETTLE:cup_age=minf(cup_age+dt,CUP_SETTLE)
	for key in decor.keys():
		decor[key]+=dt
		var duration:=.80
		if key=="cat":duration=CAT.DURATION
		if key=="balloons":duration=2.03
		if decor[key]>=duration:decor.erase(key)
	cat.set_reaction(decor.get("cat",-1.0))
	bump=move_toward(bump,0.0,dt*3.7)
	_redraw()

func _physics_process(_dt: float) -> void:
	ticks+=1
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
		_test(teddy.visible_mesh_count()>=18,"Teddy is missing its 3D geometry")
		_test(teddy.model_pin().distance_to(MARKERS["tether"])<.15,"The balloon tether drifted from the 3D bear")
		for key in TARGETS:
			_test(_tap_point(key).ratio>=.25,"Insufficient visible area: "+key)
		_hint_target()
		_test(hint_key in TARGETS and taken.is_empty(),"Hint must not collect a target")
		var fixed: Vector2=FRAMES["plate"][1]
		pan+=Vector2(90,90)
		_clamp_pan()
		pan=Vector2.ZERO
		_test(_start_pixel("plate")==fixed,"Pan changed scene coordinates")
		for fixed_prop in [Vector2(767,644),Vector2(909,587),Vector2(219,519),
				Vector2(323,573),Vector2(605,453),Vector2(851,650)]:
			_pick_scene(fixed_prop)
		_test(decor.is_empty() and flights.is_empty(),"Static props must not react or collect")
		_test(cat.model.find_children("*","MeshInstance3D",true,false).size()==23,"Cat mesh incomplete")
		_test(not cat.contains(Vector2(399,269)) and not cat.contains(Vector2(523,323)),"Cat hitbox covers the sofa")
		_pick_scene(CAT.FACE)
		_test(decor.has("cat"),"Cat did not react")
		for plant in PLANTS:
			var frame:=_clip_frame(plant)
			var tile: Rect2=FRAMES[frame][0]
			var start_at: Vector2=FRAMES[frame][1]
			var point:=Vector2(-1,-1)
			for y in range(5,int(tile.size.y*.70),2):
				for x in range(4,int(tile.size.x)-4,2):
					var sample:=start_at+Vector2(x,y)
					if _decor_at(sample)==plant:
						point=sample
						break
				if point.x>=0:break
			_pick_scene(point)
			_test(decor.has(plant),"Leaf interaction missing: "+plant)
		for i in range(BALLOONS.size()):
			var pt:=_balloon_geometry(i,_balloon_pose(i))[0]
			_test(_decor_at(pt)==BALLOONS[i],"A balloon is not independently clickable")
		_pick_scene(_balloon_geometry(1,_balloon_pose(1))[0])
		_test(decor.has("balloons") and taken.is_empty(),"Balloon response changed objective")
	if ticks==18:
		_test(_clip_frame("rubber_plant")!=CLIPS["rubber_plant"][0] and cat.active and cat.head.position.y>cat.home.y,"Missing leaf or cat animation")
		var end:=_balloon_geometry(1,_balloon_pose(1))[1]
		var cord:=_cotton_curve(1,end,elapsed)
		_test(cord[0].is_equal_approx(MARKERS["tether"]) and cord[-1].is_equal_approx(end),"Cotton cord did not maintain both tie points")
		_test(cord[17].distance_to((cord[0]+cord[-1])*.5)>6.0,"Balloon cord lost its softly bowed silhouette")
		_test(_decor_at(cord[17]).is_empty(),"Cotton cord must not be an interaction target")
		_test(taken.is_empty() and flights.is_empty(),"Decorative actions affected objective")
	if ticks==64:
		_test(not cat.active and cat.head.position==cat.home and cat.head.rotation==Vector3.ZERO,"Cat did not return to idle")
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
				if taken.has("cup"):_test(cup_age<0,"A collected cup must not reappear")
				else:_test(cup_age>=CUP_SETTLE and _start_pixel("cup").y>FRAMES["cup"][1].y+3,"Cup did not settle after its saucer was collected")
			print("TEA_TEST ",key," count=",taken.size()," category=",CATEGORY)
	if ticks==417:
		_test(taken.size()==TARGETS.size() and win.visible,"Missing end-of-level state")
		print("TEA_TEST complete=",not test_fail)
		get_tree().quit(1 if test_fail else 0)
