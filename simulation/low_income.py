"""Low-income scenario comparison and unit economics.

    python simulation/low_income.py --seeds 2

Three groups are modelled on the peri-urban low-income DT:
  1. homes that already own an inverter battery and enrol a relay node;
  2. homes with no battery, served by the essential band and (if present) the shared pack;
  3. a shared community battery at the DT.

Adoption is swept from 0% to 100% of inverter owners. For every point this module reports
reliability and a transparent cost-per-kW / simple-payback calculation from
``config/economics.yaml``. Cash payback counts DISCOM cash flows only; the value of lost
load is reported separately as a societal benefit.
"""
import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.config import load_config, repo_path
from simulation.economics_engine import load_inputs
from simulation.engine import Scenario, run
from simulation.metrics import reliability_metrics, run_metrics

RESULTS = repo_path("simulation", "results")
NAME = "peri_urban_low_income"
ADOPTION = [0.0, 0.25, 0.5, 0.75, 1.0]
BATTERY = {"capacity_kwh": 100, "power_kw": 40}
GROUPS = {
    "inverter_batteries": {"description": "Homes with their own inverter battery; adoption is the share of inverter owners with a relay node.",
                           "battery": False},
    "shared_battery": {"description": "No household relays; a 100 kWh second-life community battery at the DT plus the smart-meter essential band.",
                        "battery": True},
    "combined": {"description": "Inverter relays and the 100 kWh community battery together.",
                 "battery": True},
}


def _job(args):
    group, adoption, seed, policy = args
    ov = {}
    cb = None
    if group != "baseline" and policy == "saanjh":
        ov = {"participation": {"inverter_relay": adoption}}
        cb = ({**BATTERY} if GROUPS[group]["battery"]
              else {"capacity_kwh": 0, "power_kw": 0})
    sc = Scenario(NAME, seed, overrides=ov)
    r = run(sc, policy, cb_override=cb)
    rel = reliability_metrics(r)
    ops = run_metrics(r)
    ts = r.timeseries
    peak_flex = 0.0
    if len(ts):
        delivered = (ts["relay_kw"] + ts["appliance_reduction_kw"]
                     + ts["battery_kw"].clip(lower=0))
        peak_flex = float(delivered.max())
    return {
        "group": group, "adoption": adoption, "seed": seed, "policy": policy,
        "reliability": rel,
        "essential_supply_availability_pct": (
            ops["essential_supply_availability"] * 100
            if ops["essential_supply_availability"] is not None else None),
        "peak_flex_kw": peak_flex,
        "n_inverter": int(sc.fleet.has_inverter.sum()),
        "n_actuator": int(sc.fleet.has_actuator.sum()),
        "n_homes": int(sc.fleet.n),
    }


def _mean(rows, key):
    v = [r[key] for r in rows if r.get(key) is not None]
    return float(np.mean(v)) if v else None


def _battery_capex(e, capacity_kwh, power_kw):
    if capacity_kwh <= 0:
        return 0.0
    hw = e["hardware"]
    pack = capacity_kwh * (hw["lfp_new_pack_per_kwh"] * hw["second_life_share_of_new"]
                           + hw["repurposing_bms_per_kwh"])
    return float(pack + power_kw * hw["pcs_per_kw"] + hw["enclosure_fire_safety"]
                 + hw["battery_installation_civil"])


def _economics(e, group, adoption, rows, base_rows, n_homes, n_inverter, n_actuator, peak_flex):
    hw, t = e["hardware"], e["tariffs"]
    shared = GROUPS[group]["battery"]
    relay_nodes = n_inverter * adoption
    edge = (hw["dt_gateway"] + hw["head_end_integration_per_dt"]
            + relay_nodes * hw["relay_node"])
    battery = _battery_capex(e, BATTERY["capacity_kwh"], BATTERY["power_kw"]) if shared else 0.0
    capex = edge + battery
    case_unserved = float(np.mean([r["reliability"]["unserved_energy_kwh"] for r in rows]))
    base_unserved = float(np.mean([r["reliability"]["unserved_energy_kwh"] for r in base_rows]))
    served_gain = max(0.0, base_unserved - case_unserved)
    cash = served_gain * t["residential_tariff_per_kwh"] + peak_flex * 200 * 12
    voll = served_gain * e["value_streams"]["voll_per_kwh"]["low_income"]
    return {
        "capex_inr": round(capex, 0),
        "battery_capex_inr": round(battery, 0),
        "edge_capex_inr": round(edge, 0),
        "relay_nodes": round(relay_nodes, 1),
        "peak_flex_kw": round(peak_flex, 2),
        "cost_per_kw_inr": round(capex / peak_flex, 0) if peak_flex > 0.05 else None,
        "cost_per_home_inr": round(capex / n_homes, 0),
        "served_energy_gain_kwh_year": round(served_gain, 1),
        "annual_discom_cash_inr": round(cash, 0),
        "simple_payback_years": round(capex / cash, 1) if cash > 1 else None,
        "annual_societal_voll_inr": round(voll, 0),
        "payback_note": "Simple payback on DISCOM cash only (energy sales + DFPO); VoLL excluded.",
    }


def build(seeds=2, workers=None):
    workers = workers or max(1, min(8, (os.cpu_count() or 2) - 2))
    tasks = [("baseline", 0.0, seed, "baseline") for seed in range(seeds)]
    tasks += [(g, p, seed, "saanjh") for g in GROUPS for p in ADOPTION for seed in range(seeds)]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        rows = list(ex.map(_job, tasks, chunksize=1))

    e, _ = load_inputs()
    cfg = load_config()
    base_rows = [r for r in rows if r["group"] == "baseline"]
    out = {
        "label": "SIMULATED on the peri-urban low-income DT (NASA POWER weather, ESMI-calibrated shortfalls)",
        "scenario": NAME, "seeds": seeds, "adoption_levels": ADOPTION,
        "groups": {},
        "inputs": {
            "relay_node_inr": e["hardware"]["relay_node"],
            "gateway_inr": e["hardware"]["dt_gateway"],
            "head_end_integration_inr": e["hardware"]["head_end_integration_per_dt"],
            "community_battery_kwh": BATTERY["capacity_kwh"],
            "community_battery_kw": BATTERY["power_kw"],
            "residential_tariff_inr_kwh": e["tariffs"]["residential_tariff_per_kwh"],
            "voll_low_income_inr_kwh": e["value_streams"]["voll_per_kwh"]["low_income"],
            "source": "config/economics.yaml (base case)",
        },
        "notes": [
            "Homes without a battery still receive the smart-meter essential band; that is a load-limit function, not a battery.",
            "Payback is a simple undiscounted capex / annual-cash ratio, not an NPV. It is shown to compare cases, not to promise a return.",
            "The DFPO value is the config's flexibility value per kW-month; it is a policy revenue stream, not a guaranteed market price.",
            "The shared battery dominates the capex. A low-income DT needs storage; relays alone cannot carry the evening.",
        ],
    }
    for group in GROUPS:
        points = []
        for p in ADOPTION:
            rs = [r for r in rows if r["group"] == group and abs(r["adoption"] - p) < 1e-9]
            if not rs:
                continue
            peak = float(np.mean([r["peak_flex_kw"] for r in rs]))
            rel = {
                "essential_supply_availability_pct": _mean(rs, "essential_supply_availability_pct"),
                "saidi_hours_per_home": _mean([{**r["reliability"]} for r in rs], "saidi_hours_per_home"),
                "brownout_hours_per_home": _mean([{**r["reliability"]} for r in rs], "brownout_hours_per_home"),
                "unserved_energy_kwh": _mean([{**r["reliability"]} for r in rs], "unserved_energy_kwh"),
                "window_essential_availability_pct": _mean(
                    [{**r["reliability"]} for r in rs], "window_essential_availability_pct"),
            }
            econ = _economics(e, group, p, rs, base_rows, rs[0]["n_homes"],
                              rs[0]["n_inverter"], rs[0]["n_actuator"], peak)
            points.append({"adoption": p, **rel, **econ})
        out["groups"][group] = {"description": GROUPS[group]["description"], "points": points}

    # Best point by essential availability then payback.
    best = None
    for group, block in out["groups"].items():
        for pt in block["points"]:
            key = (pt["essential_supply_availability_pct"] or 0, -(pt["simple_payback_years"] or 99))
            if best is None or key > best[0]:
                best = (key, group, pt)
    if best:
        out["best_case"] = {"group": best[1], **best[2]}

    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.join(RESULTS, "low_income.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, allow_nan=False)
    return out, path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args(argv)
    out, path = build(a.seeds, a.workers)
    for group, block in out["groups"].items():
        print(f"\n{group}")
        for pt in block["points"]:
            print(f"  adoption {pt['adoption']*100:3.0f}%  availability "
                  f"{pt['essential_supply_availability_pct']:.1f}%  peak flex {pt['peak_flex_kw']:.1f} kW  "
                  f"capex Rs {pt['capex_inr']:,.0f}  Rs/kW {pt['cost_per_kw_inr']}  payback {pt['simple_payback_years']}")
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()
