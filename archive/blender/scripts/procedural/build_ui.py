import bpy
import math

def create_ui_element(name, text, location, mats, parent_cam, scale=0.1, is_text=True, size=(1,1)):
    if is_text:
        bpy.ops.object.text_add(location=(0,0,0))
        obj = bpy.context.active_object
        obj.name = name
        obj.data.body = text
        obj.data.materials.append(mats["ui_text"])
        obj.scale = (scale, scale, scale)
        
        # Align text
        obj.data.align_x = 'LEFT'
        obj.data.align_y = 'TOP'
        
    else:
        # Create a background panel plane
        bpy.ops.mesh.primitive_plane_add(size=1)
        obj = bpy.context.active_object
        obj.name = name
        obj.scale = (size[0], size[1], 1)
        obj.data.materials.append(mats["ui_glass"])
        
    # Parent to camera
    obj.parent = parent_cam
    
    # Location relative to camera (Z must be negative to be in front)
    obj.location = location
    
    return obj

def build_hud(cam, mats):
    ui_elements = {}
    
    dist = -4.0
    
    # Background Panels
    # Left Panel
    ui_elements["panel_left"] = create_ui_element("UI_Panel_Left", "", (-2.8, 0, dist), mats, cam, is_text=False, size=(1.5, 3.8))
    # Right Panel
    ui_elements["panel_right"] = create_ui_element("UI_Panel_Right", "", (2.8, 0, dist), mats, cam, is_text=False, size=(1.5, 3.8))
    # Top Panel
    ui_elements["panel_top"] = create_ui_element("UI_Panel_Top", "", (0, 1.8, dist), mats, cam, is_text=False, size=(4.0, 0.4))
    
    # Text Elements - TOP
    ui_elements["title"] = create_ui_element("UI_Title", "SAANJH DIGITAL TWIN  |  LIVE SIMULATION", (-2.0, 1.9, dist+0.01), mats, cam, scale=0.15)
    ui_elements["clock"] = create_ui_element("UI_Clock", "TIME: 16:00:00", (1.0, 1.9, dist+0.01), mats, cam, scale=0.15)
    
    # Text Elements - LEFT (NETWORK)
    ui_elements["net_title"] = create_ui_element("UI_NetTitle", "NETWORK STATUS", (-3.4, 1.7, dist+0.01), mats, cam, scale=0.12)
    ui_elements["net_feeder"] = create_ui_element("UI_NetFeeder", "FEEDER: ONLINE", (-3.4, 1.4, dist+0.01), mats, cam, scale=0.1)
    ui_elements["net_trans"] = create_ui_element("UI_NetTrans", "TRANSFORMER: NORMAL", (-3.4, 1.2, dist+0.01), mats, cam, scale=0.1)
    
    # Text Elements - LEFT (ANALYTICS)
    ui_elements["ana_title"] = create_ui_element("UI_AnaTitle", "ANALYTICS", (-3.4, 0.7, dist+0.01), mats, cam, scale=0.12)
    ui_elements["ana_load"] = create_ui_element("UI_AnaLoad", "FEEDER LOAD: 0.0 kW", (-3.4, 0.4, dist+0.01), mats, cam, scale=0.1)
    ui_elements["ana_load_pct"] = create_ui_element("UI_AnaLoadPct", "TRANSFORMER: 0%", (-3.4, 0.2, dist+0.01), mats, cam, scale=0.1)
    ui_elements["ana_flex"] = create_ui_element("UI_AnaFlex", "FLEXIBILITY: 0.0 kW", (-3.4, 0.0, dist+0.01), mats, cam, scale=0.1)
    
    # Text Elements - RIGHT (EVENT CONTROL)
    ui_elements["evt_title"] = create_ui_element("UI_EvtTitle", "ACTIVE EVENT", (2.2, 1.7, dist+0.01), mats, cam, scale=0.12)
    ui_elements["evt_status"] = create_ui_element("UI_EvtStatus", "STATUS: NORMAL", (2.2, 1.4, dist+0.01), mats, cam, scale=0.1)
    ui_elements["evt_homes"] = create_ui_element("UI_EvtHomes", "ACTIVE HOMES: 0 / 60", (2.2, 1.2, dist+0.01), mats, cam, scale=0.1)
    
    return ui_elements
