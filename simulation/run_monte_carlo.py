import os
import sys
import json
import numpy as np
import pandas as pd

base_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(base_dir)

from simulation.feeder_sim import run_simulation
from simulation.config import NUM_HOMES

def run_monte_carlo(iterations=50):
    print(f"--- Running Monte Carlo Robustness Tests ({iterations} Iterations) ---")
    
    results_dir = os.path.join(base_dir, 'simulation', 'data', 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    peak_reductions_kw = []
    overload_mins = []
    failure_count = 0
    
    for i in range(iterations):
        seed = 100 + i
        baseline_df, _ = run_simulation(use_saanjh=False, seed=seed)
        baseline_peak = float(baseline_df['Load_kW'].max())
        
        saanjh_df, _ = run_simulation(use_saanjh=True, seed=seed)
        saanjh_peak = float(saanjh_df['Load_kW'].max())
        
        reduction = baseline_peak - saanjh_peak
        peak_reductions_kw.append(reduction)
        
        overload = int((saanjh_df['Transformer_Loading_%'] > 100).sum() * 5)
        overload_mins.append(overload)
        
        if reduction < 0: # If SAANJH somehow caused higher peak
            failure_count += 1
            
        if (i + 1) % 10 == 0:
            print(f"Completed {i + 1}/{iterations} iterations...")
            
    summary = {
        "evaluation_type": "50-run stochastic robustness validation",
        "iterations": iterations,
        "mean_peak_reduction_kw": round(float(np.mean(peak_reductions_kw)), 2),
        "median_peak_reduction_kw": round(float(np.median(peak_reductions_kw)), 2),
        "min_peak_reduction_kw": round(float(np.min(peak_reductions_kw)), 2),
        "max_peak_reduction_kw": round(float(np.max(peak_reductions_kw)), 2),
        "P10_peak_reduction_kw": round(float(np.percentile(peak_reductions_kw, 10)), 2),
        "P90_peak_reduction_kw": round(float(np.percentile(peak_reductions_kw, 90)), 2),
        "mean_overload_mins": round(float(np.mean(overload_mins)), 1),
        "failure_rate_pct": round(float((failure_count / iterations) * 100.0), 2)
    }
    
    with open(os.path.join(results_dir, 'monte_carlo_summary.json'), 'w') as f:
        json.dump(summary, f, indent=4)
        
    print(f"\n[SUCCESS] Monte Carlo validation complete. Mean Peak Reduction: {summary['mean_peak_reduction_kw']} kW, Failure Rate: {summary['failure_rate_pct']}%.")
    return summary

if __name__ == "__main__":
    run_monte_carlo(iterations=50)
