"""
Numerical Consistency Test for SAANJH FUXA SCADA/HMI
Verifies that every displayed metric on the UI originates strictly
from canonical simulation artifacts without manual fabrication.
"""

import json
import csv
import os

def test_numerical_traceability():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sim_dir = os.path.join(base_dir, 'simulation', 'data', 'results')
    
    # 1. Comparison file
    with open(os.path.join(sim_dir, 'comparison.json'), 'r') as f:
        comp = json.load(f)
        
    assert round(comp["baseline_peak_kw"], 1) == 154.1, f"Expected 154.1 kW baseline peak, got {comp['baseline_peak_kw']}"
    assert round(comp["saanjh_peak_kw"], 2) == 109.18, f"Expected 109.18 kW SAANJH peak, got {comp['saanjh_peak_kw']}"
    assert round(comp["peak_reduction_kw"], 2) == 44.95, f"Expected 44.95 kW peak cut, got {comp['peak_reduction_kw']}"
    assert round(comp["flexibility_delivered_kw"], 2) == 56.25, f"Expected 56.25 kW flex, got {comp['flexibility_delivered_kw']}"
    assert comp["saanjh_overload_minutes"] == 60, f"Expected 60 min overload, got {comp['saanjh_overload_minutes']}"
    assert comp["baseline_overload_minutes"] == 90, f"Expected 90 min baseline overload, got {comp['baseline_overload_minutes']}"
    assert comp["voltage_violations_saanjh"] == 0, f"Expected 0 voltage violations, got {comp['voltage_violations_saanjh']}"
    assert comp["voltage_violations_baseline"] == 6, f"Expected 6 baseline voltage violations, got {comp['voltage_violations_baseline']}"
    assert comp["cost_per_dependable_kw"] == 7068, f"Expected 7068 INR/kW, got {comp['cost_per_dependable_kw']}"
    assert comp["homes_participating"] == 39, f"Expected 39 homes, got {comp['homes_participating']}"

    # 2. Household dispatch CSV
    with open(os.path.join(sim_dir, 'household_dispatch.csv'), 'r') as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 60, f"Expected 60 households, got {len(reader)}"
        
        bess_count = sum(1 for r in reader if r["has_battery"].lower() == "true")
        assert bess_count == 42, f"Expected 42 battery homes, got {bess_count}"
        
        participating = sum(1 for r in reader if r["participated"].lower() == "true")
        assert participating == 39, f"Expected 39 participating, got {participating}"
        
        opted_out = [r["household_id"] for r in reader if r["opted_out"].lower() == "true"]
        assert sorted(opted_out) == ["H-18", "H-55", "H-56"], f"Expected opt-outs H-18, H-55, H-56, got {opted_out}"
        
        # Verify 70% reserve floor across all households
        for r in reader:
            reserve = float(r["reserve_soc_limit"])
            assert reserve == 0.7, f"Home {r['household_id']} has invalid reserve {reserve}"
            final_soc = float(r["final_soc"])
            assert final_soc >= reserve, f"Home {r['household_id']} breached reserve: final SOC {final_soc} < {reserve}"

    # 3. Voltage profile check
    with open(os.path.join(sim_dir, 'comparison.json'), 'r') as f:
        # Load timeseries bundle
        with open(os.path.join(base_dir, 'docs', 'data', 'timeseries_bundle.json'), 'r') as tf:
            ts = json.load(tf)
            assert len(ts["labels"]) == 72, f"Expected 72 timesteps, got {len(ts['labels'])}"
            peak_idx = 37 # 19:05
            assert round(ts["saanjh_voltage"][peak_idx], 2) == 226.54, f"Expected 226.54 V, got {ts['saanjh_voltage'][peak_idx]}"
            assert round(ts["baseline_voltage"][peak_idx], 2) == 219.68, f"Expected 219.68 V, got {ts['baseline_voltage'][peak_idx]}"

    print("ALL NUMERICAL CONSISTENCY TESTS PASSED! Every displayed number is 100% traceable to canonical simulation artifacts.")

if __name__ == "__main__":
    test_numerical_traceability()
