"""DT overload audit, adoption sweep and storage sensitivity.

    python simulation/overload.py --seeds 2

Two cases are reported:

* the legacy 60-home evening case, audited as-is (it is where the old "109 kW on a
  95 kW transformer" claim came from);
* a deliberately stressed 250-home peri-urban DT (65 kVA, i.e. 61.75 kW at 0.95 pf) so
  the overload is measurable and the minimum flexibility can be found.

The sweep varies inverter-relay adoption and community-battery size. The answer is
reported whether or not it flatters the design.
"""
import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.config import load_config, repo_path
from simulation.engine import Scenario, run
from simulation.feeder_sim import run_simulation, summarise
from simulation.metrics import reliability_metrics, run_metrics

RESULTS = repo_path("simulation", "results")
NAME = "peri_urban_low_income"
STRESS_KVA = 65
ADOPTION = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
BATTERIES = [(0, 0), (100, 40)]
BATTERY_SWEEP = [(0, 0), (25, 10), (50, 20), (75, 30), (100, 40), (150, 60)]


def _stress_overrides(participation=None):
    ov = {"scenarios": {NAME: {"transformer_kva": STRESS_KVA}}}
    if participation is not None:
        ov["participation"] = {"inverter_relay": participation}
    return ov


def _job(args):
    seed, policy, participation, cb_kwh, cb_kw = args
    ov = _stress_overrides(None if policy == "baseline" else participation)
    sc = Scenario(NAME, seed, overrides=ov)
    cb = {"capacity_kwh": cb_kwh, "power_kw": cb_kw} if policy == "saanjh" else None
    r = run(sc, policy, cb_override=cb)
    ops = run_metrics(r)
    rel = reliability_metrics(r)
    ts = r.timeseries
    peak_flex = 0.0
    if len(ts) and policy == "saanjh":
        peak_flex = float((ts["relay_kw"] + ts["appliance_reduction_kw"]
                           + ts["battery_kw"].clip(lower=0)).max())
    return {
        "seed": seed, "policy": policy, "participation": participation,
        "battery_kwh": cb_kwh, "battery_kw": cb_kw,
        "peak_loading_pct": ops["dt_peak_loading_pct"],
        "overload_hours": ops["dt_overload_hours"],
        "essential_supply_availability_pct": (
            ops["essential_supply_availability"] * 100
            if ops["essential_supply_availability"] is not None else None),
        "saidi_hours_per_home": rel["saidi_hours_per_home"],
        "unserved_energy_kwh": rel["unserved_energy_kwh"],
        "peak_flex_kw": peak_flex,
    }


def _mean(rows, key):
    v = [r[key] for r in rows if r.get(key) is not None]
    return float(np.mean(v)) if v else None


def _aggregate(rows, **key):
    rs = [r for r in rows if all(r[k] == v for k, v in key.items())]
    return {
        **key,
        "n": len(rs),
        "peak_loading_pct": _mean(rs, "peak_loading_pct"),
        "overload_hours": _mean(rs, "overload_hours"),
        "essential_supply_availability_pct": _mean(rs, "essential_supply_availability_pct"),
        "saidi_hours_per_home": _mean(rs, "saidi_hours_per_home"),
        "unserved_energy_kwh": _mean(rs, "unserved_energy_kwh"),
        "peak_flex_kw": _mean(rs, "peak_flex_kw"),
    }


def _first_where(points, predicate):
    """First point in a sweep that meets a stated criterion, or None."""
    for point in points:
        if point.get("peak_loading_pct") is None:
            continue
        if predicate(point):
            return point
    return None


def _add_deltas(points, baseline):
    """Add service deltas against the baseline so a point is readable on its own."""
    base_unserved = baseline.get("unserved_energy_kwh")
    base_essential = baseline.get("essential_supply_availability_pct")
    for point in points:
        unserved = point.get("unserved_energy_kwh")
        essential = point.get("essential_supply_availability_pct")
        point["unserved_energy_reduction_pct"] = (
            round(100.0 * (1.0 - unserved / base_unserved), 2)
            if unserved is not None and base_unserved else None)
        point["essential_availability_gain_pts"] = (
            round(essential - base_essential, 2)
            if essential is not None and base_essential is not None else None)
    return points


def _legacy_audit(seed=42):
    cfg = load_config()
    base, _, _, cfg = run_simulation("baseline", "evening_peak_legacy", seed)
    saanjh, homes, ledger, _ = run_simulation("saanjh", "evening_peak_legacy", seed, cfg=cfg)
    s = summarise(base, saanjh, homes, ledger, cfg, "evening_peak_legacy")
    return {
        "label": "SIMULATED legacy evening case (one day)",
        "seed": seed,
        "transformer_rating_kw": s["transformer_rating_kva"] * cfg["electrical"]["power_factor"],
        "dispatch_target_kw": s["dispatch_target_kw"],
        "baseline_peak_kw": s["baseline"]["peak_kw"],
        "baseline_peak_loading_pct": s["baseline"]["peak_loading_pct"],
        "baseline_overload_minutes": s["baseline"]["overload_minutes"],
        "saanjh_peak_kw": s["saanjh"]["peak_kw"],
        "saanjh_peak_loading_pct": s["saanjh"]["peak_loading_pct"],
        "saanjh_overload_minutes": s["saanjh"]["overload_minutes"],
        "note": ("The old console showed 109.18 kW / 114.9%. That number is not reproduced "
                 "by the committed simulation: the regenerated case peaks at 151.5 kW "
                 "baseline and 141.2 kW with SAANJH, both above the 95 kW target. The "
                 "legacy dashboard is retained only as an audit trail."),
    }


def build(seeds=2, workers=None):
    workers = workers or max(1, min(8, (os.cpu_count() or 2) - 2))
    tasks = [(seed, "baseline", 0.0, 0, 0) for seed in range(seeds)]
    tasks += [(seed, "saanjh", p, kwh, kw) for p in ADOPTION for kwh, kw in BATTERIES
              for seed in range(seeds)]
    tasks += [(seed, "saanjh", 0.6, kwh, kw) for kwh, kw in BATTERY_SWEEP
              if (kwh, kw) not in BATTERIES for seed in range(seeds)]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        rows = list(ex.map(_job, tasks, chunksize=1))

    baseline = _aggregate(rows, policy="baseline", participation=0.0, battery_kwh=0)
    adoption = []
    for p in ADOPTION:
        for kwh, _ in BATTERIES:
            adoption.append(_aggregate(rows, policy="saanjh", participation=p, battery_kwh=kwh))
    storage = [_aggregate(rows, policy="saanjh", participation=0.6, battery_kwh=kwh)
               for kwh, _ in BATTERY_SWEEP]
    _add_deltas(adoption, baseline)
    _add_deltas(storage, baseline)

    without_battery = [p for p in adoption if p["battery_kwh"] == 0]
    with_100kwh = [p for p in adoption if p["battery_kwh"] == 100]

    def thermal_clear(point):
        return (point["peak_loading_pct"] <= 100.0
                and (point["overload_hours"] or 0.0) <= 0.0)

    def essential_at_least(threshold):
        return lambda p: p["essential_supply_availability_pct"] >= threshold

    def unserved_at_most(share):
        target = baseline["unserved_energy_kwh"] * share
        return lambda p: p["unserved_energy_kwh"] <= target

    thermal_only = _first_where(without_battery, thermal_clear)
    minimum = {
        "definition": (
            "First point in the sweep that meets the stated service target. A thermal-limit "
            "pass on its own is reported separately because emergency shedding can cap "
            "loading while leaving most of the demand unserved."
        ),
        "adoption_without_battery_for_95pct_essential": _first_where(
            without_battery, essential_at_least(95.0)),
        "adoption_with_100kwh_battery_for_95pct_essential": _first_where(
            with_100kwh, essential_at_least(95.0)),
        "adoption_without_battery_for_10pct_unserved_reduction": _first_where(
            without_battery, unserved_at_most(0.90)),
        "storage_at_60pct_adoption_for_95pct_essential": _first_where(
            storage, essential_at_least(95.0)),
        "storage_at_60pct_adoption_for_99pct_essential": _first_where(
            storage, essential_at_least(99.0)),
        "thermal_limit_only_without_battery": thermal_only,
        "thermal_limit_only_note": (
            "Reaching <=100% transformer loading does not mean the shortfall is served. "
            "With no battery and no relay adoption the dispatcher sheds load to stay at "
            "95%, so this point still leaves most of the unserved energy in place. It is "
            "not a service target."
        ) if thermal_only else None,
    }

    ladder = [
        ("thermal_limit", thermal_clear),
        ("essential_ge_90pct", essential_at_least(90.0)),
        ("essential_ge_95pct", essential_at_least(95.0)),
        ("essential_ge_99pct", essential_at_least(99.0)),
        ("unserved_reduction_ge_10pct", unserved_at_most(0.90)),
        ("unserved_reduction_ge_25pct", unserved_at_most(0.75)),
        ("unserved_reduction_ge_50pct", unserved_at_most(0.50)),
    ]
    service_ladder = []
    for name, predicate in ladder:
        service_ladder.append({
            "target": name,
            "adoption_without_battery": _first_where(without_battery, predicate),
            "adoption_with_100kwh_battery": _first_where(with_100kwh, predicate),
            "storage_at_60pct_adoption": _first_where(storage, predicate),
        })

    out = {
        "label": "SIMULATED; stress case forces an overload so the minimum can be measured",
        "scenario": NAME, "seeds": seeds,
        "stress_transformer_kva": STRESS_KVA,
        "stress_transformer_rating_kw": STRESS_KVA * 0.95,
        "dispatch_target_pct": 95,
        "legacy_audit": _legacy_audit(),
        "baseline": baseline,
        "adoption_sweep": adoption,
        "storage_sweep_at_60pct_adoption": storage,
        "minimum": minimum,
        "service_ladder": service_ladder,
        "limits": [
            "The 65 kVA stress transformer is constructed for this test; the committed annual scenarios do not overload (peak 87% / 83%).",
            "Relay capacity is small on a low-income DT: about 9% of homes own an inverter, so even 100% enrolment gives roughly 15 kW.",
            "The dispatcher keeps loading at or below 95% of rating. Thermal compliance alone is not treated as success: the service ladder also requires essential-supply availability or unserved-energy reduction.",
            "This is a 15-minute steady-state model. It does not check transformer thermal time constants or reverse power flow.",
            "'Essential availability' is the share of shortfall time in which the essential band is served; it is not the same as total energy served.",
        ],
    }
    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.join(RESULTS, "overload.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, allow_nan=False)
    return out, path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args(argv)
    out, path = build(a.seeds, a.workers)
    print("Legacy case:", out["legacy_audit"]["baseline_peak_kw"],
          "->", out["legacy_audit"]["saanjh_peak_kw"], "kW")
    print("Baseline stress peak loading:", out["baseline"]["peak_loading_pct"])

    def _point(point):
        if not isinstance(point, dict):
            return point
        return {k: point.get(k) for k in (
            "participation", "battery_kwh", "peak_loading_pct", "overload_hours",
            "essential_supply_availability_pct", "unserved_energy_kwh",
            "unserved_energy_reduction_pct")}

    for key, val in out["minimum"].items():
        print(key, "->", _point(val))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
