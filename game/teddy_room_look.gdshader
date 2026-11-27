shader_type spatial;
render_mode unshaded, fog_disabled, cull_disabled;

uniform sampler2D camera_look : source_color, filter_nearest, repeat_disable;

void fragment() {
	// The light is captured under the approved fixed camera, but all coverage and
	// depth come from the actual teddy meshes in the local 3D viewport.
	ALBEDO = texture(camera_look, SCREEN_UV).rgb;
}
