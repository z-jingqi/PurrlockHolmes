extends RefCounted
## Game-scale aerodynamic/contact presets; all objects share world gravity.
## Columns: friction, restitution, angular damping, effective drag coefficient.
const PRESETS := {
	"ceramic": [0.42, 0.065, 0.62, 0.53],
	"steel": [0.31, 0.025, 0.42, 0.23],
	"paper": [0.76, 0.012, 1.65, 1.10],
	"fruit": [0.56, 0.36, 0.44, 0.42],
	"plant": [0.68, 0.035, 0.85, 0.95],
	"wood": [0.58, 0.14, 0.62, 0.56],
}

static func configure(body: RigidBody3D, surface: String) -> void:
	var preset: Array=PRESETS[surface]
	body.linear_damp_mode=RigidBody3D.DAMP_MODE_REPLACE
	body.linear_damp=0.03
	body.angular_damp_mode=RigidBody3D.DAMP_MODE_REPLACE
	body.angular_damp=preset[2]
	var material:=PhysicsMaterial.new()
	material.friction=preset[0]
	material.bounce=preset[1]
	material.rough=surface in ["paper","plant"]
	body.physics_material_override=material

static func apply_air_drag(body: RigidBody3D, bounds: Vector3, surface: String) -> void:
	if body.freeze or body.sleeping:return
	var velocity:=body.linear_velocity
	var speed_squared:=velocity.length_squared()
	if speed_squared<0.01:return
	var facing:=velocity / sqrt(speed_squared)
	var local: Vector3=(body.global_basis.orthonormalized().transposed()*facing).abs()
	var area:=local.x*bounds.y*bounds.z+local.y*bounds.x*bounds.z+local.z*bounds.x*bounds.y
	var coefficient: float=PRESETS[surface][3]
	# F = 1/2 rho Cd A v². Godot divides the force by the body's mass.
	body.apply_central_force(-facing * (0.61 * coefficient * area * speed_squared))
