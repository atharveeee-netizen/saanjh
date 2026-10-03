import numpy as np
import pandas as pd
import json
import matplotlib.pyplot as plt
import os

# Add parent directory to path so imports work correctly when running this file directly
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation.config import NUM_HOMES, HOMES_WITH_INVERTER_BATTERY, HOMES_WITH_SOLAR
from simulation.models.household import Household
from simulation.models.transformer import Transformer
from simulation.models.solar import SolarPanel
from simulation.virtual_battery.aggregator import VirtualBatteryAggregator
from simulation.economics_engine import calculate_economics
import joblib

class RealWorldForecastEngine:
    def __init__(self, model_path, num_homes):
        self.model = joblib.load(model_path)
        self.num_homes = num_homes
        self.history = []
        
    def predict_next_step(self, current_total_load_kw, current_hour):
        # Explicit Scaling Layer: The XGBoost model was trained on a SINGLE household (UCI dataset).
        # We must scale the 60-home aggregate load down to a per-household basis to match the model's domain,
        # then scale the prediction back up.
        per_home_load = current_total_load_kw / self.num_homes
        self.history.append(per_home_load)
        
        # Approximate lags (assuming 15-min model steps vs 5-min sim steps)
        lag_1 = self.history[-3] if len(self.history) >= 3 else per_home_load
        lag_4 = self.history[-12] if len(self.history) >= 12 else per_home_load
        lag_96 = self.history[-288] if len(self.history) >= 288 else per_home_load
        roll_mean_4 = sum(self.history[-12:]) / len(self.history[-12:]) if len(self.history) > 0 else per_home_load
        
        # Construct feature vector expected by the real-trained XGBoost model
        import pandas as pd
        features = pd.DataFrame({
            'hour': [int(current_hour)],
            'day_of_week': [3], # Wed
            'month': [10],      # Oct
            'is_weekend': [0],
            'load_kw': [per_home_load],
            'load_lag_1': [lag_1],
            'load_lag_4': [lag_4],
            'load_lag_96': [lag_96],
            'load_roll_mean_4': [roll_mean_4]
        })
        
        predicted_per_home = self.model.predict(features)[0]
        
        # Scale back up to feeder level
        predicted_feeder_load = predicted_per_home * self.num_homes
        return predicted_feeder_load

def run_simulation(use_saanjh=False, seed=42):
    np.random.seed(seed) # For reproducibility
    
    # Initialize components
    households = []
    battery_indices = np.random.choice(NUM_HOMES, HOMES_WITH_INVERTER_BATTERY, replace=False)
    solar_indices = np.random.choice(NUM_HOMES, HOMES_WITH_SOLAR, replace=False)
    
    for i in range(NUM_HOMES):
        has_battery = i in battery_indices
        has_solar = i in solar_indices
        households.append(Household(i, has_battery, has_solar))
        
    transformer = Transformer()
    
    aggregator = VirtualBatteryAggregator(time_res_minutes=5)
    aggregator.register_households(households)
    
    # Initialize Real-World Forecast Engine
    base_dir = os.path.dirname(os.path.dirname(__file__))
    model_path = os.path.join(base_dir, 'artifacts', 'models', 'real_xgboost_model.pkl')
    forecast_engine = RealWorldForecastEngine(model_path, NUM_HOMES) if use_saanjh else None
    
    
    # Simulation loop (16:00 to 22:00, 5 minute intervals)
    start_time = 16.0
    end_time = 22.0
    dt_min = 5
    dt_hour = dt_min / 60.0
    
    times = []
    total_loads = []
    voltages = []
    transformer_loadings = []
    flexibility_delivered = []
    homes_dispatched_history = []
    
    for t in np.arange(start_time, end_time, dt_hour):
        times.append(t)
        
        # Calculate base load
        total_load_w = 0
        available_flex_w = 0
        
        for h in households:
            # Base + Deferrable
            h_load = h.get_base_load(t) 
            if not h.is_dispatched:
                h_load += h.get_deferrable_load(t)
                
            # Solar offset
            if h.has_solar:
                h_load = max(0, h_load - SolarPanel.get_generation(t))
                
            total_load_w += h_load
            
            # If dispatched, subtract the battery's active output
            if h.is_dispatched:
                total_load_w -= (h.current_dispatch_kw * 1000)
                
            total_load_w = max(0, total_load_w)
            
            available_flex_w += (h.get_available_flexibility() * 1000)
            
            # Step the household state
            h.step(dt_min)
            
        total_load_kw = total_load_w / 1000.0
        
        # Dispatch logic
        dispatched_kw = 0
        active_homes = sum(1 for h in households if h.is_dispatched)
        
        if use_saanjh:
            # Forecast using the real-data trained XGBoost model
            forecast_load_kw = forecast_engine.predict_next_step(total_load_kw, t)
            target_limit_kw = transformer.rating_kva * 0.95 * 0.85
            req_flex = max(0, forecast_load_kw - target_limit_kw)
            
            if req_flex > 0:
                dispatched_kw = aggregator.dispatch(req_flex)
                active_homes += sum(1 for h in households if h.current_dispatch_kw > 0)
                
        # Record metrics
        total_loads.append(total_load_kw)
        transformer_loadings.append(transformer.get_loading_percent(total_load_kw))
        flexibility_delivered.append(sum(h.get_available_flexibility() for h in households if h.is_dispatched) / 1000.0) # Approx delivered
        homes_dispatched_history.append(active_homes)
        
        # Voltage heuristic (drops as load increases)
        voltages.append(240 - (total_load_kw / 5)) 

    # Compile results
    df = pd.DataFrame({
        'Time': times,
        'Load_kW': total_loads,
        'Transformer_Loading_%': transformer_loadings,
        'Voltage_V': voltages,
        'Flexibility_Delivered_kW': flexibility_delivered,
        'Active_Homes': homes_dispatched_history
    })
    
    return df, households

def generate_results():
    # Set paths relative to script location
    base_dir = os.path.dirname(os.path.dirname(__file__))
    results_dir = os.path.join(base_dir, 'simulation', 'data', 'results')
    plots_dir = os.path.join(base_dir, 'simulation', 'plots')
    
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)
    
    baseline_df, _ = run_simulation(use_saanjh=False, seed=42)
    saanjh_df, saanjh_households = run_simulation(use_saanjh=True, seed=42)
    
    baseline_df.to_csv(os.path.join(results_dir, 'baseline_profile.csv'), index=False)
    saanjh_df.to_csv(os.path.join(results_dir, 'saanjh_profile.csv'), index=False)
    
    # Calculate KPIs
    baseline_peak_kw = baseline_df['Load_kW'].max()
    saanjh_peak_kw = saanjh_df['Load_kW'].max()
    peak_reduction_kw = baseline_peak_kw - saanjh_peak_kw
    peak_reduction_pct = (peak_reduction_kw / baseline_peak_kw) * 100 if baseline_peak_kw > 0 else 0
    
    baseline_overload_mins = (baseline_df['Transformer_Loading_%'] > 100).sum() * 5
    saanjh_overload_mins = (saanjh_df['Transformer_Loading_%'] > 100).sum() * 5
    
    flexibility_delivered_kw = saanjh_df['Flexibility_Delivered_kW'].max()
    
    voltage_violations_baseline = (baseline_df['Voltage_V'] < 210).sum()
    voltage_violations_saanjh = (saanjh_df['Voltage_V'] < 210).sum()
    
    homes_participating = sum(1 for h in saanjh_households if h.participation_count > 0)
    
    economics = calculate_economics(peak_reduction_kw, homes_participating)
    
    kpis = {
        "baseline_peak_kw": float(baseline_peak_kw),
        "saanjh_peak_kw": float(saanjh_peak_kw),
        "peak_reduction_kw": float(peak_reduction_kw),
        "peak_reduction_pct": float(peak_reduction_pct),
        "baseline_overload_minutes": int(baseline_overload_mins),
        "saanjh_overload_minutes": int(saanjh_overload_mins),
        "flexibility_delivered_kw": float(flexibility_delivered_kw),
        "dependable_flexibility_ratio": float((homes_participating / NUM_HOMES) if NUM_HOMES > 0 else 0),
        "voltage_violations_baseline": int(voltage_violations_baseline),
        "voltage_violations_saanjh": int(voltage_violations_saanjh),
        "homes_participating": int(homes_participating),
        "cost_per_dependable_kw": economics["cost_per_dependable_kw"],
        "total_initial_investment": economics["total_initial_investment"]
    }
    
    with open(os.path.join(results_dir, 'comparison.json'), 'w') as f:
        json.dump(kpis, f, indent=4)
        
    # Generate Plots
    plt.figure(figsize=(10, 6))
    plt.plot(baseline_df['Time'], baseline_df['Load_kW'], 'r--', label='Baseline Load')
    plt.plot(saanjh_df['Time'], saanjh_df['Load_kW'], 'g-', label='SAANJH Load')
    plt.fill_between(saanjh_df['Time'], saanjh_df['Load_kW'], baseline_df['Load_kW'], color='green', alpha=0.2, label='Flexibility Delivered')
    plt.axhline(y=100*0.95, color='orange', linestyle=':', label='Transformer 100% Rating')
    plt.title('Evening Peak Load: Baseline vs SAANJH')
    plt.xlabel('Time (Hour of Day)')
    plt.ylabel('Feeder Load (kW)')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(plots_dir, 'load_comparison.png'))
    print("Simulation Complete. Results saved in simulation/data/results and simulation/plots.")
    
if __name__ == "__main__":
    generate_results()
