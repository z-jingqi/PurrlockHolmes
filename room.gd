extends Control

const NAMES := ["杯子", "盘子", "叉子", "小碗", "茶匙", "茶壶", "小碟"]
const ROOM := preload("res://assets/room.webp")
var mask: Image
var scene_size: Vector2
var pan := Vector2.ZERO
var known: Dictionary = {}
var pins: Dictionary = {}
var active := -2
var down := Vector2.ZERO
var offset_at_down := Vector2.ZERO
var dragged := false
var title: Label
var subtitle: Label
var hint: Label
var hud: Label
var list: Label
var done: Label
var reset: Button

func _ready() -> void:
	mask = preload("res://assets/pick.png").get_image()
	scene_size = ROOM.get_size()
	title = _label(30, Color("#4a3634"))
	title.text = "福尔猫斯"
	subtitle = _label(12, Color("#806a57"))
	subtitle.text = "PURRLOCK HOLMES  /  案卷 01 · 午后客厅"
	hint = _label(14, Color("#806a57"))
	hint.text = "拖动看房间 · 点按收集"
	hud = _label(19, Color("#4a3634"))
	list = _label(16, Color("#4a3634"))
	done = _label(28, Color("#4a3634"))
	reset = Button.new()
	reset.text = "再玩一局"
	reset.add_theme_font_override("font", hud.get_theme_font("font"))
	reset.position = Vector2(22, 136)
	reset.pressed.connect(_reset)
	add_child(reset)
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
	if hud == null or list == null or done == null:
		return
	_clamp()
	title.position = Vector2(20, 5)
	subtitle.position = Vector2(22, 46)
	hud.position = Vector2(20, size.y - 70)
	hint.position = Vector2(maxf(20, size.x - 178), 21)
	hint.visible = size.x >= 350
	list.position = Vector2(20, size.y - 42)
	done.position = Vector2(22, 87)
	queue_redraw()

func _reset() -> void:
	known.clear()
	pins.clear()
	pan = Vector2.ZERO
	active = -2
	_refresh()
	_layout()

func _refresh() -> void:
	hud.text = "本关线索 · 餐具    %s / 7" % known.size()
	var labels := PackedStringArray()
	for i in range(7):
		labels.append(("✓ " if known.has(i + 1) else "· ") + NAMES[i])
	list.text = "  ".join(labels) if size.x >= 390 else "  ".join(labels.slice(0, 4)) + "\n" + "  ".join(labels.slice(4))
	done.text = "餐具找齐了！" if known.size() == 7 else ""
	reset.visible = known.size() == 7
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
	for id: int in pins:
		var pos: Vector2 = origin + Vector2(pins[id]) * f
		draw_circle(pos, 10, Color("#6f9779"), true, -1, true)
		draw_polyline(PackedVector2Array([pos + Vector2(-4, 0), pos + Vector2(-1, 4), pos + Vector2(5, -4)]), Color.WHITE, 2, true)
	draw_rect(Rect2(0, 0, size.x, 72 if known.size() < 7 else 179), Color("#fff7e9"))
	draw_rect(Rect2(0, size.y - 79, size.x, 79), Color("#fff7e9"))
	draw_line(Vector2(0, 71), Vector2(size.x, 71), Color("#dec3a8"))
	draw_line(Vector2(0, size.y - 79), Vector2(size.x, size.y - 79), Color("#dec3a8"))

func _pick(p: Vector2i) -> int:
	if not Rect2i(Vector2i.ZERO, mask.get_size()).has_point(p):
		return 0
	var c := mask.get_pixelv(p)
	var v := roundi(c.r * 255)
	var id := roundi(v / 32.0)
	return id if id >= 1 and id <= 7 and absi(v - id * 32) <= 2 and c.g < .015 and c.b < .015 else 0

func _collect(id: int, p: Vector2i) -> void:
	if id > 0 and not known.has(id):
		known[id] = true
		pins[id] = p
		_refresh()

func _press(id: int, p: Vector2) -> void:
	if active != -2 or p.y < (179 if known.size() == 7 else 72) or p.y >= size.y - 79:
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
		if not dragged and p.y >= 72 and p.y < size.y - 79:
			var q := Vector2i(((p - _image_origin()) / _factor()).floor())
			_collect(_pick(q), q)
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
	var miss := _image_origin() + Vector2(750.5, 300.5) * _factor()
	_mouse_at(miss, true)
	_mouse_at(miss, false)
	all_hit = known.is_empty()
	for i in range(points.size()):
		var p := _image_origin() + (Vector2(points[i]) + Vector2(0.5, 0.5)) * _factor()
		_mouse_at(p, true)
		_mouse_at(p, false)
		_mouse_at(p, true)
		_mouse_at(p, false)
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
	var cancel_ok := known.is_empty() and active == -2
	var p := Vector2(400,220)
	var previous := _image_origin()
	_mouse_at(p, true)
	var motion := InputEventMouseMotion.new()
	motion.position = p + Vector2(30,22)
	_input(motion)
	_mouse_at(motion.position, false)
	var pan_ok := (_image_origin() - previous).is_equal_approx(Vector2(30,22)) and known.is_empty()
	var ok := won and cancel_ok and pan_ok
	print("DEMO_TEST mouse_win=%s cancel_preserves_targets=%s flat_pan=%s" % [won, cancel_ok, pan_ok])
	get_tree().quit(0 if ok else 1)
