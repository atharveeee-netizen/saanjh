"""Energy balance of a dispatch: battery energy + deferred-load energy vs the claim.

    python simulation/energy_balance.py

The legacy console claimed "dispatch 56.25 kW for 45 minutes". That is 42.19 kWh. This
module takes the regenerated evening-peak case, finds the best continuous 45-minute
delivery window, splits it into inverter-battery energy and deferred/curtailed appliance
energy, and reconciles the sum against the claim. Any shortfall is reported explicitly;
it is never folded into the claim.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.config import load_config, repo_path
from simulation.feeder_sim import run_simulation, summarise

RESULTS = repo_path("simulation", "results")
CLAIM_KW = 56.25
CLAIM_MIN = 45


def _window(df, step_h):
    """Best continuous 45-minute window by delivered flexibility energy."""
    n = max(1, int(round(CLAIM_MIN / (step_h * 60))))
    batt = df["battery_delivered_kw"].to_numpy()
    app = df["appliance_reduction_kw"].to_numpy()
    total = batt + app
    if len(total) < n:
        return None
    sums = np.convolve(total, np.ones(n), mode="valid") * step_h
    i = int(np.argmax(sums))
    j = i + n
    return {
        "start": f"{int(df.loc[i, 'hour']):02d}:{int(round((df.loc[i, 'hour'] % 1) * 60)):02d}",
        "end": f"{int(df.loc[j - 1, 'hour']):02d}:{int(round(((df.loc[j - 1, 'hour'] + step_h) % 1) * 60)):02d}",
        "blocks": n,
        "battery_kwh": float(batt[i:j].sum() * step_h),
        "deferred_kwh": float(app[i:j].sum() * step_h),
        "delivered_kwh": float(sums[i]),
        "peak_delivered_kw": float(total[i:j].max()),
        "mean_delivered_kw": float(sums[i] / (n * step_h)),
        "battery_peak_kw": float(batt[i:j].max()),
        "deferred_peak_kw": float(app[i:j].max()),
        "relays_open_max": int(df.loc[i:j - 1, "relays_open"].max()),
        "homes_curtailed_max": int(df.loc[i:j - 1, "homes_curtailed"].max()),
    }


def build(seed=42):
    cfg = load_config()
    step_h = cfg["simulation"]["step_min"] / 60.0
    base, _, _, cfg = run_simulation("baseline", "evening_peak_legacy", seed)
    saanjh, homes, ledger, cfg = run_simulation("saanjh", "evening_peak_legacy", seed, cfg=cfg)
    s = summarise(base, saanjh, homes, ledger, cfg, "evening_peak_legacy")
    win = _window(saanjh, step_h)
    claim_kwh = CLAIM_KW * CLAIM_MIN / 60.0
    delivered = win["delivered_kwh"] if win else 0.0
    unmet = max(0.0, claim_kwh - delivered)
    flex = s["flexibility"]
    hh = s["households"]
    inverter_homes = int(round(CLAIM_KW / cfg["inverter_battery"]["inverter_kw"]))
    current_share = hh["homes_with_inverter"] / hh["homes"] if hh["homes"] else 0.0
    homes_at_current_ownership = (int(np.ceil(inverter_homes / current_share))
                                  if current_share > 0 else None)
    out = {
        "label": "SIMULATED (evening_peak_legacy, one day, seed %d)" % seed,
        "scenario": "evening_peak_legacy",
        "seed": seed,
        "legacy_claim": {
            "power_kw": CLAIM_KW, "duration_min": CLAIM_MIN,
            "energy_kwh": round(claim_kwh, 3),
            "source": "legacy operator-console page and video title cards (artefacts removed)",
        },
        "simulated_event": {
            "event": s["event"],
            "required_kwh": flex["required_kwh"],
            "delivered_kwh": flex["delivered_kwh"],
            "battery_delivered_kwh": flex["battery_delivered_kwh"],
            "appliance_deferred_kwh": flex["appliance_deferred_kwh"],
            "ac_setpoint_avoided_kwh": flex["ac_setpoint_avoided_kwh"],
            "rebound_kwh": flex["rebound_kwh"],
            "recharge_kwh": flex["recharge_kwh"],
            "peak_delivered_kw": flex["peak_delivered_kw"],
            "delivery_ratio": flex["delivery_ratio"],
            "battery_peak_kw": flex["battery_peak_kw"],
            "sum_inverter_ratings_kw": flex["sum_inverter_ratings_kw"],
        },
        "best_45_min": win,
        "reconciliation": {
            "target_kwh": round(claim_kwh, 3),
            "battery_kwh": round(win["battery_kwh"], 3) if win else 0.0,
            "deferred_kwh": round(win["deferred_kwh"], 3) if win else 0.0,
            "delivered_kwh": round(delivered, 3),
            "unmet_kwh": round(unmet, 3),
            "delivered_pct_of_claim": round(delivered / claim_kwh * 100, 1),
            "battery_share_pct": round(win["battery_kwh"] / delivered * 100, 1) if delivered else 0.0,
            "deferred_share_pct": round(win["deferred_kwh"] / delivered * 100, 1) if delivered else 0.0,
            "unmet_share_pct": round(unmet / claim_kwh * 100, 1),
            "identity": "battery + deferred + unmet = 42.19 kWh",
            "adds_up": bool(abs(win["battery_kwh"] + win["deferred_kwh"] + unmet - claim_kwh) < 1e-6),
        },
        "fleet_requirement": {
            "inverter_kw_each": cfg["inverter_battery"]["inverter_kw"],
            "inverter_homes_for_claim_power": inverter_homes,
            "current_inverter_share": round(current_share, 3),
            "homes_needed_at_current_ownership": homes_at_current_ownership,
            "note": ("Even at full inverter output the claim needs about 81 inverter homes; "
                     "the legacy fleet has 13. The remaining energy has to come from deferred "
                     "appliances and the community battery, which this legacy case does not have."),
        },
        "notes": [
            "The 56.25 kW / 42.19 kWh figure is not reproduced by the committed simulation. "
            "It is retained only as the legacy claim being audited.",
            "battery_kwh is AC energy measured at the inverter output; deferred_kwh is "
            "appliance load moved out of the window. Rebound and recharge return later and "
            "are reported separately.",
            "The best 45-minute window is an upper bound on what the modelled fleet can "
            "deliver, not an operating schedule.",
        ],
    }
    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.join(RESULTS, "energy_balance.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, allow_nan=False)
    return out, path


def main(argv=None):
    argparse.ArgumentParser().parse_args(argv)
    out, path = build()
    r = out["reconciliation"]
    print(f"Claim {r['target_kwh']:.2f} kWh = battery {r['battery_kwh']:.2f} "
          f"+ deferred {r['deferred_kwh']:.2f} + unmet {r['unmet_kwh']:.2f}")
    print(f"Delivered {r['delivered_pct_of_claim']:.0f}% of the legacy claim. Wrote {path}")


if __name__ == "__main__":
    main()
