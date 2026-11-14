"""Reliability scorecard across Monte Carlo seeds, with and without SAANJH.

    python simulation/reliability.py --seeds 5

Writes ``simulation/results/reliability.json``. This is the source for the README
scorecard and the dashboard reliability panel. Inputs are the same engine runs used by
``simulation/run_year.py``; this module adds the standard indices (SAIDI, SAIFI, CAIDI,
ASAI, brownout hours, unserved energy) and the 17:00-19:00 window.
"""
import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.config import repo_path
from simulation.engine import Scenario, run
from simulation.metrics import reliability_metrics, run_metrics

RESULTS = repo_path("simulation", "results")
SCENARIOS = ["peri_urban_low_income", "mixed_urban"]

SCORECARD = [
    ("essential_supply_availability_pct", "Essential supply available in shortfall windows", "%"),
    ("saidi_hours_per_home", "SAIDI-style outage hours per home", "h"),
    ("saifi_interruptions_per_home", "SAIFI-style interruptions per home", "n"),
    ("brownout_hours_per_home", "Brownout hours per home (on essential band)", "h"),
    ("unserved_energy_kwh", "Unserved energy", "kWh"),
    ("energy_not_delivered_kwh", "Energy not delivered (unserved + above-band)", "kWh"),
    ("window_supply_availability_pct", "Any supply available, 17:00-19:00", "%"),
    ("window_essential_availability_pct", "Essential supply available, 17:00-19:00", "%"),
    ("window_deficit_essential_availability_pct", "Essential supply available, 17:00-19:00 shortfall blocks", "%"),
    ("dt_peak_loading_pct", "DT peak loading", "%"),
    ("dt_overload_hours", "DT overload hours", "h"),
]


def _one(args):
    name, seed, policy = args
    sc = Scenario(name, seed)
    r = run(sc, policy)
    rel = reliability_metrics(r)
    ops = run_metrics(r)
    rel["essential_supply_availability_pct"] = (
        ops["essential_supply_availability"] * 100 if ops["essential_supply_availability"] is not None else None)
    rel["dt_peak_loading_pct"] = ops["dt_peak_loading_pct"]
    rel["dt_overload_hours"] = ops["dt_overload_hours"]
    return {"scenario": name, "seed": seed, "policy": policy, "metrics": rel,
            "flexibility": ops.get("flexibility"), "ledger": {"community_battery": ops.get("community_battery")}}


def _summarise(values):
    v = np.array([x for x in values if x is not None], dtype=float)
    if not len(v):
        return None
    return {"mean": float(v.mean()), "p10": float(np.percentile(v, 10)),
            "p90": float(np.percentile(v, 90)), "n": int(len(v))}


def build(seeds=5, workers=None):
    workers = workers or max(1, min(8, (os.cpu_count() or 2) - 2))
    tasks = [(name, seed, pol) for name in SCENARIOS for seed in range(seeds)
             for pol in ("baseline", "saanjh")]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        rows = list(ex.map(_one, tasks, chunksize=1))

    out = {
        "label": "SIMULATED on inputs CALIBRATED TO REAL DATA (see docs/DATA_SOURCES.md)",
        "seeds": seeds,
        "window": "17:00-19:00",
        "scenarios": {},
    }
    for name in SCENARIOS:
        block = {"policies": {}, "by_seed": {}}
        for pol in ("baseline", "saanjh"):
            ms = [r["metrics"] for r in rows if r["scenario"] == name and r["policy"] == pol]
            block["policies"][pol] = {
                key: _summarise([m.get(key) for m in ms]) for key, _, _ in SCORECARD
            }
            block["by_seed"][pol] = {
                str(r["seed"]): r["metrics"] for r in rows
                if r["scenario"] == name and r["policy"] == pol
            }
        # Paired improvement per seed (same weather and shortfall draws).
        common = sorted(set(block["by_seed"]["baseline"]) & set(block["by_seed"]["saanjh"]), key=int)
        block["delta"] = {
            "unserved_energy_kwh": _summarise([
                block["by_seed"]["baseline"][s]["unserved_energy_kwh"]
                - block["by_seed"]["saanjh"][s]["unserved_energy_kwh"] for s in common]),
            "saidi_hours_per_home": _summarise([
                block["by_seed"]["baseline"][s]["saidi_hours_per_home"]
                - block["by_seed"]["saanjh"][s]["saidi_hours_per_home"] for s in common]),
            "brownout_hours_per_home": _summarise([
                block["by_seed"]["baseline"][s]["brownout_hours_per_home"]
                - block["by_seed"]["saanjh"][s]["brownout_hours_per_home"] for s in common]),
            "window_essential_availability_pct": _summarise([
                block["by_seed"]["saanjh"][s]["window_essential_availability_pct"]
                - block["by_seed"]["baseline"][s]["window_essential_availability_pct"] for s in common]),
        }
        block["scorecard"] = [
            {"key": k, "label": lab, "unit": unit,
             "baseline": block["policies"]["baseline"].get(k),
             "saanjh": block["policies"]["saanjh"].get(k)}
            for k, lab, unit in SCORECARD
        ]
        out["scenarios"][name] = block

    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.join(RESULTS, "reliability.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, allow_nan=False)
    return out, path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args(argv)
    out, path = build(a.seeds, a.workers)
    for name, block in out["scenarios"].items():
        print(f"\n{name}")
        for row in block["scorecard"]:
            b, s = row["baseline"], row["saanjh"]
            if not b or not s:
                continue
            print(f"  {row['label']:58s} {b['mean']:9.2f} -> {s['mean']:9.2f} {row['unit']}")
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()
