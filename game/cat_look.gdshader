shader_type spatial;
render_mode unshaded, fog_disabled, cull_disabled;

// Appearance is attached to the mesh UVs, so the face and fabric move with the head.
uniform sampler2D awake : source_color, filter_linear, repeat_disable;
uniform sampler2D asleep : source_color, filter_linear, repeat_disable;
uniform float blink : hint_range(0.0, 1.0) = 0.0;

void fragment() {
	ALBEDO = mix(texture(awake, UV).rgb, texture(asleep, UV).rgb, blink);
}
