#version 330
uniform sampler2D tex;
uniform float target_height;

in vec2 v_tex;
out vec4 f_color;

void main() {
    float offset = 1.0 / target_height;
    
    // Same massive radius scaling
    float r = offset * 2.5;

    vec4 color = vec4(0.0);
    // 9-tap Gaussian blur across Y axis
    color += texture(tex, v_tex + vec2(0.0, -4.0 * r)) * 0.016216;
    color += texture(tex, v_tex + vec2(0.0, -3.0 * r)) * 0.054054;
    color += texture(tex, v_tex + vec2(0.0, -2.0 * r)) * 0.1216216;
    color += texture(tex, v_tex + vec2(0.0, -1.0 * r)) * 0.1945946;
    color += texture(tex, v_tex) * 0.227027;
    color += texture(tex, v_tex + vec2(0.0, 1.0 * r)) * 0.1945946;
    color += texture(tex, v_tex + vec2(0.0, 2.0 * r)) * 0.1216216;
    color += texture(tex, v_tex + vec2(0.0, 3.0 * r)) * 0.054054;
    color += texture(tex, v_tex + vec2(0.0, 4.0 * r)) * 0.016216;

    f_color = color;
}
