"""Year-long, scenario-based evaluation: BASELINE vs SAANJH with Monte Carlo seeds.

    python simulation/run_year.py                 # 30 seeds, sensitivity with 10 seeds
    python simulation/run_year.py --seeds 5 --sens-seeds 3 --quick

Outputs (single source of truth for docs and UI):
    simulation/results/results.json   sections "annual" and "sensitivity"
    simulation/results/montecarlo.csv one row per scenario x policy x seed
    simulation/results/annual/        seed-0 per-home tables, monthly outages, event log
    simulation/results/timeseries/    seed-0 per-block series (large, not committed)
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.config import load_config, repo_path
from simulation.engine import Scenario, run
from simulation.metrics import run_metrics

RESULTS = repo_path("simulation", "results")
SCENARIOS = ["peri_urban_low_income", "mixed_urban"]
HEADLINE = [
    ("essential_supply_availability", "Essential-supply availability in deficit windows", "%"),
    ("outage_hours_per_home", "Outage hours per home per year (full disconnection)", "h"),
    ("outage_hours_in_deficit_per_home", "…of which in deficit windows", "h"),
    ("banded_hours_per_home", "Hours on essential band per home per year", "h"),
    ("energy_not_served_kwh", "Energy not served (kWh/year)", "kWh"),
    ("energy_curtailed_above_band_kwh", "Energy curtailed above the band (kWh/year)", "kWh"),
    ("dt_overload_hours", "DT overload hours per year", "h"),
    ("dt_peak_loading_pct", "DT peak loading", "%"),
]


def sensitivity_variants(name):
    alt_mix = {"peri_urban_low_income": {"low_income": 0.5, "middle": 0.4, "affluent": 0.1},
               "mixed_urban": {"low_income": 0.2, "middle": 0.5, "affluent": 0.3}}[name]
    ladder = [1000, 750, 500, 300]
    return {
        "essential_band_w": [
            (300, {"essential_band": {"band_w": 300, "ladder_w": ladder}}, None),
            (500, {}, None),
            (1000, {"essential_band": {"band_w": 1000, "ladder_w": ladder}}, None),
        ],
        "community_battery_kwh": [
            (0, {}, {"capacity_kwh": 0, "power_kw": 0}),
            (50, {}, {"capacity_kwh": 50, "power_kw": 20}),
            (100, {}, None),
            (200, {}, {"capacity_kwh": 200, "power_kw": 80}),
        ],
        "inverter_relay_participation": [
            (0.0, {"participation": {"inverter_relay": 0.0}}, None),
            (0.6, {}, None),
            (1.0, {"participation": {"inverter_relay": 1.0}}, None),
        ],
        "segment_mix": [
            ("base", {}, None),
            ("more affluent", {"scenarios": {name: {"segment_mix": alt_mix}}}, None),
        ],
        "deficit_share": [
            (0.3, {"outage_calibration": {"deficit_share": 0.3}}, None),
            (0.5, {}, None),
            (0.7, {"outage_calibration": {"deficit_share": 0.7}}, None),
        ],
        "shortfall_depth": [
            ("15-45%", {}, None),
            ("25-60%", {"dispatch": {"shortfall_depth": [0.25, 0.60]}}, None),
        ],
    }


def _task(args):
    name, seed, policy, overrides, cb_override, keep = args
    sc = Scenario(name, seed, overrides=overrides)
    r = run(sc, policy, cb_override=cb_override, record_days=None if keep else [])
    m = run_metrics(r)
    out = {"scenario": name, "seed": seed, "policy": policy, "metrics": m}
    if keep:
        _save_seed0(sc, r)
    return out


def _save_seed0(sc, r):
    ann = os.path.join(RESULTS, "annual")
    ts = os.path.join(RESULTS, "timeseries")
    os.makedirs(ann, exist_ok=True)
    os.makedirs(ts, exist_ok=True)
    r.homes.to_csv(os.path.join(ann, f"{sc.name}_{r.policy}_homes.csv"), index=False)
    r.timeseries.to_csv(os.path.join(ts, f"{sc.name}_{r.policy}.csv"), index=False)
    t = r.timeseries
    t["month"] = pd.to_datetime(t["date"]).dt.month
    monthly = t.groupby("month").agg(
        outage_home_hours=("homes_shed", lambda s: s.sum() * sc.step_h),
        banded_home_hours=("homes_banded", lambda s: s.sum() * sc.step_h),
        deficit_hours=("unmanaged_gap_kw", lambda s: (s > 0).sum() * sc.step_h),
        unserved_kwh=("unserved_kw", lambda s: s.sum() * sc.step_h),
    ).reset_index()
    monthly["outage_hours_per_home"] = monthly["outage_home_hours"] / sc.fleet.n
    monthly.to_csv(os.path.join(ann, f"{sc.name}_{r.policy}_monthly.csv"), index=False)
    if r.policy == "saanjh":
        with open(os.path.join(ann, f"{sc.name}_events.json"), "w", encoding="utf-8") as f:
            json.dump(r.log, f, indent=1, default=float)


def summarise(values):
    v = np.array([x for x in values if x is not None], dtype=float)
    if not len(v):
        return None
    return {"mean": float(v.mean()), "p10": float(np.percentile(v, 10)), "p90": float(np.percentile(v, 90))}


def aggregate(rows, name):
    out = {}
    for policy in ("baseline", "saanjh"):
        ms = [r["metrics"] for r in rows if r["scenario"] == name and r["policy"] == policy]
        if not ms:
            continue
        agg = {k: summarise([m[k] for m in ms]) for k, _, _ in HEADLINE}
        agg["fairness_outage_gini"] = summarise([m["fairness_outage_hours"]["gini"] for m in ms])
        agg["fairness_curtailment_gini"] = summarise([m["fairness_total_curtailment_hours"]["gini"] for m in ms])
        agg["share_of_homes_with_outage"] = summarise([m["fairness_outage_hours"]["share_of_homes_affected"] for m in ms])
        agg["essential_household_hours"] = summarise([m["essential_household_hours"] for m in ms])
        agg["by_segment"] = {
            seg: {k: summarise([m["by_segment"][seg][k] for m in ms if seg in m["by_segment"]])
                  for k in ("essential_supply_availability", "outage_hours_per_home", "banded_hours_per_home")}
            for seg in ms[0]["by_segment"]
        }
        if policy == "saanjh":
            agg["flexibility"] = {k: summarise([m["flexibility"][k] for m in ms]) for k in ms[0]["flexibility"]}
            agg["household_battery_cycles_added_per_year"] = summarise(
                [m["household_battery_cycles_added_per_year"] for m in ms])
            if "community_battery" in ms[0]:
                agg["community_battery"] = {k: summarise([m["community_battery"][k] for m in ms])
                                            for k in ms[0]["community_battery"]}
        out[policy] = agg
    by_seed = {pol: {r["seed"]: r["metrics"] for r in rows if r["scenario"] == name and r["policy"] == pol}
               for pol in ("baseline", "saanjh")}
    seeds = sorted(set(by_seed["baseline"]) & set(by_seed["saanjh"]))
    out["essential_household_hours_preserved"] = summarise(
        [by_seed["saanjh"][s]["essential_household_hours"] - by_seed["baseline"][s]["essential_household_hours"]
         for s in seeds])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--sens-seeds", type=int, default=10)
    ap.add_argument("--workers", type=int, default=max(1, min(30, (os.cpu_count() or 2) - 2)))
    ap.add_argument("--no-sensitivity", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.time()
    cfg = load_config()

    # Calibrate every variant in this process first so workers only read the cache.
    variants = {name: sensitivity_variants(name) for name in SCENARIOS}
    for name in SCENARIOS:
        Scenario(name, 0)
        if not a.no_sensitivity:
            for param, opts in variants[name].items():
                for _, ov, _ in opts:
                    if ov:
                        Scenario(name, 0, overrides=ov)
    print(f"Calibration done in {time.time() - t0:.0f} s")

    tasks = [(name, seed, pol, {}, None, seed == 0)
             for name in SCENARIOS for seed in range(a.seeds) for pol in ("baseline", "saanjh")]
    sens_tasks = []
    if not a.no_sensitivity:
        for name in SCENARIOS:
            for param, opts in variants[name].items():
                for value, ov, cb in opts:
                    for seed in range(a.sens_seeds):
                        for pol in ("baseline", "saanjh"):
                            sens_tasks.append(((name, param, value), (name, seed, pol, ov, cb, False)))

    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        main_rows = list(ex.map(_task, tasks, chunksize=1))
        print(f"Main runs done in {time.time() - t0:.0f} s")
        sens_rows = list(ex.map(_task, [t for _, t in sens_tasks], chunksize=1)) if sens_tasks else []
    print(f"Sensitivity runs done in {time.time() - t0:.0f} s")

    mc = pd.DataFrame([{"scenario": r["scenario"], "policy": r["policy"], "seed": r["seed"],
                        **{k: r["metrics"][k] for k, _, _ in HEADLINE}} for r in main_rows])
    mc.to_csv(os.path.join(RESULTS, "montecarlo.csv"), index=False)

    annual = {"label": "SIMULATED on inputs CALIBRATED TO REAL DATA (see docs/DATA_SOURCES.md)",
              "seeds": a.seeds, "days": 365, "site": cfg["site"], "scenarios": {}}
    for name in SCENARIOS:
        sc = cfg["scenarios"][name]
        seed0 = next(r["metrics"] for r in main_rows if r["scenario"] == name and r["policy"] == "saanjh" and r["seed"] == 0)
        cal = Scenario(name, 0).calibration
        annual["scenarios"][name] = {
            "description": " ".join(sc["description"].split()),
            "homes": sc["num_homes"], "transformer_kva": sc["transformer_kva"],
            "segment_mix": sc["segment_mix"], "esmi_category": sc["esmi_category"],
            "calibration": {k: v for k, v in cal.items() if k != "signature"},
            **aggregate(main_rows, name),
            "seed0_saanjh_fairness": seed0["fairness_outage_hours"],
        }

    sensitivity = {}
    for (key, _), r in zip(sens_tasks, sens_rows):
        name, param, value = key
        sensitivity.setdefault(name, {}).setdefault(param, {}).setdefault(str(value), []).append(r)
    sens_out = {}
    for name, params in sensitivity.items():
        sens_out[name] = {}
        for param, values in params.items():
            sens_out[name][param] = []
            for value, rs in values.items():
                row = {"value": value}
                for pol in ("baseline", "saanjh"):
                    ms = [x["metrics"] for x in rs if x["policy"] == pol]
                    row[pol] = {
                        "essential_supply_availability": summarise([m["essential_supply_availability"] for m in ms]),
                        "outage_hours_per_home": summarise([m["outage_hours_per_home"] for m in ms]),
                        "banded_hours_per_home": summarise([m["banded_hours_per_home"] for m in ms]),
                    }
                sens_out[name][param].append(row)

    path = os.path.join(RESULTS, "results.json")
    data = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    data["annual"] = annual
    if sens_out:
        data["sensitivity"] = {"seeds": a.sens_seeds, "label": "SIMULATED", "scenarios": sens_out}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print_summary(annual)
    print(f"\nWrote {path} in {time.time() - t0:.0f} s")


def fmt(x, unit):
    if x is None:
        return "–"
    if unit == "%":
        return f"{x * 100:.1f}%" if x <= 1.0001 else f"{x:.0f}%"
    return f"{x:,.1f}"


def print_summary(annual):
    for name, s in annual["scenarios"].items():
        print(f"\n{name} ({s['homes']} homes, {s['transformer_kva']} kVA) — mean of {annual['seeds']} seeds")
        print(f"{'Metric':55s} {'Baseline':>12s} {'SAANJH':>12s}")
        for k, label, unit in HEADLINE:
            b = s["baseline"][k]["mean"] if s["baseline"][k] else None
            v = s["saanjh"][k]["mean"] if s["saanjh"][k] else None
            if k == "dt_peak_loading_pct":
                print(f"{label:55s} {b:11.0f}% {v:11.0f}%")
            else:
                print(f"{label:55s} {fmt(b, unit):>12s} {fmt(v, unit):>12s}")


if __name__ == "__main__":
    main()
