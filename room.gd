extends Control

const NAMES := ["杯子", "盘子", "叉子", "小碗", "茶匙", "茶壶", "小碟"]
const ROOM := preload("res://assets/room.webp")
const BOX := preload("res://assets/paw-box.svg")
const ATLAS := preload("res://assets/pickups.webp")
const ITEMS := preload("res://assets/pickup_data.gd").ITEMS
const LIFT := 0.14
const DURATION := 0.58
const FOOTER := 111.0
const WRONG_ATLAS := preload("res://assets/wrong.webp")
const WRONG := preload("res://assets/wrong_data.gd").ITEMS
const WRONG_MASK := preload("res://assets/wrong.png")
const HINT_SECONDS := 3.0
const HINT_RAY := preload("res://assets/hint-ray.png")
var mask: Image
var wrong_mask: Image
var shake: Dictionary = {}
var hint_id := 0
var last_hint := 0
var hint_age := 0.0
var hint_button: Button
var scene_size: Vector2
var pan := Vector2.ZERO
var known: Dictionary = {}
var flights: Dictionary = {}
var taken: Dictionary = {}
var bump := 0.0
var active := -2
var down := Vector2.ZERO
var offset_at_down := Vector2.ZERO
var dragged := false
var title: Label
var subtitle: Label
var hint: Label
var hud: Label
var done: Label
var reset: Button

func _ready() -> void:
	mask = preload("res://assets/pick.png").get_image()
	wrong_mask = WRONG_MASK.get_image()
	scene_size = ROOM.get_size()
	title = _label(30, Color("#4a3634"))
	title.text = "福尔猫斯"
	subtitle = _label(12, Color("#806a57"))
	subtitle.text = "PURRLOCK HOLMES  /  案卷 01 · 午后客厅"
	hint = _label(14, Color("#806a57"))
	hint.text = "拖动看房间 · 点按收集"
	hud = _label(19, Color("#4a3634"))
	done = _label(28, Color("#4a3634"))
	reset = Button.new()
	reset.text = "再玩一局"
	reset.add_theme_font_override("font", hud.get_theme_font("font"))
	reset.position = Vector2(22, 136)
	reset.pressed.connect(_reset)
	add_child(reset)
	hint_button = Button.new()
	hint_button.text = "✦  提示"
	hint_button.add_theme_font_override("font", hud.get_theme_font("font"))
	hint_button.custom_minimum_size = Vector2(75,39)
	hint_button.pressed.connect(_hint_target)
	add_child(hint_button)
	resized.connect(_relayout)
	_reset()
	if "--test-demo" in OS.get_cmdline_user_args():
		_test_demo()

func _label(font_size: int, shade: Color) -> Label:
	var label := Label.new()
	var font := SystemFont.new()
	font.font_names = PackedStringArray(["PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", "Arial"])
	label.add_theme_font_override("font", font)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", shade)
	add_child(label)
	return label

func _relayout() -> void:
	_refresh()
	_layout()

func _layout() -> void:
	if hud == null or done == null or hint_button == null:
		return
	_clamp()
	title.position = Vector2(20, 5)
	subtitle.position = Vector2(22, 46)
	_align_footer()
	hint.position = Vector2(maxf(20, size.x - 178), 21)
	hint.visible = size.x >= 350
	done.position = Vector2(22, 87)
	queue_redraw()

func _reset() -> void:
	known.clear()
	flights.clear()
	taken.clear()
	bump = 0.0
	hint_id = 0
	last_hint = 0
	shake.clear()
	pan = Vector2.ZERO
	active = -2
	_refresh()
	_layout()

func _align_footer() -> void:
	var width := hud.get_minimum_size().x
	hud.position = Vector2((size.x-width)/2.0, size.y - FOOTER + 9)
	hint_button.size = hint_button.custom_minimum_size
	hint_button.position = Vector2(size.x-91,size.y-66)

func _refresh() -> void:
	hud.text = "餐具  %d/%d" % [known.size(), NAMES.size()]
	_align_footer()
	done.text = "餐具找齐了！" if known.size() == 7 else ""
	reset.visible = known.size() == 7
	hint_button.disabled = taken.size() >= NAMES.size()
	queue_redraw()

func _factor() -> float:
	return maxf(size.x / scene_size.x, size.y / scene_size.y) * 1.15

func _clamp() -> void:
	if scene_size.x <= 0.0:
		return
	var limit := (scene_size * _factor() - size) * 0.5
	pan = pan.clamp(-limit, limit)

func _image_origin() -> Vector2:
	return (size - scene_size * _factor()) * 0.5 + pan

func _draw() -> void:
	if scene_size.x <= 0.0:
		return
	var f := _factor()
	var origin := _image_origin()
	draw_texture_rect(ROOM, Rect2(origin, scene_size * f), false)
	for id: int in taken:
		var data: Dictionary = ITEMS[str(id)]
		var patch := _rect(data["patch"])
		draw_texture_rect_region(ATLAS, Rect2(origin + _vec(data["origin"]) * f, patch.size * f), patch)
	for id: int in shake:
		var data: Dictionary = WRONG[str(id)]
		var original := origin + _vec(data["origin"]) * f
		var patch := _rect(data["patch"])
		draw_texture_rect_region(WRONG_ATLAS,Rect2(original,patch.size*f),patch)
		var elapsed: float = shake[id]
		var wave := sin(elapsed/.30*TAU*2.5)*5.5*(1.0-elapsed/.30)
		var sprite := _rect(data["sprite"])
		draw_texture_rect_region(WRONG_ATLAS,Rect2(original+Vector2(wave,0),sprite.size*f),sprite)
	if hint_id > 0:
		_draw_hint(origin,f)
	draw_rect(Rect2(0, 0, size.x, 72 if known.size() < 7 else 179), Color("#fff7e9"))
	draw_rect(Rect2(0, size.y - FOOTER, size.x, FOOTER), Color("#fff7e9"))
	draw_line(Vector2(0, 71), Vector2(size.x, 71), Color("#dec3a8"))
	draw_line(Vector2(0, size.y - FOOTER), Vector2(size.x, size.y - FOOTER), Color("#dec3a8"))

	var box_size := Vector2(96, 67) * (1.0 + sin(bump * PI) * .09)
	var dest := _box_center()
	draw_texture_rect(BOX, Rect2(dest - box_size / 2.0, box_size), false)
	for id: int in flights:
		_draw_flight(id)

func _box_center() -> Vector2:
	return Vector2(size.x/2.0, size.y - 43)

func _vec(a: Array) -> Vector2:
	return Vector2(a[0], a[1])

func _rect(a: Array) -> Rect2:
	return Rect2(a[0], a[1], a[2], a[3])

func _draw_flight(id: int) -> void:
	var flight: Dictionary = flights[id]
	var age: float = flight["age"]
	var source: Vector2 = flight["source"]
	var aperture := _box_center() + Vector2(0, -10)
	var sprite := _rect(ITEMS[str(id)]["sprite"])
	var lift := source + Vector2(0, -26)
	var p := source
	var t := 0.0
	var zoom := 1.0
	if age < LIFT:
		t = clampf(age / LIFT, 0.0, 1.0)
		p = source.lerp(lift, 1.0 - pow(1.0 - t, 3.0))
		zoom = lerpf(1.0, 1.12, t)
	else:
		t = clampf((age - LIFT) / (DURATION - LIFT), 0.0, 1.0)
		p = lift.bezier_interpolate(lift + Vector2((aperture.x-lift.x)*.26,-40), aperture + Vector2((lift.x-aperture.x)*.26,-73), aperture, t*t*(3.0-2.0*t))
		zoom = lerpf(1.12, .17, t*t)
	var dims := sprite.size * float(flight["factor"]) * zoom
	var opacity := 1.0 if age < LIFT else 1.0 - smoothstep(.80, 1.0, t)
	draw_texture_rect_region(ATLAS, Rect2(p - dims / 2.0, dims), sprite, Color(1,1,1,opacity))

func _process(delta: float) -> void:
	if flights.is_empty() and bump <= 0.0 and hint_id == 0 and shake.is_empty():
		return
	if hint_id > 0:
		hint_age += delta
		if hint_age >= HINT_SECONDS:
			hint_id = 0
	for id: int in shake.keys():
		shake[id] += delta
		if shake[id] >= .30:
			shake.erase(id)
	bump = maxf(0.0, bump - delta * 5)
	for id: int in flights.keys():
		flights[id]["age"] += delta
		if flights[id]["age"] >= DURATION:
			flights.erase(id)
			known[id] = true
			bump = .9
			_refresh()
	queue_redraw()

func _hint_target() -> void:
	if taken.size() >= NAMES.size():
		return
	var origin := _image_origin()
	var f := _factor()
	var fallback := 0
	hint_id = 0
	for offset in range(1, NAMES.size()+1):
		var id := (last_hint + offset - 1) % NAMES.size() + 1
		if taken.has(id):
			continue
		if fallback == 0:
			fallback = id
		var c := origin + _vec(ITEMS[str(id)]["hint_center"]) * f
		if Rect2(27, 99, maxf(1,size.x-54),maxf(1,size.y-FOOTER-126)).has_point(c):
			hint_id = id
			break
	if hint_id == 0:
		hint_id = fallback if fallback != 0 else hint_id
	if hint_id == 0:
		return
	var center := origin + _vec(ITEMS[str(hint_id)]["hint_center"]) * f
	if not Rect2(20, 93, maxf(1,size.x-40),maxf(1,size.y-FOOTER-115)).has_point(center):
		pan += Vector2(size.x/2.0,(72+size.y-FOOTER)*.5)-center
		_clamp()
	last_hint = hint_id
	hint_age = 0.0
	queue_redraw()

func _draw_hint(origin: Vector2, f: float) -> void:
	var data: Dictionary = ITEMS[str(hint_id)]
	var a := minf(hint_age/.12,1.0) * (1.0 - smoothstep(HINT_SECONDS-.32,HINT_SECONDS,hint_age))
	var patch := _rect(data["patch"])
	draw_texture_rect_region(ATLAS,Rect2(origin+_vec(data["origin"])*f,patch.size*f),patch,Color(1,1,1,a))
	var c := origin + _vec(data["hint_center"])*f
	var sprite := _rect(data["hint"])
	var breath := 1.0 + (.5 + .5*sin(hint_age*TAU*1.12)) * .10 * a
	var dims := sprite.size*f*breath
	# Beam size follows the resting prop, not the breathing curve.
	var base := sprite.size * f
	var radius := clampf(maxf(base.x,base.y)*1.24,31.0,110.0)
	var spin := hint_age*TAU*.42
	for i in range(7):
		var angle := spin+float(i)*TAU/7.0
		var length := radius * ([1.04,.76,1.0,.83,.92,.73,1.0][i] as float)
		draw_set_transform(c,angle,Vector2.ONE)
		var bloom := clampf(length*.38,13.0,38.0)
		draw_texture_rect(HINT_RAY,Rect2(0,-bloom/2.0,length,bloom),false,Color(1,1,1,a*.94))
		draw_set_transform(c,angle+.20,Vector2.ONE)
		draw_texture_rect(HINT_RAY,Rect2(0,-bloom*.25,length*.78,bloom*.5),false,Color(1,1,1,a*.60))
	draw_set_transform(Vector2.ZERO,0,Vector2.ONE)
	# The item stays in front of the beam origin.
	draw_texture_rect_region(ATLAS,Rect2(c-dims/2,dims),sprite,Color(1,1,1,a))

func _wrong_at(p: Vector2i) -> void:
	if not Rect2i(Vector2i.ZERO, wrong_mask.get_size()).has_point(p):
		return
	var id := roundi(wrong_mask.get_pixelv(p).r * 255.0/8.0)
	if WRONG.has(str(id)):
		shake[id] = 0.0
		queue_redraw()

func _pick(p: Vector2i) -> int:
	if not Rect2i(Vector2i.ZERO, mask.get_size()).has_point(p):
		return 0
	var c := mask.get_pixelv(p)
	var v := roundi(c.r * 255)
	var id := roundi(v / 32.0)
	return id if id >= 1 and id <= 7 and absi(v - id * 32) <= 2 and c.g < .015 and c.b < .015 else 0

func _collect(id: int, _p: Vector2i) -> void:
	if id <= 0 or taken.has(id):
		return
	taken[id] = true
	if hint_id == id:
		hint_id = 0
	hint_button.disabled = taken.size() >= NAMES.size()
	var f := _factor()
	flights[id] = {"age": 0.0, "source": _image_origin() + _vec(ITEMS[str(id)]["center"]) * f, "factor": f}
	queue_redraw()

func _press(id: int, p: Vector2) -> void:
	if active != -2 or p.y < (179 if known.size() == 7 else 72) or p.y >= size.y - FOOTER:
		return
	active = id
	down = p
	offset_at_down = pan
	dragged = false

func _move(id: int, p: Vector2) -> void:
	if active != id:
		return
	if p.distance_to(down) >= 7:
		dragged = true
	if dragged:
		pan = offset_at_down + p - down
		_clamp()
		queue_redraw()

func _release(id: int, p: Vector2, canceled: bool) -> void:
	if active != id:
		return
	if not canceled:
		_move(id, p)
		if not dragged and p.y >= 72 and p.y < size.y - FOOTER:
			var q := Vector2i(((p - _image_origin()) / _factor()).floor())
			var id_found := _pick(q)
			if id_found > 0:
				_collect(id_found, q)
			else:
				_wrong_at(q)
	active = -2

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_WINDOW_FOCUS_OUT:
		active = -2

func _input(e: InputEvent) -> void:
	if e is InputEventScreenTouch:
		if e.pressed and not e.canceled:
			_press(e.index, e.position)
		else:
			_release(e.index, e.position, e.canceled)
	elif e is InputEventScreenDrag:
		_move(e.index, e.position)
	elif e is InputEventMouseButton and e.button_index == MOUSE_BUTTON_LEFT and e.device != InputEvent.DEVICE_ID_EMULATION:
		if e.pressed:
			_press(-1, e.position)
		else:
			_release(-1, e.position, e.canceled)
	elif e is InputEventMouseMotion and e.device != InputEvent.DEVICE_ID_EMULATION:
		_move(-1, e.position)

func _mouse_at(p: Vector2, pressed: bool) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = MOUSE_BUTTON_LEFT
	event.position = p
	event.pressed = pressed
	_input(event)

func _test_demo() -> void:
	set_anchors_preset(Control.PRESET_TOP_LEFT)
	size = Vector2(960, 720)
	_layout()
	var points := [Vector2i(679,549), Vector2i(683,630), Vector2i(786,614),
		Vector2i(1098,471), Vector2i(420,660), Vector2i(784,826), Vector2i(414,493)]
	var all_hit := true
	_hint_target()
	var hinted := hint_id
	_process(.18)
	var hint_ok := hinted > 0 and hint_age > 0.0 and known.is_empty()
	_hint_target()
	hint_ok = hint_ok and hint_id > 0 and hint_id != hinted
	_reset()
	var decoy := _image_origin() + Vector2(996.5,805.5) * _factor()
	_mouse_at(decoy,true)
	_mouse_at(decoy,false)
	var wrong_ok := shake.has(7) and known.is_empty() and flights.is_empty()
	_process(.31)
	wrong_ok = wrong_ok and shake.is_empty()
	var miss := _image_origin() + Vector2(750.5, 300.5) * _factor()
	_mouse_at(miss, true)
	_mouse_at(miss, false)
	all_hit = known.is_empty() and shake.is_empty()
	for i in range(points.size()):
		var p := _image_origin() + (Vector2(points[i]) + Vector2(0.5, 0.5)) * _factor()
		_mouse_at(p, true)
		_mouse_at(p, false)
		_mouse_at(p, true)
		_mouse_at(p, false)
		all_hit = all_hit and not known.has(i + 1) and flights.size() == 1
		_process(DURATION + .01)
		all_hit = all_hit and known.has(i + 1) and known.size() == i + 1
	var won := all_hit and known.size() == 7 and reset.visible
	_reset()
	var touch := InputEventScreenTouch.new()
	touch.index = 0
	touch.position = _image_origin() + Vector2(679.5,549.5) * _factor()
	touch.pressed = true
	_input(touch)
	touch.pressed = false
	touch.canceled = true
	_input(touch)
	var cancel_ok := known.is_empty() and active == -2 and flights.is_empty()
	var p := Vector2(400,220)
	var previous := _image_origin()
	_mouse_at(p, true)
	var motion := InputEventMouseMotion.new()
	motion.position = p + Vector2(30,22)
	_input(motion)
	_mouse_at(motion.position, false)
	var pan_ok := (_image_origin() - previous).is_equal_approx(Vector2(30,22)) and known.is_empty()
	var ok := won and cancel_ok and pan_ok and hint_ok and wrong_ok
	print("DEMO_TEST mouse_win=%s cancel_preserves_targets=%s flat_pan=%s hint=%s decoy_shake=%s" % [won, cancel_ok, pan_ok, hint_ok, wrong_ok])
	get_tree().quit(0 if ok else 1)
