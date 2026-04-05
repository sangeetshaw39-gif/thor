#version 330
uniform sampler2D tex;
uniform float target_width;

in vec2 v_tex;
out vec4 f_color;

void main() {
    float offset = 1.0 / target_width; // 1 pixel width
    
    // To make it massive without a huge kernel, we scale the offset
    // Since it's downsampled already, a radius of 3.0 gives massive bloom
    float r = offset * 2.5;

    vec4 color = vec4(0.0);
    // 9-tap Gaussian blur across X axis
    color += texture(tex, v_tex + vec2(-4.0 * r, 0.0)) * 0.016216;
    color += texture(tex, v_tex + vec2(-3.0 * r, 0.0)) * 0.054054;
    color += texture(tex, v_tex + vec2(-2.0 * r, 0.0)) * 0.1216216;
    color += texture(tex, v_tex + vec2(-1.0 * r, 0.0)) * 0.1945946;
    color += texture(tex, v_tex) * 0.227027;
    color += texture(tex, v_tex + vec2(1.0 * r, 0.0)) * 0.1945946;
    color += texture(tex, v_tex + vec2(2.0 * r, 0.0)) * 0.1216216;
    color += texture(tex, v_tex + vec2(3.0 * r, 0.0)) * 0.054054;
    color += texture(tex, v_tex + vec2(4.0 * r, 0.0)) * 0.016216;

    f_color = color;
}
