import os
import sys
import json
import numpy as np
import pandas as pd

base_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(base_dir)

from simulation.feeder_sim import run_simulation
from simulation.config import NUM_HOMES

def run_monte_carlo(iterations=10):
    print(f"--- Running Monte Carlo Robustness Tests ({iterations} Iterations) ---")
    
    results_dir = os.path.join(base_dir, 'simulation', 'data', 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    peak_reductions_kw = []
    overload_mins = []
    
    for i in range(iterations):
        # We simulate randomness by implicitly letting np.random handle the distribution of solar/battery
        # inside the Household initialization (if we re-initialize it).
        # We need to change the global seed per iteration.
        np.random.seed(i)
        
        # Run baseline
        baseline_df, _ = run_simulation(use_saanjh=False, seed=i)
        baseline_peak = baseline_df['Load_kW'].max()
        
        # Run SAANJH
        saanjh_df, _ = run_simulation(use_saanjh=True, seed=i)
        saanjh_peak = saanjh_df['Load_kW'].max()
        
        peak_reductions_kw.append(baseline_peak - saanjh_peak)
        
        overload = (saanjh_df['Transformer_Loading_%'] > 100).sum() * 5
        overload_mins.append(overload)
        
        print(f"Iteration {i}: Peak Reduction = {baseline_peak - saanjh_peak:.2f} kW, Overload = {overload} mins")
        
    # Aggregate Metrics
    summary = {
        "mean_peak_reduction_kw": np.mean(peak_reductions_kw),
        "median_peak_reduction_kw": np.median(peak_reductions_kw),
        "min_peak_reduction_kw": np.min(peak_reductions_kw),
        "max_peak_reduction_kw": np.max(peak_reductions_kw),
        "P10_peak_reduction": np.percentile(peak_reductions_kw, 10),
        "P90_peak_reduction": np.percentile(peak_reductions_kw, 90),
        "mean_overload_mins": np.mean(overload_mins)
    }
    
    with open(os.path.join(results_dir, 'monte_carlo_summary.json'), 'w') as f:
        json.dump(summary, f, indent=4)
        
    print("\n[SUCCESS] Monte Carlo testing complete. Summary saved.")
    
if __name__ == "__main__":
    run_monte_carlo(iterations=5)
