import bpy
import math

def create_materials():
    materials = {}
    
    # Ground Base
    mat_ground = bpy.data.materials.new(name="Mat_Ground")
    mat_ground.use_nodes = True
    bsdf = mat_ground.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.015, 0.02, 0.03, 1) # Dark tech blue
    bsdf.inputs["Roughness"].default_value = 0.8
    bsdf.inputs["Specular IOR Level"].default_value = 0.2
    materials["ground"] = mat_ground
    
    # Grid Lines
    mat_grid = bpy.data.materials.new(name="Mat_Grid")
    mat_grid.use_nodes = True
    bsdf = mat_grid.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1)
    bsdf.inputs["Emission Color"].default_value = (0.0, 0.3, 0.8, 1) # Cyan glow
    bsdf.inputs["Emission Strength"].default_value = 2.0
    materials["grid"] = mat_grid
    
    # Concrete/House
    mat_house = bpy.data.materials.new(name="Mat_House")
    mat_house.use_nodes = True
    bsdf = mat_house.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.1, 0.1, 0.12, 1)
    bsdf.inputs["Metallic"].default_value = 0.2
    bsdf.inputs["Roughness"].default_value = 0.9
    materials["house"] = mat_house

    # Solar
    mat_solar = bpy.data.materials.new(name="Mat_Solar")
    mat_solar.use_nodes = True
    bsdf = mat_solar.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.01, 0.01, 0.03, 1)
    bsdf.inputs["Metallic"].default_value = 0.9
    bsdf.inputs["Roughness"].default_value = 0.1
    materials["solar"] = mat_solar

    # Battery
    mat_battery = bpy.data.materials.new(name="Mat_Battery")
    mat_battery.use_nodes = True
    bsdf = mat_battery.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.2, 0.2, 0.2, 1)
    bsdf.inputs["Metallic"].default_value = 0.8
    materials["battery"] = mat_battery

    # Battery Glow
    mat_bglow = bpy.data.materials.new(name="Mat_BatteryGlow")
    mat_bglow.use_nodes = True
    bsdf = mat_bglow.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Emission Color"].default_value = (0.0, 1.0, 0.2, 1)
    bsdf.inputs["Emission Strength"].default_value = 0.0
    materials["battery_glow"] = mat_bglow

    # Transformer
    mat_trans = bpy.data.materials.new(name="Mat_Transformer")
    mat_trans.use_nodes = True
    bsdf = mat_trans.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.3, 0.3, 0.35, 1)
    bsdf.inputs["Metallic"].default_value = 0.9
    bsdf.inputs["Roughness"].default_value = 0.3
    materials["transformer"] = mat_trans
    
    # Feeder lines
    mat_feeder = bpy.data.materials.new(name="Mat_Feeder")
    mat_feeder.use_nodes = True
    bsdf = mat_feeder.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0,0,0,1)
    bsdf.inputs["Emission Color"].default_value = (0.0, 0.5, 1.0, 1)
    bsdf.inputs["Emission Strength"].default_value = 1.0
    materials["feeder"] = mat_feeder

    # UI Glass
    mat_ui_glass = bpy.data.materials.new(name="Mat_UIGlass")
    mat_ui_glass.use_nodes = True
    bsdf = mat_ui_glass.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.02, 0.05, 0.1, 0.5)
    bsdf.inputs["Alpha"].default_value = 0.4
    mat_ui_glass.blend_method = 'BLEND'
    materials["ui_glass"] = mat_ui_glass

    # UI Text
    mat_ui_text = bpy.data.materials.new(name="Mat_UIText")
    mat_ui_text.use_nodes = True
    bsdf = mat_ui_text.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0,0,0,1)
    bsdf.inputs["Emission Color"].default_value = (0.8, 0.9, 1.0, 1)
    bsdf.inputs["Emission Strength"].default_value = 2.0
    materials["ui_text"] = mat_ui_text

    return materials

def build_environment(mats):
    # Ground plane
    bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    ground.data.materials.append(mats["ground"])

    # Decorative wireframe grid overlay
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=50, y_subdivisions=50, size=300, location=(0,0,0.05))
    grid = bpy.context.active_object
    grid.name = "TechGrid"
    grid.data.materials.append(mats["grid"])
    
    # Add wireframe modifier
    wf = grid.modifiers.new(name="Wireframe", type='WIREFRAME')
    wf.thickness = 0.05
    wf.use_replace = True

def build_transformer(mats):
    # Base pad
    bpy.ops.mesh.primitive_cube_add(size=4, location=(0, 0, 0.5))
    pad = bpy.context.active_object
    pad.data.materials.append(mats["ground"])
    
    # Main body
    bpy.ops.mesh.primitive_cube_add(size=3.5, location=(0, 0, 3.5))
    body = bpy.context.active_object
    body.name = "Transformer_Body"
    body.data.materials.append(mats["transformer"])
    
    # Bushings
    for i in range(3):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.5, location=(-1 + i*1.0, 0, 6.0))
        bushing = bpy.context.active_object
        bushing.data.materials.append(mats["transformer"])
        bushing.parent = body
        
    # Gateway Box
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(2.2, 0, 3.0))
    gw = bpy.context.active_object
    gw.name = "Gateway"
    gw.data.materials.append(mats["transformer"])
    gw.parent = body
    
    # Gateway Antenna
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.0, location=(2.2, 0, 4.0))
    ant = bpy.context.active_object
    ant.data.materials.append(mats["battery_glow"]) # repurposing glow
    ant.parent = gw
    
    return body, gw

def build_house(mats, location, index, has_battery=True):
    x, y, z = location
    
    # Main House
    bpy.ops.mesh.primitive_cube_add(size=2.5, location=(x, y, 1.25))
    house = bpy.context.active_object
    house.name = f"House_{index:03d}"
    house.data.materials.append(mats["house"])
    
    # Roof (Pyramid)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=2.0, radius2=0, depth=1.5, location=(x, y, 3.25))
    roof = bpy.context.active_object
    roof.rotation_euler[2] = math.pi / 4
    roof.data.materials.append(mats["house"])
    roof.parent = house
    
    # Solar
    bpy.ops.mesh.primitive_plane_add(size=1.8, location=(x, y-0.6, 3.0))
    solar = bpy.context.active_object
    solar.rotation_euler[0] = math.radians(35)
    solar.data.materials.append(mats["solar"])
    solar.parent = house
    
    # Battery
    batt = None
    bglow = None
    if has_battery:
        bpy.ops.mesh.primitive_cube_add(size=0.6, location=(x+1.5, y, 0.5))
        batt = bpy.context.active_object
        batt.name = f"Battery_{index:03d}"
        batt.data.materials.append(mats["battery"])
        batt.parent = house
        
        # Inner glow core for battery to show dispatch
        bpy.ops.mesh.primitive_plane_add(size=0.4, location=(x+1.5, y+0.31, 0.5))
        bglow = bpy.context.active_object
        bglow.name = f"BatteryGlow_{index:03d}"
        bglow.rotation_euler[0] = math.radians(90)
        # We need a unique material instance per battery to animate independently
        mat_inst = mats["battery_glow"].copy()
        bglow.data.materials.append(mat_inst)
        bglow.parent = batt

    return house, bglow

def build_feeder_lines(transformer, houses, mats):
    # Creates simple cylinder curves from transformer to houses
    for i, h in enumerate(houses):
        hx, hy, hz = h.location
        
        # To avoid massive geometry, we just draw a line from central pole to house
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.0)
        line = bpy.context.active_object
        
        # Calculate vector
        tx, ty, tz = transformer.location[0], transformer.location[1], 5.0
        dx = hx - tx
        dy = hy - ty
        dz = 2.0 - tz # go to roof height
        dist = math.sqrt(dx**2 + dy**2 + dz**2)
        
        line.scale[2] = dist
        line.location = (tx + dx/2, ty + dy/2, tz + dz/2)
        
        # Look at
        rot_y = math.acos(dz/dist)
        rot_z = math.atan2(dy, dx)
        line.rotation_euler = (0, rot_y, rot_z)
        
        line.data.materials.append(mats["feeder"])
        line.name = f"FeederLine_{i:03d}"
