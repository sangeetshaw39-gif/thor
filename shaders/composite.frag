#version 330
in vec2 v_tex;
out vec4 out_color;

uniform sampler2D tex_bg;
uniform sampler2D tex_mask;
uniform sampler2D tex_vfx_bg;
uniform sampler2D tex_vfx_fg;
uniform sampler2D tex_bloom_bg;
uniform sampler2D tex_bloom_fg;

uniform float u_storm_intensity;

// ACES tone mapping curve for Hollywood filmic highlights
vec3 ACESFilm(vec3 x) {
    float a = 2.51;
    float b = 0.03;
    float c = 2.43;
    float d = 0.59;
    float e = 0.14;
    return clamp((x*(a*x+b))/(x*(c*x+d)+e), 0.0, 1.0);
}

void main() {
    // MediaPipe mask edge thresholding
    vec2 u_tex = v_tex; // Removed shake offset as requested
    float raw_mask = texture(tex_mask, u_tex).r; 
    float mask_val = smoothstep(0.4, 0.6, raw_mask);
    float inverted_mask = 1.0 - mask_val;
    
    // --- Lens Optic: Chromatic Aberration ---
    // CA spikes massively depending on EMF storm intensity
    vec2 ndc = u_tex * 2.0 - 1.0;
    vec2 ca_offset = ndc * (0.003 + (u_storm_intensity * 0.006)); 
    float r_cam = texture(tex_bg, u_tex - ca_offset).r;
    float g_cam = texture(tex_bg, u_tex).g;
    float b_cam = texture(tex_bg, u_tex + ca_offset).b;
    vec3 base_cam = vec3(r_cam, g_cam, b_cam);
    
    // --- Lens Optic: Cinematic Teal & Orange Grade (MCU Style) ---
    float cam_luma = dot(base_cam, vec3(0.299, 0.587, 0.114));
    vec3 teal_shadows = vec3(0.2, 0.5, 0.7);
    vec3 orange_hilights = vec3(1.0, 0.7, 0.4);
    vec3 grade = mix(teal_shadows, orange_hilights, smoothstep(0.1, 0.7, cam_luma));
    // Apply 50% strength of the cinematic grade to raw footage
    base_cam = mix(base_cam, base_cam * grade * 1.5, 0.5);

    vec4 sharp_bg_lightning = texture(tex_vfx_bg, u_tex);
    vec4 sharp_fg_lightning = texture(tex_vfx_fg, u_tex);
    
    vec4 bg_bloom = texture(tex_bloom_bg, u_tex);
    vec4 fg_bloom = texture(tex_bloom_fg, u_tex);
    
    vec3 background_layer = base_cam;
    vec3 foreground_layer = base_cam;
    vec3 bloom_tint = vec3(0.1, 0.4, 1.0); 
    
    // --- Layer 0: Background Environment Optics ---
    if (u_storm_intensity > 0.0) {
        // Crush the room into a pitch-black thunderstorm
        vec3 dark_cyan = vec3(0.01, 0.03, 0.08); 
        background_layer = mix(background_layer, background_layer * dark_cyan, min(u_storm_intensity * 2.0, 1.0)); 
        
        // Searing bright white/blue flash
        vec3 flash_color = vec3(0.6, 0.9, 1.0) * max(0.0, (u_storm_intensity - 0.5) * 3.0); 
        background_layer += flash_color;
        
        // --- Optic: Ambient Shadow Matching ---
        float luma = dot(foreground_layer, vec3(0.299, 0.587, 0.114));
        vec3 ambient_shadow = mix(dark_cyan * 3.0, vec3(1.0), smoothstep(0.0, 0.4, luma));
        foreground_layer = mix(foreground_layer, foreground_layer * ambient_shadow, min(u_storm_intensity, 1.0));
    }
    
    background_layer += sharp_bg_lightning.rgb * sharp_bg_lightning.a;
    background_layer += bg_bloom.rgb * bloom_tint * 2.0;

    // --- Hard Mask Stacking ---
    vec3 comp = mix(background_layer, foreground_layer, mask_val);
    
    // --- Optic: True Lens Light Wrap ---
    if (u_storm_intensity > 0.0) {
        float wrap_boundary = smoothstep(0.4, 0.9, raw_mask) * (1.0 - smoothstep(0.8, 1.0, raw_mask));
        comp += bg_bloom.rgb * bloom_tint * wrap_boundary * 3.0; 
    }
    
    // --- Optic: Hero Rim Lighting ---
    // Synthesize a harsh cyan edge highlight against the stormy background
    float edge_detect = smoothstep(0.3, 0.5, raw_mask) * (1.0 - smoothstep(0.5, 0.6, raw_mask));
    vec3 rim_color = vec3(0.1, 0.8, 1.0);
    // Multiply by storm intensity so it flares with the lightning
    comp += rim_color * edge_detect * u_storm_intensity * 2.5;
    
    // --- Layer 2: Foreground Skin Plasma ---
    comp += sharp_fg_lightning.rgb * sharp_fg_lightning.a;
    comp += fg_bloom.rgb * bloom_tint * 2.5;

    // --- Optic: Vignette ---
    float dist = length(ndc);
    float vignette = smoothstep(1.5, 0.4, dist);
    comp *= mix(1.0, vignette, 0.6); 

    // --- Optic: ACES Tone Mapping ---
    // Smoothly wraps extreme floating point pixel values (like 4.0 from the lightning core)
    // back accurately into the 0.0-1.0 monitor spectrum, preserving color saturation instead of just blowing to white.
    comp = ACESFilm(comp);

    out_color = vec4(comp, 1.0);
}
