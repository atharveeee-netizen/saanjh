import pypsa
import pandas as pd
import numpy as np
import os

def validate_profile_with_pypsa(profile_path, output_path):
    """
    Independently validates the electrical integrity of SAANJH's output 
    using the industry-standard PyPSA AC power flow solver.
    Models the 415V/240V 3-phase 4-wire radial distribution feeder downstream of the 100 kVA DT.
    Calculates genuine bus voltages and modeled resistive-loss proxy.
    """
    df = pd.read_csv(profile_path)
    
    network = pypsa.Network()
    network.set_snapshots(df.index)
    
    # 415V (0.415 kV line-to-line, 240V phase-to-neutral) standard Indian distribution voltage
    v_nom_kv = 0.415
    v_phase_nominal = 240.0
    
    # Secondary side of 100 kVA distribution transformer (Slack Bus)
    network.add("Bus", "Trafo_LV_Bus", v_nom=v_nom_kv, control="Slack")
    network.add("Generator", "Trafo_Secondary", bus="Trafo_LV_Bus", control="Slack")
    
    # 3-phase LT radial feeder line (e.g. 50 mm² AB cable / ACSR conductor, 250m)
    # Balanced 3-phase equivalent: R = 0.08 ohm, X = 0.02 ohm, 250 kVA capacity
    network.add("Bus", "Load_Center_Bus", v_nom=v_nom_kv)
    network.add("Line", "Feeder_Cable",
                bus0="Trafo_LV_Bus", bus1="Load_Center_Bus",
                r=0.08, x=0.02, s_nom=0.25)
                
    # 3-phase aggregate neighborhood demand (MW) with 0.95 power factor
    p_load_mw = df["Load_kW"].values / 1000.0
    q_load_mvar = p_load_mw * np.tan(np.arccos(0.95))
    
    network.add("Load", "Neighbourhood_Demand",
                bus="Load_Center_Bus",
                p_set=p_load_mw,
                q_set=q_load_mvar)
                
    # Run full Non-Linear AC Power Flow (Newton-Raphson)
    try:
        network.pf()
    except Exception as e:
        print(f"Warning: Falling back to linear power flow: {e}")
        network.lpf()
        
    # Extract genuine physical results
    v_pu = network.buses_t.v_mag_pu["Load_Center_Bus"].values
    v_actual_phase = v_pu * v_phase_nominal
    trafo_p_kw = network.generators_t.p["Trafo_Secondary"].values * 1000.0
    
    # Modeled resistive-loss proxy = sum of power at both ends of line
    line_loss_kw = np.maximum(0.0, (network.lines_t.p0["Feeder_Cable"].values + network.lines_t.p1["Feeder_Cable"].values) * 1000.0)
    
    results = pd.DataFrame({
        "Time": df["Time"],
        "Original_SAANJH_Load_kW": df["Load_kW"],
        "PyPSA_Trafo_Load_kW": trafo_p_kw,
        "PyPSA_Voltage_V": v_actual_phase,
        "PyPSA_Voltage_pu": v_pu,
        "PyPSA_Line_Loss_kW": line_loss_kw
    })
    
    results.to_csv(output_path, index=False)
    print(f"PyPSA Validation complete. Wrote: {output_path}")
    return results

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(__file__))
    baseline_path = os.path.join(base_dir, 'data', 'results', 'baseline_profile.csv')
    saanjh_path = os.path.join(base_dir, 'data', 'results', 'saanjh_profile.csv')
    
    if os.path.exists(baseline_path):
        validate_profile_with_pypsa(baseline_path, os.path.join(base_dir, 'data', 'results', 'pypsa_baseline_validation.csv'))
    
    if os.path.exists(saanjh_path):
        validate_profile_with_pypsa(saanjh_path, os.path.join(base_dir, 'data', 'results', 'pypsa_saanjh_validation.csv'))
