import bpy
import math
import os
import sys
import json
import random

# Add current directory to path to import local modules
sys.path.append(os.path.dirname(__file__))

import procedural.build_env as build_env
import procedural.build_ui as build_ui

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Clear materials and cameras
    for block in [bpy.data.materials, bpy.data.cameras, bpy.data.curves, bpy.data.meshes]:
        for data in block:
            block.remove(data)

    bpy.app.handlers.frame_change_pre.clear()

def format_time(hour_float):
    h = int(hour_float)
    m = int((hour_float - h) * 60)
    return f"{h:02d}:{m:02d}:00"

def get_event_status(hour, stress, flex):
    if hour < 17.0:
        return "NORMAL"
    elif hour < 18.0:
        return "FORECAST WARNING"
    elif stress > 0.5 and flex == 0:
        return "STRESS DETECTED"
    elif flex > 0:
        return "DISPATCH ACTIVE"
    else:
        return "RECOVERY"

def render_scene(json_path, is_preview=False):
    clear_scene()
    
    # Setup rendering engine for SPEED and visual quality (Eevee)
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    num_homes = data["metadata"]["num_homes"]
    fps = data["metadata"]["fps"]
    bpy.context.scene.render.fps = fps
    
    frames_data = data["frames"]
    total_frames = len(frames_data) * fps # Interpolate simulation steps to seconds
    bpy.context.scene.frame_end = total_frames
    
    # 1. Build Materials
    mats = build_env.create_materials()
    
    # 2. Build Environment
    build_env.build_environment(mats)
    
    # 3. Build Transformer
    transformer, gateway = build_env.build_transformer(mats)
    
    # 4. Build Houses
    houses = []
    battery_glows = []
    
    grid_size = int(math.ceil(math.sqrt(num_homes)))
    spacing = 6.0
    
    offset_x = (grid_size * spacing) / 2.0
    offset_y = (grid_size * spacing) / 2.0
    
    for i in range(num_homes):
        row = i // grid_size
        col = i % grid_size
        
        # Don't place houses directly over the transformer (center)
        x = (col * spacing) - offset_x
        y = (row * spacing) - offset_y
        
        # Push away from center
        if abs(x) < 5 and abs(y) < 5:
            x += (5 * math.copysign(1, x)) if x != 0 else 5
            y += (5 * math.copysign(1, y)) if y != 0 else 5
            
        house, bglow = build_env.build_house(mats, (x, y, 0), i, has_battery=True)
        houses.append(house)
        battery_glows.append(bglow)
        
    # 5. Build Feeder Lines
    build_env.build_feeder_lines(transformer, houses, mats)
    
    # 6. Setup Camera
    # High angled cinematic shot
    bpy.ops.object.camera_add(location=(0, -45, 30), rotation=(math.radians(60), 0, 0))
    cam = bpy.context.active_object
    bpy.context.scene.camera = cam
    
    # 7. Setup UI
    ui = build_ui.build_hud(cam, mats)
    
    # 8. Setup Lighting
    bpy.ops.object.light_add(type='SUN', location=(0, -20, 20))
    sun = bpy.context.active_object
    sun.data.energy = 2.0
    sun.data.color = (1.0, 0.9, 0.8) # Sunset glow
    sun.rotation_euler = (math.radians(45), 0, 0)
    
    # Rim light for cinematic feel
    bpy.ops.object.light_add(type='AREA', location=(0, 40, 10))
    rim = bpy.context.active_object
    rim.data.energy = 1000.0
    rim.data.color = (0.2, 0.5, 1.0)
    rim.scale = (50, 50, 1)
    rim.rotation_euler = (math.radians(-45), 0, 0)
    
    # --- ANIMATION DRIVER (Frame Change Handler) ---
    def update_frame(scene):
        curr_frame = scene.frame_current
        # Find which simulation step we are in
        sim_step = min(curr_frame // fps, len(frames_data) - 1)
        next_step = min(sim_step + 1, len(frames_data) - 1)
        
        # Interpolation factor
        t = (curr_frame % fps) / float(fps)
        
        f1 = frames_data[sim_step]
        f2 = frames_data[next_step]
        
        # Interpolate values
        hour = f1["hour"] + (f2["hour"] - f1["hour"]) * t
        load = f1["feeder_load_kw"] + (f2["feeder_load_kw"] - f1["feeder_load_kw"]) * t
        trans_pct = f1["transformer_loading_pct"] + (f2["transformer_loading_pct"] - f1["transformer_loading_pct"]) * t
        stress = f1["transformer_stress"] + (f2["transformer_stress"] - f1["transformer_stress"]) * t
        flex = f1["flexibility_delivered_kw"] + (f2["flexibility_delivered_kw"] - f1["flexibility_delivered_kw"]) * t
        
        # Active homes doesn't interpolate well conceptually, snap it or smooth it?
        # Let's snap it to integer
        active_homes = int(f1["active_homes"])
        
        # Multi-Shot Cinematic Director across 6 discrete operational shots
        prog = float(curr_frame) / float(max(1, total_frames))
        
        # Shot 1 (0-6s, prog 0.0 to 0.167): Wide establishing shot
        if prog < 0.167:
            st = prog / 0.167
            cam.location = (0, -55 + 13*st, 36 - 8*st)
            cam.rotation_euler = (math.radians(56 + 6*st), 0, 0)
            sun.data.energy = 2.8 - 0.6*st
            sun.data.color = (1.0, 0.95, 0.85)
            shot_status = "NORMAL OPERATION"
            ui_status_color = (0.2, 0.8, 1.0, 1)

        # Shot 2 (6-12s, prog 0.167 to 0.333): Move to transformer & feeder
        elif prog < 0.333:
            st = (prog - 0.167) / 0.166
            cam.location = (-2*st, -42 + 14*st, 28 - 10*st)
            cam.rotation_euler = (math.radians(62 + 2*st), 0, math.radians(-5*st))
            sun.data.energy = 2.2 - 0.8*st
            sun.data.color = (1.0, 0.75 - 0.2*st, 0.45)
            shot_status = "FORECAST: SUNSET APPROACHING"
            ui_status_color = (1.0, 0.8, 0.2, 1)

        # Shot 3 (12-18s, prog 0.333 to 0.50): Evening transition / Solar cliff
        elif prog < 0.50:
            st = (prog - 0.333) / 0.167
            cam.location = (-2 - 2*st, -28 + 8*st, 18 - 5*st)
            cam.rotation_euler = (math.radians(64 + 4*st), 0, math.radians(-5 - 3*st))
            sun.data.energy = max(0.2, 1.4 - 1.1*st)
            sun.data.color = (0.4, 0.3, 0.7)
            shot_status = "RENEWABLE DEFICIT DETECTED"
            ui_status_color = (1.0, 0.2, 0.2, 1)

        # Shot 4 (18-24s, prog 0.50 to 0.667): SAANJH Gateway & LoRa request
        elif prog < 0.667:
            st = (prog - 0.50) / 0.167
            cam.location = (-4 + 8*st, -20 - 4*st, 13 + 3*st)
            cam.rotation_euler = (math.radians(68 - 6*st), 0, math.radians(-8 + 14*st))
            sun.data.energy = 0.25
            sun.data.color = (0.2, 0.3, 0.8)
            shot_status = "FLEXIBILITY REQUEST DISPATCHED"
            ui_status_color = (0.0, 0.9, 1.0, 1)

        # Shot 5 (24-30s, prog 0.667 to 0.833): Battery activation & grid relief
        elif prog < 0.833:
            st = (prog - 0.667) / 0.166
            cam.location = (4 + 4*st, -24 - 4*st, 16 + 2*st)
            cam.rotation_euler = (math.radians(62 - 4*st), 0, math.radians(6 - 6*st))
            sun.data.energy = 0.2
            sun.data.color = (0.15, 0.25, 0.7)
            shot_status = "DISPATCH ACTIVE: 56.2 kW"
            ui_status_color = (0.2, 1.0, 0.3, 1)

        # Shot 6 (30-36s, prog 0.833 to 1.0): Pull back to wide stabilized grid
        else:
            st = (prog - 0.833) / 0.167
            cam.location = (8 - 8*st, -28 - 22*st, 18 + 14*st)
            cam.rotation_euler = (math.radians(58), 0, 0)
            sun.data.energy = 0.25
            sun.data.color = (0.1, 0.2, 0.5)
            shot_status = "GRID RECOVERED | SAANJH ACTIVE"
            ui_status_color = (0.2, 1.0, 0.4, 1)

        # Update UI Text
        ui["clock"].data.body = f"TIME: {format_time(hour)}"
        ui["ana_load"].data.body = f"FEEDER LOAD: {load:.1f} kW"
        ui["ana_load_pct"].data.body = f"TRANSFORMER: {trans_pct:.1f}%"
        ui["ana_flex"].data.body = f"FLEXIBILITY: {flex:.1f} kW"
        ui["evt_homes"].data.body = f"ACTIVE HOMES: {active_homes} / {num_homes}"
        ui["evt_status"].data.body = f"STATUS: {shot_status}"
        ui["evt_status"].data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = ui_status_color

        # Update 3D Geometry properties
        # Transformer color based on stress
        t_mat = mats["transformer"].node_tree.nodes["Principled BSDF"]
        t_mat.inputs["Base Color"].default_value = (0.3 + stress*0.5, 0.3 - stress*0.2, 0.35 - stress*0.2, 1)
        
        # Feeder glow based on load
        f_mat = mats["feeder"].node_tree.nodes["Principled BSDF"]
        f_mat.inputs["Emission Strength"].default_value = 1.0 + (trans_pct / 100.0) * 5.0
        
        # Battery glow logic
        random.seed(sim_step)
        active_indices = set(random.sample(range(num_homes), active_homes))
        
        for idx, bglow in enumerate(battery_glows):
            if not bglow: continue
            b_mat = bglow.data.materials[0].node_tree.nodes["Principled BSDF"]
            if idx in active_indices and flex > 0:
                b_mat.inputs["Emission Strength"].default_value = 12.0
            else:
                b_mat.inputs["Emission Strength"].default_value = 0.0

    # Attach handler
    bpy.app.handlers.frame_change_pre.append(update_frame)
    
    # Initial update
    bpy.context.scene.frame_set(1)
    
    # --- RENDER SETUP ---
    base_dir_for_video = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    video_output_dir = os.path.join(base_dir_for_video, 'artifacts', 'video')
    os.makedirs(os.path.join(video_output_dir, 'frames'), exist_ok=True)
    
    bpy.context.scene.render.filepath = os.path.join(video_output_dir, 'frames', 'frame_')
    bpy.context.scene.render.image_settings.file_format = 'JPEG'
    
    if is_preview:
        bpy.context.scene.frame_step = 60 # Very fast preview, 1 frame every 2 seconds of sim
        print("Executing PREVIEW render...")
    else:
        bpy.context.scene.frame_step = 1 # Full render
        print("Executing FINAL render...")
        
    bpy.ops.render.render(animation=True)

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    json_path = os.path.join(base_dir, 'artifacts', 'blender', 'saanjh_visualization_data.json')
    
    if os.path.exists(json_path):
        is_prev = "--preview" in sys.argv
        render_scene(json_path, is_preview=is_prev)
    else:
        print(f"ERROR: Could not find JSON contract at {json_path}")
