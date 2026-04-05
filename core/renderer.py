import moderngl
import numpy as np

class VFXRenderer:
    def __init__(self, width=640, height=480):
        self.ctx = moderngl.create_context()
        self.width = width
        self.height = height
        
        with open('shaders/composite.vert', 'r') as f:
            vert = f.read()
            
        with open('shaders/composite.frag', 'r') as f:
            comp_frag = f.read()
            
        with open('shaders/blur.vert', 'r') as f:
            blur_vert = f.read()
            
        with open('shaders/blur_x.frag', 'r') as f:
            blur_x_frag = f.read()
            
        with open('shaders/blur_y.frag', 'r') as f:
            blur_y_frag = f.read()
            
        self.prog_comp = self.ctx.program(vertex_shader=vert, fragment_shader=comp_frag)
        self.prog_blur_x = self.ctx.program(vertex_shader=blur_vert, fragment_shader=blur_x_frag)
        self.prog_blur_y = self.ctx.program(vertex_shader=blur_vert, fragment_shader=blur_y_frag)
        
        # Screen quad (UV mapped with flipped Y for Pygame top-left to OpenGL bottom-left translation)
        vertices = np.array([
            -1.0, -1.0,   0.0, 1.0,
             1.0, -1.0,   1.0, 1.0,
            -1.0,  1.0,   0.0, 0.0,
             1.0,  1.0,   1.0, 0.0,
        ], dtype='f4')
        
        self.vbo = self.ctx.buffer(vertices)
        
        self.vao_comp = self.ctx.simple_vertex_array(self.prog_comp, self.vbo, 'in_vert', 'in_texcoord')
        self.vao_blur_x = self.ctx.simple_vertex_array(self.prog_blur_x, self.vbo, 'in_vert', 'in_texcoord')
        self.vao_blur_y = self.ctx.simple_vertex_array(self.prog_blur_y, self.vbo, 'in_vert', 'in_texcoord')
        
        # Base Textures
        self.tex_bg = self.ctx.texture((self.width, self.height), 3)
        self.tex_bg.filter = (moderngl.LINEAR, moderngl.LINEAR)
        
        self.tex_mask = self.ctx.texture((self.width, self.height), 1)
        self.tex_mask.filter = (moderngl.LINEAR, moderngl.LINEAR)
        
        self.tex_vfx_bg = self.ctx.texture((self.width, self.height), 4)
        self.tex_vfx_bg.filter = (moderngl.LINEAR, moderngl.LINEAR)
        
        self.tex_vfx_fg = self.ctx.texture((self.width, self.height), 4)
        self.tex_vfx_fg.filter = (moderngl.LINEAR, moderngl.LINEAR)
        
        # FBO Downsample setup (Double architecture for separated BG/FG bloom)
        fbo_w, fbo_h = self.width // 2, self.height // 2
        
        self.tex_fbo_bg_x = self.ctx.texture((fbo_w, fbo_h), 4)
        self.tex_fbo_bg_x.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.fbo_bg_x = self.ctx.framebuffer(self.tex_fbo_bg_x)
        
        self.tex_fbo_bg_y = self.ctx.texture((fbo_w, fbo_h), 4)
        self.tex_fbo_bg_y.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.fbo_bg_y = self.ctx.framebuffer(self.tex_fbo_bg_y)
        
        self.tex_fbo_fg_x = self.ctx.texture((fbo_w, fbo_h), 4)
        self.tex_fbo_fg_x.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.fbo_fg_x = self.ctx.framebuffer(self.tex_fbo_fg_x)
        
        self.tex_fbo_fg_y = self.ctx.texture((fbo_w, fbo_h), 4)
        self.tex_fbo_fg_y.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.fbo_fg_y = self.ctx.framebuffer(self.tex_fbo_fg_y)
        
        self.prog_blur_x['target_width'].value = float(fbo_w)
        self.prog_blur_y['target_height'].value = float(fbo_h)
        
        # Strict Channel Binding
        self.prog_comp['tex_bg'].value = 0
        self.prog_comp['tex_mask'].value = 1
        self.prog_comp['tex_vfx_bg'].value = 2
        self.prog_comp['tex_vfx_fg'].value = 3
        self.prog_comp['tex_bloom_bg'].value = 4
        self.prog_comp['tex_bloom_fg'].value = 5
        
        if 'u_storm_intensity' in self.prog_comp:
            self.prog_comp['u_storm_intensity'].value = 0.0

    def render(self, bg_frame_rgb_bytes, mask_bytes, vfx_bg_bytes, vfx_fg_bytes, storm_intensity=0.0):
        if 'u_storm_intensity' in self.prog_comp:
            self.prog_comp['u_storm_intensity'].value = float(storm_intensity)
            
        self.tex_bg.write(bg_frame_rgb_bytes)
        self.tex_mask.write(mask_bytes)
        self.tex_vfx_bg.write(vfx_bg_bytes)
        self.tex_vfx_fg.write(vfx_fg_bytes)
        
        # --- Background Bloom Pass ---
        self.fbo_bg_x.use()
        self.fbo_bg_x.clear(0.0, 0.0, 0.0, 0.0)
        self.tex_vfx_bg.use(0)
        self.prog_blur_x['tex'].value = 0
        self.vao_blur_x.render(moderngl.TRIANGLE_STRIP)
        
        self.fbo_bg_y.use()
        self.fbo_bg_y.clear(0.0, 0.0, 0.0, 0.0)
        self.tex_fbo_bg_x.use(0)
        self.prog_blur_y['tex'].value = 0
        self.vao_blur_y.render(moderngl.TRIANGLE_STRIP)
        
        # --- Foreground Bloom Pass ---
        self.fbo_fg_x.use()
        self.fbo_fg_x.clear(0.0, 0.0, 0.0, 0.0)
        self.tex_vfx_fg.use(0)
        self.prog_blur_x['tex'].value = 0
        self.vao_blur_x.render(moderngl.TRIANGLE_STRIP)
        
        self.fbo_fg_y.use()
        self.fbo_fg_y.clear(0.0, 0.0, 0.0, 0.0)
        self.tex_fbo_fg_x.use(0)
        self.prog_blur_y['tex'].value = 0
        self.vao_blur_y.render(moderngl.TRIANGLE_STRIP)
        
        # --- Clean Deep Composite Pass ---
        self.ctx.screen.use()
        
        self.tex_bg.use(0)
        self.tex_mask.use(1)
        self.tex_vfx_bg.use(2)
        self.tex_vfx_fg.use(3)
        self.tex_fbo_bg_y.use(4)
        self.tex_fbo_fg_y.use(5)
        
        self.vao_comp.render(moderngl.TRIANGLE_STRIP)
        
        # Read the final graded pixels from the GPU backbuffer for the DVR
        return self.ctx.screen.read(components=3)
