import random
import math

def generate_fractal_lightning(start_pos, end_pos, time_seed, width, height, depth=0, max_depth=2, base_thickness=6.0, base_alpha=255.0, fork_prob=0.40, layer='fg'):
    """
    Recursively generates fractal lightning branches.
    Returns a list of segment dictionaries: {'start': (x,y), 'end': (x,y), 'thickness': int, 'alpha': int, 'layer': str}
    """
    segments = []
    
    sx, sy = start_pos
    ex, ey = end_pos
    
    vec_x = ex - sx
    vec_y = ey - sy
    length = math.hypot(vec_x, vec_y)
    
    if length < 5:
        return []
        
    # Spatial jitter seeded with time hash: creates the rapid electrical 60fps snap
    random.seed(int(time_seed * 1000) + int(sx) + int(sy) + depth*31)
    
    num_pts = random.randint(8, 15)
    pts = [start_pos]
    
    for i in range(1, num_pts):
        t = i / num_pts
        base_x = sx + vec_x * t
        base_y = sy + vec_y * t
        
        perp_x = -vec_y / length
        perp_y = vec_x / length
        
        # Central bulge tapering algorithm for electrical arcing
        taper = math.sin(t * math.pi)
        disp = random.uniform(-length * 0.15, length * 0.15) * taper
        
        px = base_x + perp_x * disp
        py = base_y + perp_y * disp
        pts.append((px, py))
        
    pts.append(end_pos)
    
    for i in range(len(pts) - 1):
        t = i / (len(pts) - 1)
        
        # Heavy exponential tapering line thickness and fading alpha for cinematic realism
        taper_mod = math.pow(1.0 - t, 1.5) # Exponent makes tips sharp
        thick = max(1.0, base_thickness * taper_mod)
        alph = max(0, int(base_alpha * (0.2 + 0.8 * taper_mod)))
        
        # Segment Culling: Skip if completely outside screen bounds
        sx, sy = pts[i]
        ex, ey = pts[i+1]
        
        # Simple bounding box check
        min_x, max_x = min(sx, ex), max(sx, ex)
        min_y, max_y = min(sy, ey), max(sy, ey)
        
        # If segment is completely to the left, right, top, or bottom of screen, cull it
        if not (max_x < 0 or min_x > width or max_y < 0 or min_y > height):
            segments.append({
                'type': 'line',
                'start': (sx, sy),
                'end': (ex, ey),
                'thickness': thick,
                'alpha': alph,
                'layer': layer
            })
        
        # Fractal fork probability
        if depth < max_depth and random.random() < fork_prob:
            fork_start = pts[i]
            
            # Sharp angle split
            angle = math.atan2(vec_y, vec_x)
            dev = math.radians(random.uniform(25, 75))
            if random.random() > 0.5:
                dev = -dev
            fork_angle = angle + dev
            
            # Shorter branch
            fork_length = length * random.uniform(0.3, 0.6) * (1.0 - t)
            
            fx = fork_start[0] + math.cos(fork_angle) * fork_length
            fy = fork_start[1] + math.sin(fork_angle) * fork_length
            
            # Recurse with strict depth limit
            child_segments = generate_fractal_lightning(
                fork_start, (fx, fy), 
                time_seed=time_seed, 
                width=width,
                height=height,
                depth=depth+1, 
                max_depth=max_depth,
                base_thickness=thick * 0.6,    # Fork is thinner
                base_alpha=alph * 0.8,         # Fork is slightly dimmer
                fork_prob=fork_prob,
                layer=layer
            )
            segments.extend(child_segments)
            
    return segments

def get_point_spark(center, width, height, time_seed):
    """
    Highly volatile cluster of lightning anchored exactly to the fingertip.
    """
    all_shapes = []
    random.seed(int(time_seed * 2000)) # Ultra high-frequency jitter lock
    num_sparks = random.randint(5, 10)
    radius = width * 0.08 # Restrict length to simulate miniature Tesla coil spark
    
    for i in range(num_sparks):
        angle = random.uniform(0, math.pi * 2)
        ex = center[0] + math.cos(angle) * radius * random.uniform(0.3, 1.0)
        ey = center[1] + math.sin(angle) * radius * random.uniform(0.3, 1.0)
        
        segs = generate_fractal_lightning(
            center, (ex, ey), 
            time_seed, width, height,
            depth=0, 
            max_depth=1, # Super fast recursion for miniature sparks
            base_thickness=3.0, 
            base_alpha=255.0  # Pure fiery white
        )
        all_shapes.extend(segs)
        
    return all_shapes

def get_superhero_aura(landmarks, face_landmarks, screen_center, width, height, time_seed):
    """
    Simulates 3D depth by combining 4 environmental strikes and 21 foreground plasma nodes.
    Now injects glowing eye plasma flares based on MediaPipe FaceMesh.
    """
    all_shapes = []
    
    # Layer: FaceMesh logic bypassed/removed per user request.
    
    # Layer A: Massive Volatile Background Strikes (Thor Super-Storm)
    random.seed(int(time_seed * 400))
    radius_bg = math.hypot(width, height) * 1.5
    
    num_strikes = random.randint(8, 12) # Huge increase in volume
    for _ in range(num_strikes):
        angle = random.uniform(0, math.pi * 2) # Free 360-degree chaotic propagation
        
        # Originate wildly anywhere behind the user torso
        dist = random.uniform(0, width * 0.3)
        start_x = screen_center[0] + math.cos(angle) * dist
        start_y = screen_center[1] + math.sin(angle) * dist
        
        ex = screen_center[0] + math.cos(angle) * radius_bg
        ey = screen_center[1] + math.sin(angle) * radius_bg
        
        segs = generate_fractal_lightning(
            (start_x, start_y), (ex, ey), 
            time_seed + angle, width, height,
            depth=0, 
            max_depth=1, 
            base_thickness=random.uniform(4.0, 10.0), # Hyper-variance in power
            base_alpha=random.randint(150, 255), 
            fork_prob=0.95, # Extreme branching rate to imitate raw atmospheric energy
            layer='bg'
        )
        all_shapes.extend(segs)
        
    # Layer B: Superhero Foreground Plasma
    random.seed(int(time_seed * 600) + 1234)
    
    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4), # Thumb
        (0, 5), (5, 6), (6, 7), (7, 8), # Index
        (5, 9), (9, 10), (10, 11), (11, 12), # Middle
        (9, 13), (13, 14), (14, 15), (15, 16), # Ring
        (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) # Pinky
    ]
    
    for connection in HAND_CONNECTIONS:
        # Draw highly volatile skin electricity between joints
        lm1 = landmarks[connection[0]]
        lm2 = landmarks[connection[1]]
        
        segs = generate_fractal_lightning(
            lm1, lm2, time_seed + connection[0], width, height,
            depth=0,
            max_depth=1, # Allow small aggressive sparking off the fingers
            base_thickness=random.uniform(2.5, 5.0), # High variance popping
            base_alpha=255.0, # 100% Core White/Blue Intensity for foreground
            fork_prob=0.3, # 30% chance for mini hand-sparks
            layer='fg'
        )
        all_shapes.extend(segs)
            
    return all_shapes
