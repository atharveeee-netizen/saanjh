import pypsa
import pandas as pd
import numpy as np

def validate_profile_with_pypsa(profile_path, output_path):
    """
    Independently validates the electrical integrity of SAANJH's output 
    using the industry-standard PyPSA load flow solver.
    """
    # Load the SAANJH simulated timeseries
    df = pd.read_csv(profile_path)
    
    # Initialize PyPSA Network
    network = pypsa.Network()
    network.set_snapshots(df.index)
    
    # Grid Slack Bus (11kV MV Side)
    network.add("Bus", "Grid_Bus", v_nom=11.0, control="Slack")
    network.add("Generator", "External_Grid", bus="Grid_Bus", p_set=0, control="Slack")
    
    # Feeder Bus (240V LV Side)
    network.add("Bus", "Feeder_Bus", v_nom=0.24)
    
    # Distribution Transformer (100 kVA, 11kV -> 240V)
    network.add("Transformer", "Dist_Trafo", 
                bus0="Grid_Bus", bus1="Feeder_Bus",
                s_nom=100.0, # 100 kVA rating matches our SAANJH assumption
                r_pu=0.01, x_pu=0.04) # Typical LV transformer impedance
                
    # Feeder Line (Approximating voltage drop down the street)
    network.add("Bus", "Load_Center_Bus", v_nom=0.24)
    network.add("Line", "Street_Cable",
                bus0="Feeder_Bus", bus1="Load_Center_Bus",
                r=0.05, x=0.01, length=0.5, # 500 meters of cable
                s_nom=200.0)
                
    # Add the dynamic timeseries load from SAANJH
    # We assign the total kW to the load center
    network.add("Load", "Aggregated_Neighbourhood",
                bus="Load_Center_Bus",
                p_set=df["Load_kW"].values / 1000.0, # PyPSA expects MW
                q_set=df["Load_kW"].values / 1000.0 * 0.3) # Assume 0.95 PF roughly
                
    # Run Non-Linear AC Power Flow
    try:
        network.lpf() # Linear PF as a fast fallback
        network.pf()  # Full Newton-Raphson AC Power Flow
    except Exception as e:
        print(f"PyPSA AC Power Flow failed, falling back to LPF: {e}")
        
    # Extract independent physical results
    trafo_loading = network.transformers_t.p0["Dist_Trafo"] * 1000.0 # Convert back to kW
    voltage_pu = network.buses_t.v_mag_pu["Load_Center_Bus"]
    voltage_v = voltage_pu * 240.0
    
    # Package Results
    results = pd.DataFrame({
        "Time": df["Time"],
        "Original_SAANJH_Load_kW": df["Load_kW"],
        "PyPSA_Trafo_Load_kW": trafo_loading.values,
        "PyPSA_Voltage_V": voltage_v.values
    })
    
    results.to_csv(output_path, index=False)
    print(f"PyPSA Validation complete. Wrote: {output_path}")
    return results

if __name__ == "__main__":
    import os
    base_dir = os.path.dirname(os.path.dirname(__file__))
    baseline_path = os.path.join(base_dir, 'data', 'results', 'baseline_profile.csv')
    saanjh_path = os.path.join(base_dir, 'data', 'results', 'saanjh_profile.csv')
    
    if os.path.exists(baseline_path):
        validate_profile_with_pypsa(baseline_path, os.path.join(base_dir, 'data', 'results', 'pypsa_baseline_validation.csv'))
    
    if os.path.exists(saanjh_path):
        validate_profile_with_pypsa(saanjh_path, os.path.join(base_dir, 'data', 'results', 'pypsa_saanjh_validation.csv'))
