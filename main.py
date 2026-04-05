import pygame
import time
import cv2
import math
from core.tracker import HandTracker
from core.vfx import get_superhero_aura, get_point_spark, generate_fractal_lightning
from core.renderer import VFXRenderer

def lerp(a, b, t):
    """Linear Interpolation for smooth tracking, zero perceptual jitter"""
    if isinstance(a, tuple):
        return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))
    return a + (b - a) * t

def main():
    WIDTH, HEIGHT = 640, 480
    
    pygame.init()
    
    # ModernGL requires at least Core Profile 3.3
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
    pygame.display.set_caption("Real-Time VFX - Cinematic Aura Engine Init...")
    
    tracker = HandTracker(camera_index=0, width=WIDTH, height=HEIGHT)
    renderer = VFXRenderer(width=WIDTH, height=HEIGHT)
    
    # Pygame transparent surfaces for CPU segmented layers
    bg_vfx_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    fg_vfx_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    comb_vfx_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    clock = pygame.time.Clock()
    running = True
    
    smooth_target = (WIDTH//2, HEIGHT//2)
    last_state = 'Idle'
    t_start = time.time()
    
    # DVR Settings
    is_recording = False
    video_writer = None
    
    frame_count = 0
    smooth_landmarks = []
    cached_shapes = []
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    is_recording = not is_recording
                    if is_recording:
                        # Initialize high-quality OpenCV encoder
                        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                        video_writer = cv2.VideoWriter('vfx_output.mp4', fourcc, 30.0, (WIDTH, HEIGHT))
                    else:
                        if video_writer is not None:
                            video_writer.release()
                            video_writer = None
                            
        # 1. Fetch latest async tracking info
        frame, landmarks, state, mask, face_landmarks = tracker.get_latest()
        
        if frame is None:
            # Wait for webcam
            clock.tick(60)
            continue
            
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # clear VFX texture space
        bg_vfx_surface.fill((0, 0, 0, 0))
        fg_vfx_surface.fill((0, 0, 0, 0))
        current_time = time.time() - t_start
        
        storm_intensity = 0.0
        
        # 2. Logic & Rendering
        if landmarks is not None:
            import random
            if state == 'Point':
                # Index Tip - Sparks
                target_x = int(landmarks[8][0] * WIDTH)
                target_y = int(landmarks[8][1] * HEIGHT)
                
                if last_state != 'Point':
                    smooth_target = (target_x, target_y)
                else:
                    smooth_target = lerp(smooth_target, (target_x, target_y), 0.4)
                
                # Recalculate main structure every 3 frames or on state change
                if last_state != 'Point' or frame_count % 3 == 0:
                    cached_shapes = get_point_spark(smooth_target, WIDTH, HEIGHT, current_time)
                
            elif state == 'Aura':
                # Superhero Hand Aura
                current_landmarks = [(int(lm[0] * WIDTH), int(lm[1] * HEIGHT)) for lm in landmarks]
                
                if last_state != 'Aura':
                    smooth_landmarks = current_landmarks
                else:
                    smooth_landmarks = [lerp(smooth_landmarks[i], current_landmarks[i], 0.3) for i in range(21)]
                    
                # Recalculate main structure every 3 frames or on state change
                if last_state != 'Aura' or frame_count % 3 == 0:
                    screen_center = (WIDTH // 2, HEIGHT // 2)
                    cached_shapes = get_superhero_aura(smooth_landmarks, face_landmarks, screen_center, WIDTH, HEIGHT, time_seed=current_time)
                
                # Highly chaotic rapid flashing corresponding to the lightning noise
                # Raise to power of 3 to create a dark room that violently explodes with lightning flashes
                val = random.random()
                storm_intensity = math.pow(val, 3) * 1.8
            else:
                cached_shapes = []
            
            # Apply Jitter and draw
            for shape in cached_shapes:
                # Route to surface
                target_surface = bg_vfx_surface if shape.get('layer', 'fg') == 'bg' else fg_vfx_surface
                
                if shape['type'] == 'line':
                    if frame_count % 3 != 0:
                        jx, jy = random.uniform(-2.5, 2.5), random.uniform(-2.5, 2.5)
                        c_start = (shape['start'][0] + jx, shape['start'][1] + jy)
                        c_end = (shape['end'][0] + jx, shape['end'][1] + jy)
                    else:
                        c_start = shape['start']
                        c_end = shape['end']
                        
                    alpha = int(shape['alpha'])
                    thick = max(1, int(shape['thickness']))
                    
                    if shape.get('layer', 'fg') == 'bg':
                        # Massive background lightning with Cyan outer core and blinding White inner core
                        c_outer = (50, 150, 255, alpha)
                        pygame.draw.line(target_surface, c_outer, c_start, c_end, thick + 2)
                        if thick > 2:
                            c_inner = (255, 255, 255, alpha)
                            pygame.draw.line(target_surface, c_inner, c_start, c_end, max(1, thick // 3))
                    else:
                        # Foreground hand branches
                        c_outer = (100, 200, 255, alpha)
                        pygame.draw.line(target_surface, c_outer, c_start, c_end, thick)
                        if thick >= 2:
                            c_inner = (255, 255, 255, alpha)
                            pygame.draw.line(target_surface, c_inner, c_start, c_end, max(1, thick // 2))
                    
                elif shape['type'] == 'circle':
                    if frame_count % 3 != 0:
                        jx, jy = random.uniform(-2.5, 2.5), random.uniform(-2.5, 2.5)
                        c_coord = (shape['center'][0] + jx, shape['center'][1] + jy)
                    else:
                        c_coord = shape['center']
                        
                    if shape.get('is_white_core', False):
                        c = (255, 255, 255, int(shape['alpha']))
                    else:
                        c = (150, 220, 255, int(shape['alpha']))
                        
                    pygame.draw.circle(target_surface, c, c_coord, shape['radius'])
                        
            last_state = state
        else:
            last_state = 'Idle'
            cached_shapes = []
            
        frame_count += 1
        
        # 3. GLSL Hardware Accelerated Cinematic Passes
        import numpy as np
        if mask is None:
            mask_bytes = np.zeros((HEIGHT, WIDTH), dtype=np.uint8).tobytes()
        else:
            mask_bytes = mask.tobytes()
            
        # 3. Offload all textures to GPU
        vfx_bg_bytes = pygame.image.tostring(bg_vfx_surface, 'RGBA')
        vfx_fg_bytes = pygame.image.tostring(fg_vfx_surface, 'RGBA')
        
        screen_bytes = renderer.render(frame_rgb.tobytes(), mask_bytes, vfx_bg_bytes, vfx_fg_bytes, storm_intensity)
        
        # --- Internal DVR Extraction ---
        if is_recording and video_writer is not None:
            # Reconstruct the raw linear data sequence returned by ModernGL into a 3D Tensor
            frame_array = np.frombuffer(screen_bytes, dtype=np.uint8).reshape((HEIGHT, WIDTH, 3))
            # OpenGL coordinate space is Y-up. OpenCV is Y-down. Flip vertically.
            flipped_rgb = cv2.flip(frame_array, 0)
            # Encode back to BGR for MP4 standard writing
            frame_bgr = cv2.cvtColor(flipped_rgb, cv2.COLOR_RGB2BGR)
            video_writer.write(frame_bgr)
        
        # 4. Flip Pygame buffer
        pygame.display.flip()
        clock.tick(60)
        
        # Update window title with diagnostics
        fps = int(clock.get_fps())
        rec_flag = "[RECORDING - 30 FPS] | " if is_recording else ""
        pygame.display.set_caption(f"{rec_flag}VFX Cinematic | Dual-Pass Bloom | State: {state} | FPS: {fps}")
        
    tracker.stop()
    if video_writer is not None:
        video_writer.release()
    pygame.quit()

if __name__ == '__main__':
    main()
