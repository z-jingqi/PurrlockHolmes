shader_type canvas_item;
render_mode blend_premul_alpha;

void fragment() {
	// Resolve the 2× model coverage first, then filter on the same pixel
	// grid as the original room so portrait pans do not change the outline.
	vec2 tex_size = 1.0 / TEXTURE_PIXEL_SIZE;
	vec2 grid = UV * (tex_size * 0.5) - vec2(0.5);
	vec2 f = fract(grid);
	vec2 base_uv = (2.0 * floor(grid) + vec2(1.0)) * TEXTURE_PIXEL_SIZE;
	vec2 step_uv = 2.0 * TEXTURE_PIXEL_SIZE;
	vec4 a = texture(TEXTURE, base_uv);
	vec4 b = texture(TEXTURE, base_uv + vec2(step_uv.x, 0.0));
	vec4 c = texture(TEXTURE, base_uv + vec2(0.0, step_uv.y));
	vec4 d = texture(TEXTURE, base_uv + step_uv);
	COLOR = mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}
