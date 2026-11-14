"""Robustness: LoRa packet loss and node dropout.

    python simulation/robustness.py --seeds 3

Runs the peri-urban low-income DT under degraded control links. The essential band is a
smart-meter function and is not affected; relay and actuator commands are. Nodes fail
safe: a relay that hears no command leaves the inverter on grid.
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
NAME = "peri_urban_low_income"
CASES = [
    ("perfect", "Ideal link (no loss, no dropout)", None),
    ("loss_5pct", "5% of relay/actuator packets lost per block", {"packet_loss": 0.05}),
    ("loss_20pct", "20% of relay/actuator packets lost per block", {"packet_loss": 0.20}),
    ("dropout_10pct", "10% of nodes offline for a whole day", {"node_dropout": 0.10}),
    ("combined", "20% packet loss plus 10% daily node dropout", {"packet_loss": 0.20, "node_dropout": 0.10}),
]


def _job(args):
    case, seed, policy = args
    comms = dict(CASES[[c[0] for c in CASES].index(case)][2] or {}) or None
    sc = Scenario(NAME, seed)
    r = run(sc, policy, comms=comms)
    rel = reliability_metrics(r)
    ops = run_metrics(r)
    led = r.ledger.get("comms") or {}
    return {
        "case": case, "seed": seed, "policy": policy,
        "essential_supply_availability_pct": (
            ops["essential_supply_availability"] * 100
            if ops["essential_supply_availability"] is not None else None),
        "saidi_hours_per_home": rel["saidi_hours_per_home"],
        "brownout_hours_per_home": rel["brownout_hours_per_home"],
        "unserved_energy_kwh": rel["unserved_energy_kwh"],
        "window_essential_availability_pct": rel["window_essential_availability_pct"],
        "relay_commands": led.get("relay_commands", 0),
        "relay_delivered": led.get("relay_delivered", 0),
        "curtail_commands": led.get("curtail_commands", 0),
        "curtail_delivered": led.get("curtail_delivered", 0),
        "node_days_offline": led.get("node_days_offline", 0),
    }


def _mean(rows, key):
    v = [r[key] for r in rows if r.get(key) is not None]
    return float(np.mean(v)) if v else None


def build(seeds=3, workers=None):
    workers = workers or max(1, min(8, (os.cpu_count() or 2) - 2))
    tasks = [(case, seed, pol) for case, _, _ in CASES for seed in range(seeds)
             for pol in ("baseline", "saanjh")]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        rows = list(ex.map(_job, tasks, chunksize=1))

    base = [r for r in rows if r["policy"] == "baseline"]
    base_summary = {
        "essential_supply_availability_pct": _mean(base, "essential_supply_availability_pct"),
        "saidi_hours_per_home": _mean(base, "saidi_hours_per_home"),
        "brownout_hours_per_home": _mean(base, "brownout_hours_per_home"),
        "unserved_energy_kwh": _mean(base, "unserved_energy_kwh"),
        "window_essential_availability_pct": _mean(base, "window_essential_availability_pct"),
    }
    cases = []
    for case, desc, comms in CASES:
        rs = [r for r in rows if r["case"] == case and r["policy"] == "saanjh"]
        rc = sum(r["relay_commands"] for r in rs)
        rd = sum(r["relay_delivered"] for r in rs)
        cc = sum(r["curtail_commands"] for r in rs)
        cd = sum(r["curtail_delivered"] for r in rs)
        cases.append({
            "case": case, "description": desc,
            "packet_loss": (comms or {}).get("packet_loss", 0.0),
            "node_dropout": (comms or {}).get("node_dropout", 0.0),
            "essential_supply_availability_pct": _mean(rs, "essential_supply_availability_pct"),
            "saidi_hours_per_home": _mean(rs, "saidi_hours_per_home"),
            "brownout_hours_per_home": _mean(rs, "brownout_hours_per_home"),
            "unserved_energy_kwh": _mean(rs, "unserved_energy_kwh"),
            "window_essential_availability_pct": _mean(rs, "window_essential_availability_pct"),
            "relay_command_delivery_pct": (rd / rc * 100) if rc else None,
            "curtail_command_delivery_pct": (cd / cc * 100) if cc else None,
            "relay_commands": rc,
            "node_days_offline": sum(r["node_days_offline"] for r in rs),
        })
    out = {
        "label": "SIMULATED; LoRa link modelled as independent per-block packet loss and per-day node dropout",
        "scenario": NAME, "seeds": seeds,
        "baseline": base_summary,
        "cases": cases,
        "limits": [
            "Packet loss is independent per node and block; real LoRa fading is bursty and correlated.",
            "The band is applied by the smart meter, so a radio outage never removes the essential-supply floor.",
            "A relay node that loses its command leaves the inverter on grid (normally closed), so the failure mode is lost flexibility, not a safety hazard.",
            "These are Monte Carlo draws, not measurements. The hardware packet-success rate is measured separately by the gateway demo.",
        ],
    }
    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.join(RESULTS, "robustness.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, allow_nan=False)
    return out, path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args(argv)
    out, path = build(a.seeds, a.workers)
    for c in out["cases"]:
        print(f"{c['case']:14s} availability {c['essential_supply_availability_pct']:.1f}%  "
              f"outage {c['saidi_hours_per_home']:.1f} h  relay delivery {c['relay_command_delivery_pct']}")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
