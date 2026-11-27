extends Node2D
## A true 3D prop. Cache only its fixed-camera draw, not a sprite of the teddy.
const LAYOUT := preload("res://game/teddy_layout.gd")
const MODEL := preload("res://assets/teddy.glb")
const CAMERA_LOOK := preload("res://assets/teddy-look.png")
const SHADER := preload("res://game/teddy_room_look.gdshader")
const RESOLVE := preload("res://game/teddy_resolve.gdshader")
const ROOM_SIZE := Vector2(1200,896)
const NEAR := .10

var camera: Camera3D
var model: Node3D
var view: SubViewport

func _ready() -> void:
	show_behind_parent=true
	view=SubViewport.new()
	view.size=Vector2i(LAYOUT.TILE.size)*2
	view.own_world_3d=true
	view.transparent_bg=true
	view.msaa_3d=Viewport.MSAA_4X
	view.render_target_update_mode=SubViewport.UPDATE_ONCE
	add_child(view)
	camera=Camera3D.new()
	camera.keep_aspect=Camera3D.KEEP_HEIGHT
	view.add_child(camera)
	camera.position=LAYOUT.CAMERA
	camera.look_at(LAYOUT.TARGET)
	var full_width:=NEAR*LAYOUT.SENSOR_WIDTH/LAYOUT.LENS
	var center: Vector2=LAYOUT.TILE.get_center()-ROOM_SIZE*.5
	var center_of_frustum:=Vector2(center.x,-center.y)*full_width/ROOM_SIZE.x
	camera.set_frustum(full_width*LAYOUT.TILE.size.y/ROOM_SIZE.x,center_of_frustum,NEAR,64.0)
	camera.current=true
	model=MODEL.instantiate()
	view.add_child(model)
	model.position=LAYOUT.ORIGIN
	var shading:=ShaderMaterial.new()
	shading.shader=SHADER
	shading.set_shader_parameter("camera_look",CAMERA_LOOK)
	for node in model.find_children("*","MeshInstance3D",true,false):
		var mesh:=node as MeshInstance3D
		mesh.material_override=shading
		mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	texture_filter=CanvasItem.TEXTURE_FILTER_LINEAR
	var renderer_blend:=ShaderMaterial.new()
	renderer_blend.shader=RESOLVE
	material=renderer_blend

func _draw() -> void:
	if view:draw_texture_rect(view.get_texture(),LAYOUT.TILE,false)

func visible_mesh_count() -> int:
	return model.find_children("*","MeshInstance3D",true,false).size()

func model_pin() -> Vector2:
	return LAYOUT.TILE.position+camera.unproject_position(model.to_global(LAYOUT.ANCHOR))*.5
