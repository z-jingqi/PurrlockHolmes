extends Node2D
## Real fitted 3D meshes in a small fixed-view tile. The viewport sleeps between taps.
const LAYOUT := preload("res://game/cat_layout.gd")
const MODEL := preload("res://assets/cat.glb")
const LOOK := preload("res://assets/cat-look.webp")
const BLINK := preload("res://assets/cat-blink.webp")
const SHADER := preload("res://game/cat_look.gdshader")
const RESOLVE := preload("res://game/teddy_resolve.gdshader")
const DURATION := .76
# Neutral silhouette, inset so the nearby sofa and cushions remain inert.
var hit := PackedVector2Array([Vector2(455,262),Vector2(468,256),Vector2(477,260),
	Vector2(483,267),Vector2(496,270),Vector2(509,282),Vector2(518,294),
	Vector2(518,308),Vector2(510,318),Vector2(492,319),Vector2(472,323),
	Vector2(461,330),Vector2(444,331),Vector2(439,325),Vector2(423,328),
	Vector2(408,326),Vector2(408,316),Vector2(416,306),Vector2(407,296),
	Vector2(406,283),Vector2(410,269),Vector2(413,251),Vector2(421,249),
	Vector2(432,258),Vector2(442,260)])
const FACE := Vector2(444,294)

var view: SubViewport
var model: Node3D
var head: Node3D
var surface: ShaderMaterial
var home: Vector3
var active := false

func _ready() -> void:
	show_behind_parent=true
	view=SubViewport.new()
	view.size=Vector2i(LAYOUT.TILE.size)*2
	view.own_world_3d=true
	view.transparent_bg=true
	view.msaa_3d=Viewport.MSAA_2X
	view.render_target_update_mode=SubViewport.UPDATE_ONCE
	add_child(view)
	var camera:=Camera3D.new()
	view.add_child(camera)
	camera.position=LAYOUT.CAMERA
	camera.look_at(LAYOUT.LOOK)
	camera.set_orthogonal(LAYOUT.SIZE,.05,24.0)
	camera.current=true
	model=MODEL.instantiate()
	view.add_child(model)
	head=model.find_child("CatHead",true,false) as Node3D
	assert(head!=null)
	home=head.position
	surface=ShaderMaterial.new()
	surface.shader=SHADER
	surface.set_shader_parameter("awake",LOOK)
	surface.set_shader_parameter("asleep",BLINK)
	for node in model.find_children("*","MeshInstance3D",true,false):
		var mesh:=node as MeshInstance3D
		mesh.material_override=surface
		mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	texture_filter=CanvasItem.TEXTURE_FILTER_LINEAR
	var resolve:=ShaderMaterial.new()
	resolve.shader=RESOLVE
	material=resolve

func set_reaction(age: float) -> void:
	if age<0.0:
		if not active:return
		active=false
		head.position=home
		head.rotation=Vector3.ZERO
		surface.set_shader_parameter("blink",0.0)
		view.render_target_update_mode=SubViewport.UPDATE_ONCE
		return
	if not active:
		active=true
		view.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	var lift:=smoothstep(.015,.225,age)*(1.0-smoothstep(.32,DURATION,age))
	head.position=home+Vector3(0,.022*lift,0)
	head.rotation=Vector3(-.051*lift,.027*lift,.018*lift)
	var blink:=smoothstep(.022,.084,age)*(1.0-smoothstep(.108,.187,age))
	surface.set_shader_parameter("blink",blink)

func _draw() -> void:
	if view:draw_texture_rect(view.get_texture(),LAYOUT.TILE,false)

func contains(pixel: Vector2) -> bool:
	return Geometry2D.is_point_in_polygon(pixel,hit)
