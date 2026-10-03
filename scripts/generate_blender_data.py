import os
import json
import pandas as pd

def generate_blender_data():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    results_dir = os.path.join(base_dir, 'simulation', 'data', 'results')
    blender_dir = os.path.join(base_dir, 'artifacts', 'blender')
    
    os.makedirs(blender_dir, exist_ok=True)
    
    saanjh_csv_path = os.path.join(results_dir, 'saanjh_profile.csv')
    if not os.path.exists(saanjh_csv_path):
        print("Error: saanjh_profile.csv not found.")
        return
        
    df = pd.read_csv(saanjh_csv_path)
    
    # We will construct a frame-by-frame (or timestep-by-timestep) animation data structure
    frames = []
    
    for idx, row in df.iterrows():
        # Transformer loading logic
        loading = row['Transformer_Loading_%']
        stress = min(1.0, max(0.0, (loading - 85.0) / 30.0)) if loading > 85.0 else 0.0
        
        frame_data = {
            "time_idx": int(idx),
            "hour": float(row['Time']),
            "feeder_load_kw": float(row['Load_kW']),
            "transformer_loading_pct": float(loading),
            "transformer_stress": float(stress),
            "active_homes": int(row['Active_Homes']),
            "flexibility_delivered_kw": float(row['Flexibility_Delivered_kW'])
        }
        frames.append(frame_data)
        
    # Build the final contract
    data_contract = {
        "metadata": {
            "num_homes": 60, # Inferred from simulation config
            "fps": 30,
            "seconds_per_timestep": 1.0 # 1 simulation step = 1 second in blender, so 72 seconds total
        },
        "frames": frames
    }
    
    out_path = os.path.join(blender_dir, 'saanjh_visualization_data.json')
    with open(out_path, 'w') as f:
        json.dump(data_contract, f, indent=4)
        
    print(f"Generated Blender data contract at: {out_path}")

if __name__ == "__main__":
    generate_blender_data()
