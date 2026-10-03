"""Evening peak case: DT overload management with household flexibility.

Runs one day (noon to noon, so rebound and recharge finish inside the run) for a
scenario under two policies on identical demand:

* ``baseline``: no SAANJH. Homes draw what they draw.
* ``saanjh``: a one-step load forecast estimates the next block's DT load. If it would
  exceed the dispatch target, SAANJH opens inverter relays and then curtails actuated
  appliances. Everything reported as delivered is the measured physical response of
  each device; recharge and rebound are added back to the feeder.

All outputs are SIMULATED.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.config import load_config, repo_path
from simulation.forecast import OneStepLoadForecaster
from simulation.models.solar import clear_sky_profile
from simulation.models.transformer import Transformer
from simulation.neighbourhood import build_households
from simulation.validators.pypsa_validator import run_power_flow

RESULTS_DIR = repo_path("simulation", "results")
TIMESERIES_DIR = repo_path("simulation", "results", "timeseries")
START_HOUR = 12.0


def run_simulation(policy="baseline", scenario_name="evening_peak_legacy", seed=42,
                   cfg=None, overrides=None, use_forecast=True):
    cfg = cfg or load_config(overrides)
    scenario = cfg["scenarios"][scenario_name]
    step_h = cfg["simulation"]["step_min"] / 60.0
    steps = int(round(24 / step_h))
    hours = (START_HOUR + np.arange(steps) * step_h) % 24

    rng_build = np.random.default_rng(seed)
    homes = build_households(cfg, scenario, rng_build)
    for h in homes:
        h.generate_day(rng_build, steps, step_h, start_hour=START_HOUR)
    pv_per_kwp = clear_sky_profile(hours, 1.0)

    rng_ops = np.random.default_rng(seed + 1_000_003)
    dt = Transformer(cfg["transformer"]["rating_kva"], cfg["electrical"]["power_factor"])
    limit_kw = dt.rating_kw * cfg["transformer"]["dispatch_target_pct"] / 100.0
    stagger = cfg["inverter_battery"]["release_stagger_steps"]

    forecaster = None
    if policy == "saanjh" and use_forecast:
        forecaster = OneStepLoadForecaster(repo_path(cfg["forecast"]["model_path"]), len(homes))

    batt_homes = [h for h in homes if h.inverter is not None and not h.opted_out]
    act_homes = [h for h in homes if h.appliance_flex is not None and not h.opted_out]
    opt_out_dispatches = 0
    rows = []

    for t in range(steps):
        demand = sum(h.demand_kw(t) for h in homes)
        pv = sum(h.pv_kwp for h in homes) * pv_per_kwp[t]
        uncontrolled = demand - pv

        required = 0.0
        forecast_kw = np.nan
        curtail = set()
        if policy == "saanjh":
            if forecaster is not None:
                f = forecaster.predict(hours[t - 1] if t else hours[t])
                forecast_kw = uncontrolled if f is None else f
            else:
                forecast_kw = uncontrolled  # perfect-information variant
            expected_recharge = sum(
                min(h.inverter.charge_kw, max(0.0, h.inverter.target_soc - h.inverter.soc)
                    * h.inverter.capacity_kwh / h.inverter.eta_charge / step_h)
                for h in batt_homes if not h.inverter.relay_open)
            required = max(0.0, forecast_kw + expected_recharge - limit_kw)

            if required > 0:
                expected = 0.0
                for h in batt_homes:
                    if h.inverter.relay_open:
                        h.inverter.release_step = None
                        expected += h.inverter.available_kw(h.backed_up_kw(t), step_h)
                candidates = sorted(
                    (h for h in batt_homes if not h.inverter.relay_open),
                    key=lambda h: (h.inverter.dispatch_steps,
                                   -h.inverter.available_kw(h.backed_up_kw(t), step_h)))
                for h in candidates:
                    if expected >= required:
                        break
                    avail = h.inverter.available_kw(h.backed_up_kw(t), step_h)
                    if avail <= 0:
                        continue
                    h.inverter.open_relay()
                    expected += avail
                shortfall = required - expected
                if shortfall > 0:
                    for h in sorted(act_homes, key=lambda h: h.appliance_flex.curtailed_steps):
                        if shortfall <= 0:
                            break
                        pot = h.appliance_flex.potential_kw(t, step_h)
                        if pot > 0:
                            curtail.add(h.hid)
                            shortfall -= pot
            else:
                for h in batt_homes:
                    if h.inverter.relay_open and h.inverter.release_step is None:
                        h.inverter.schedule_release(t + int(rng_ops.integers(0, stagger + 1)))

        batt_kw = recharge_kw = reduction_kw = rebound_kw = 0.0
        relays_open = 0
        for h in homes:
            if h.inverter is not None:
                if h.opted_out and h.inverter.relay_open:
                    opt_out_dispatches += 1
                relays_open += int(h.inverter.relay_open)
                served, charge = h.inverter.step(t, h.backed_up_kw(t), step_h)
                batt_kw += served
                recharge_kw += charge
            if h.appliance_flex is not None:
                if h.opted_out and h.hid in curtail:
                    opt_out_dispatches += 1
                red, reb = h.appliance_flex.step(t, h.hid in curtail, step_h, rng_ops)
                reduction_kw += red
                rebound_kw += reb

        net = uncontrolled - batt_kw - reduction_kw + rebound_kw + recharge_kw
        if forecaster is not None:
            # The gateway observes the DT meter; the forecaster learns the unmanaged load
            # by adding back what SAANJH itself changed.
            forecaster.observe(net + batt_kw + reduction_kw - rebound_kw - recharge_kw)

        rows.append({
            "step": t,
            "hour": hours[t],
            "demand_kw": demand,
            "pv_kw": pv,
            "uncontrolled_net_kw": uncontrolled,
            "forecast_kw": forecast_kw,
            "required_flex_kw": required,
            "battery_delivered_kw": batt_kw,
            "appliance_reduction_kw": reduction_kw,
            "delivered_flex_kw": batt_kw + reduction_kw,
            "rebound_kw": rebound_kw,
            "recharge_kw": recharge_kw,
            "net_load_kw": net,
            "loading_pct": dt.loading_pct(net),
            "relays_open": relays_open,
            "homes_curtailed": len(curtail),
        })

    df = pd.DataFrame(rows)
    ledger = {"opt_out_dispatches": opt_out_dispatches}
    return df, homes, ledger, cfg


def _event_window(df):
    on = df["required_flex_kw"] > 0
    if not on.any():
        return None
    idx = df.index[on]
    return int(idx.min()), int(idx.max())


def summarise(base_df, saanjh_df, homes, ledger, cfg, scenario_name):
    step_h = cfg["simulation"]["step_min"] / 60.0
    step_min = cfg["simulation"]["step_min"]
    dt = Transformer(cfg["transformer"]["rating_kva"], cfg["electrical"]["power_factor"])
    v_low = cfg["electrical"]["voltage_low_limit_pu"]

    pf_base = run_power_flow(base_df["net_load_kw"], cfg)
    pf_saanjh = run_power_flow(saanjh_df["net_load_kw"], cfg)
    base_df["voltage_v"] = pf_base["voltage_v"]
    saanjh_df["voltage_v"] = pf_saanjh["voltage_v"]
    base_df["line_loss_kw"] = pf_base["line_loss_kw"]
    saanjh_df["line_loss_kw"] = pf_saanjh["line_loss_kw"]

    def block(df, pf):
        return {
            "peak_kw": float(df["net_load_kw"].max()),
            "peak_loading_pct": float(df["loading_pct"].max()),
            "overload_minutes": int((df["loading_pct"] > 100).sum() * step_min),
            "energy_above_rating_kwh": float(np.maximum(0, df["net_load_kw"] - dt.rating_kw).sum() * step_h),
            "min_voltage_v": float(pf["voltage_v"].min()),
            "low_voltage_minutes": int((pf["voltage_pu"] < v_low).sum() * step_min),
            "line_losses_kwh": float(pf["line_loss_kw"].sum() * step_h),
            "total_energy_kwh": float(df["net_load_kw"].sum() * step_h),
        }

    b, s = block(base_df, pf_base), block(saanjh_df, pf_saanjh)

    inv = [h.inverter for h in homes if h.inverter is not None]
    afx = [h.appliance_flex for h in homes if h.appliance_flex is not None]
    batt_ac = sum(i.ac_delivered_kwh for i in inv)
    batt_cell_out = sum(i.cell_out_kwh for i in inv)
    recharge_ac = sum(i.ac_recharge_kwh for i in inv)
    recharge_cell = sum(i.cell_in_kwh for i in inv)
    required_kwh = float(saanjh_df["required_flex_kw"].sum() * step_h)
    delivered_kwh = float(saanjh_df["delivered_flex_kw"].sum() * step_h)
    inverter_sum_kw = sum(i.inverter_kw for i in inv)
    window = _event_window(saanjh_df)
    reserve = cfg["inverter_battery"]["reserve_soc"]

    flex = {
        "required_kwh": required_kwh,
        "delivered_kwh": delivered_kwh,
        "delivery_ratio": delivered_kwh / required_kwh if required_kwh > 0 else None,
        "peak_delivered_kw": float(saanjh_df["delivered_flex_kw"].max()),
        "battery_delivered_kwh": batt_ac,
        "battery_peak_kw": float(saanjh_df["battery_delivered_kw"].max()),
        "sum_inverter_ratings_kw": inverter_sum_kw,
        "appliance_deferred_kwh": sum(a.deferred_kwh for a in afx),
        "ac_setpoint_avoided_kwh": sum(a.ac_avoided_kwh for a in afx),
        "rebound_kwh": sum(a.rebound_kwh + a.ac_rebound_kwh for a in afx),
        "recharge_kwh": recharge_ac,
        "battery_losses_kwh": (batt_cell_out - batt_ac) + (recharge_ac - recharge_cell),
        "pending_deferred_kwh_at_end": sum(a.pending_kwh() for a in afx),
    }
    homes_info = {
        "homes": len(homes),
        "homes_with_inverter": len(inv),
        "homes_with_actuator": len(afx),
        "homes_opted_out": sum(h.opted_out for h in homes),
        "inverter_homes_dispatched": sum(1 for i in inv if i.dispatch_steps > 0),
        "actuator_homes_curtailed": sum(1 for a in afx if a.curtailed_steps > 0),
    }
    invariants = {
        "reserve_breaches": sum(1 for i in inv if i.min_soc_seen < reserve - 1e-6),
        "opt_out_dispatches": ledger["opt_out_dispatches"],
        "battery_peak_within_inverter_ratings": bool(flex["battery_peak_kw"] <= inverter_sum_kw + 1e-9),
    }
    event = None
    if window:
        i0, i1 = window
        ev = saanjh_df.iloc[i0:i1 + 1]
        event = {
            "start": _clock(saanjh_df.loc[i0, "hour"]),
            "end": _clock((saanjh_df.loc[i1, "hour"] + step_h) % 24),
            "duration_minutes": int((i1 - i0 + 1) * step_min),
            "peak_required_kw": float(ev["required_flex_kw"].max()),
            "peak_delivered_kw": float(ev["delivered_flex_kw"].max()),
            "max_relays_open": int(ev["relays_open"].max()),
            "max_homes_curtailed": int(ev["homes_curtailed"].max()),
        }

    return {
        "scenario": scenario_name,
        "label": cfg["scenarios"][scenario_name].get("label", "SIMULATED"),
        "description": " ".join(cfg["scenarios"][scenario_name].get("description", "").split()),
        "transformer_rating_kva": cfg["transformer"]["rating_kva"],
        "dispatch_target_kw": dt.rating_kw * cfg["transformer"]["dispatch_target_pct"] / 100.0,
        "voltage_nominal_v": cfg["electrical"]["voltage_nominal_v"],
        "voltage_low_limit_v": cfg["electrical"]["voltage_nominal_v"] * v_low,
        "forecast": "one-step-ahead XGBoost trained on UCI (non-Indian) household data",
        "baseline": b,
        "saanjh": s,
        "flexibility": flex,
        "households": homes_info,
        "invariants": invariants,
        "event": event,
    }


def _clock(hour):
    h = int(hour) % 24
    m = int(round((hour - int(hour)) * 60))
    return f"{h:02d}:{m:02d}"


def update_results(section, payload):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, "results.json")
    data = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    data[section] = payload
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def generate_results(seed=42, scenario_name="evening_peak_legacy"):
    base_df, _, _, cfg = run_simulation("baseline", scenario_name, seed)
    saanjh_df, homes, ledger, _ = run_simulation("saanjh", scenario_name, seed, cfg=cfg)
    summary = summarise(base_df, saanjh_df, homes, ledger, cfg, scenario_name)
    summary["seed"] = seed

    os.makedirs(TIMESERIES_DIR, exist_ok=True)
    base_df.to_csv(os.path.join(TIMESERIES_DIR, f"{scenario_name}_baseline.csv"), index=False)
    saanjh_df.to_csv(os.path.join(TIMESERIES_DIR, f"{scenario_name}_saanjh.csv"), index=False)
    path = update_results("evening_peak_case", summary)
    return summary, path


def print_table(summary):
    b, s = summary["baseline"], summary["saanjh"]
    rows = [
        ("Peak DT load (kW)", b["peak_kw"], s["peak_kw"]),
        ("Peak loading (%)", b["peak_loading_pct"], s["peak_loading_pct"]),
        ("Overload time (min)", b["overload_minutes"], s["overload_minutes"]),
        ("Energy above DT rating (kWh)", b["energy_above_rating_kwh"], s["energy_above_rating_kwh"]),
        ("Minimum tail voltage (V)", b["min_voltage_v"], s["min_voltage_v"]),
        ("Low-voltage time (min)", b["low_voltage_minutes"], s["low_voltage_minutes"]),
        ("LT line losses (kWh)", b["line_losses_kwh"], s["line_losses_kwh"]),
    ]
    print(f"{'Metric':34s} {'Baseline':>10s} {'SAANJH':>10s}")
    for name, x, y in rows:
        print(f"{name:34s} {x:10.1f} {y:10.1f}")
    print("\nFlexibility:", json.dumps({k: (round(v, 2) if isinstance(v, float) else v)
                                        for k, v in summary["flexibility"].items()}, indent=1))
    print("Invariants:", summary["invariants"])


if __name__ == "__main__":
    summary, path = generate_results()
    print_table(summary)
    print(f"\nWrote {path}")
