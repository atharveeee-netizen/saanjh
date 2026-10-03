import bpy
import math
import os
import json

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Clear materials to prevent duplication
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)

def build_scene_and_animate(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    num_homes = data["metadata"]["num_homes"]
    fps = data["metadata"]["fps"]
    bpy.context.scene.render.fps = fps
    
    frames_data = data["frames"]
    total_frames = len(frames_data) * fps # 1 simulation step = 1 second of animation
    bpy.context.scene.frame_end = total_frames
    
    # Create Ground
    bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, 0))
    ground = bpy.context.active_object
    mat_ground = bpy.data.materials.new(name="GroundMat")
    mat_ground.diffuse_color = (0.1, 0.1, 0.12, 1)
    ground.data.materials.append(mat_ground)
    
    # Create Transformer
    bpy.ops.mesh.primitive_cylinder_add(radius=2.0, depth=5, location=(0, 0, 2.5))
    transformer = bpy.context.active_object
    mat_trans = bpy.data.materials.new(name="TransformerMat")
    mat_trans.use_nodes = True
    trans_bsdf = mat_trans.node_tree.nodes["Principled BSDF"]
    trans_bsdf.inputs["Base Color"].default_value = (0.2, 0.2, 0.2, 1)
    transformer.data.materials.append(mat_trans)
    
    # Create Houses
    radius = 30
    mat_house = bpy.data.materials.new(name="HouseMat")
    mat_house.diffuse_color = (0.7, 0.7, 0.75, 1)
    
    mat_battery = bpy.data.materials.new(name="BatteryMat")
    mat_battery.use_nodes = True
    batt_bsdf = mat_battery.node_tree.nodes["Principled BSDF"]
    batt_bsdf.inputs["Emission Strength"].default_value = 0.0 # Will animate
    batt_bsdf.inputs["Emission Color"].default_value = (0.0, 1.0, 0.2, 1) # Green
    
    for i in range(num_homes):
        angle = (i / num_homes) * 2 * math.pi
        r = radius + (i % 4) * 4
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        
        bpy.ops.mesh.primitive_cube_add(size=2.5, location=(x, y, 1.25))
        house = bpy.context.active_object
        house.data.materials.append(mat_house)
        
        if i % 3 != 0: # 66% have batteries
            bpy.ops.mesh.primitive_cube_add(size=0.8, location=(x, y, 3.0))
            batt = bpy.context.active_object
            batt.parent = house
            batt.data.materials.append(mat_battery)
            
    # Setup Camera
    bpy.ops.object.camera_add(location=(50, -50, 40), rotation=(math.radians(55), 0, math.radians(45)))
    cam = bpy.context.active_object
    bpy.context.scene.camera = cam
    
    # Setup Output Path
    base_dir_for_video = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    video_output_dir = os.path.join(base_dir_for_video, 'artifacts', 'video')
    os.makedirs(video_output_dir, exist_ok=True)
    
    bpy.context.scene.render.filepath = os.path.join(video_output_dir, 'frames', 'frame_')
    bpy.context.scene.render.image_settings.file_format = 'JPEG'
    
    # Fast preview settings
    bpy.context.scene.frame_step = 20
    
    # Lighting
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 20))
    sun = bpy.context.active_object
    sun.data.energy = 3.0
    
    # --- ANIMATION PASS ---
    for step, frame_data in enumerate(frames_data):
        blender_frame = step * fps + 1
        
        # 1. Animate Transformer Stress (Color blends from Grey to Red)
        stress = frame_data["transformer_stress"]
        r = 0.2 + (0.8 * stress)
        g = 0.2 - (0.1 * stress)
        b = 0.2 - (0.1 * stress)
        trans_bsdf.inputs["Base Color"].default_value = (r, g, b, 1)
        trans_bsdf.inputs["Base Color"].keyframe_insert(data_path="default_value", frame=blender_frame)
        
        # 2. Animate Battery Dispatch (Emission Strength)
        # If flexibility is being delivered, make batteries glow.
        flex = frame_data["flexibility_delivered_kw"]
        glow_strength = min(10.0, flex / 5.0) # Arbitrary scale for visual effect
        batt_bsdf.inputs["Emission Strength"].default_value = glow_strength
        batt_bsdf.inputs["Emission Strength"].keyframe_insert(data_path="default_value", frame=blender_frame)

    print("Executing final render...")
    bpy.ops.render.render(animation=True)

if __name__ == "__main__":
    clear_scene()
    
    # Path is relative to the script execution which is typically inside the repository root
    # or inside the blender script execution context.
    import sys
    # Find the artifacts path. If ran from saanjh root:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    json_path = os.path.join(base_dir, 'artifacts', 'blender', 'saanjh_visualization_data.json')
    
    if os.path.exists(json_path):
        build_scene_and_animate(json_path)
        print(f"Data-driven animation generated successfully from {json_path}")
    else:
        print(f"ERROR: Could not find JSON contract at {json_path}")
