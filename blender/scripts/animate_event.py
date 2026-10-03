import bpy
import math

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def create_neighbourhood():
    # Ground
    bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    
    # Material for ground
    mat_ground = bpy.data.materials.new(name="GroundMat")
    mat_ground.diffuse_color = (0.1, 0.1, 0.1, 1)
    ground.data.materials.append(mat_ground)

    # Transformer
    bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=4, location=(0, 0, 2))
    transformer = bpy.context.active_object
    transformer.name = "Transformer"
    
    mat_trans = bpy.data.materials.new(name="TransMat")
    mat_trans.diffuse_color = (0.3, 0.3, 0.3, 1)
    transformer.data.materials.append(mat_trans)

    # Houses
    num_houses = 60
    radius = 25
    
    mat_house = bpy.data.materials.new(name="HouseMat")
    mat_house.diffuse_color = (0.8, 0.8, 0.8, 1)
    
    mat_batt = bpy.data.materials.new(name="BatteryMat")
    mat_batt.diffuse_color = (0.0, 0.8, 0.2, 1) # Green

    for i in range(num_houses):
        angle = (i / num_houses) * 2 * math.pi
        
        # Add some noise to radius
        r = radius + (i % 3) * 5
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        
        bpy.ops.mesh.primitive_cube_add(size=2.5, location=(x, y, 1.25))
        house = bpy.context.active_object
        house.name = f"House_{i}"
        house.data.materials.append(mat_house)
        
        # 70% have batteries
        if i % 3 != 0: 
            bpy.ops.mesh.primitive_cube_add(size=0.6, location=(x, y, 3))
            batt = bpy.context.active_object
            batt.name = f"Battery_{i}"
            batt.parent = house
            batt.data.materials.append(mat_batt)

def setup_camera_and_light():
    # Camera
    bpy.ops.object.camera_add(location=(40, -40, 30), rotation=(math.radians(60), 0, math.radians(45)))
    cam = bpy.context.active_object
    bpy.context.scene.camera = cam
    
    # Sun
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 20))
    sun = bpy.context.active_object
    sun.data.energy = 5

if __name__ == "__main__":
    clear_scene()
    create_neighbourhood()
    setup_camera_and_light()
    print("SAANJH 3D Scene generated successfully.")
