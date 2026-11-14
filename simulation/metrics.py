"""Reliability, fairness and flexibility metrics computed from engine runs."""
import numpy as np

STEP_H = 0.25


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    if x.sum() <= 0:
        return 0.0
    n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))


def fairness(values):
    """Distribution of a per-home burden (e.g. hours disconnected)."""
    v = np.asarray(values, dtype=float)
    return {
        "gini": gini(v),
        "max": float(v.max()) if len(v) else 0.0,
        "median": float(np.median(v)) if len(v) else 0.0,
        "max_over_median": float(v.max() / np.median(v)) if len(v) and np.median(v) > 0 else None,
        "share_of_homes_affected": float((v > 0).mean()) if len(v) else 0.0,
    }


def availability(homes, mask=None):
    h = homes if mask is None else homes[mask]
    den = h["deficit_blocks"].sum()
    return float(h["ess_ok_blocks"].sum() / den) if den else None


def _pct(num, den):
    return float(num / den * 100) if den else None


def reliability_metrics(r, step_h=STEP_H):
    """Standard reliability indices, unserved energy and the 17:00-19:00 window.

    Definitions (all computed per home over the simulated period):
    * SAIDI-style: total hours fully disconnected / homes.
    * SAIFI-style: number of disconnection episodes / homes.
    * CAIDI: SAIDI / SAIFI.
    * ASAI: fraction of block-time with any supply at the meter.
    * Brownout: connected but held at an essential band below demand.
    * Unserved energy: demand not delivered while fully disconnected (including
      battery-limited backup). Energy curtailed above the band is reported separately;
      ``energy_not_delivered`` is the sum.
    * 17:00-19:00 availability is reported over every block in the window, and over
      deficit blocks only (the latter is the comparable "event" figure).
    """
    h = r.homes
    n = max(len(h), 1)
    blocks = float(h["blocks"].sum()) if "blocks" in h else float(n)
    shed_blocks = float(h["shed_blocks"].sum())
    demand = float(h["demand_kwh"].sum())
    unserved = float(h["unserved_kwh"].sum())
    curtailed = float(h["band_curtailed_kwh"].sum())
    interruptions = float(h["interruptions"].sum()) if "interruptions" in h else 0.0
    saidi = float(h["shed_blocks"].mean() * step_h)
    saifi = interruptions / n
    win_blocks = float(h["window_blocks"].sum()) if "window_blocks" in h else 0.0
    win_supply = float(h["window_supply_blocks"].sum()) if "window_supply_blocks" in h else 0.0
    win_ess = float(h["window_ess_ok_blocks"].sum()) if "window_ess_ok_blocks" in h else 0.0
    win_def = float(h["window_deficit_blocks"].sum()) if "window_deficit_blocks" in h else 0.0
    win_def_ess = (float(h["window_deficit_ess_ok_blocks"].sum())
                   if "window_deficit_ess_ok_blocks" in h else 0.0)
    return {
        "homes": int(len(h)),
        "period_days": round(blocks / n * step_h / 24, 1) if n else None,
        "saidi_hours_per_home": saidi,
        "saifi_interruptions_per_home": saifi,
        "caidi_hours_per_interruption": (saidi / saifi) if saifi > 0 else None,
        "asai_pct": (1 - shed_blocks / blocks) * 100 if blocks else None,
        "supply_availability_pct": (1 - shed_blocks / blocks) * 100 if blocks else None,
        "brownout_hours_per_home": float(h["banded_blocks"].mean() * step_h),
        "brownout_share_of_homes_pct": float((h["banded_blocks"] > 0).mean() * 100),
        "unserved_energy_kwh": unserved,
        "unserved_energy_pct_of_demand": _pct(unserved, demand),
        "curtailed_energy_kwh": curtailed,
        "energy_not_delivered_kwh": unserved + curtailed,
        "energy_not_delivered_pct_of_demand": _pct(unserved + curtailed, demand),
        "window_hours": "17:00-19:00",
        "window_hours_per_home": win_blocks / n * step_h if n else None,
        "window_supply_availability_pct": _pct(win_supply, win_blocks),
        "window_essential_availability_pct": _pct(win_ess, win_blocks),
        "window_deficit_essential_availability_pct": _pct(win_def_ess, win_def),
        "homes_with_any_interruption_pct": float((h["shed_blocks"] > 0).mean() * 100),
        "homes_with_any_brownout_pct": float((h["banded_blocks"] > 0).mean() * 100),
    }


def run_metrics(r, step_h=STEP_H):
    h = r.homes
    burden = (h["shed_blocks"] + h["banded_blocks"]) * step_h
    out = {
        "essential_supply_availability": availability(h),
        "outage_hours_per_home": float(h["shed_blocks"].mean() * step_h),
        "outage_hours_in_deficit_per_home": float(h["shed_deficit_blocks"].mean() * step_h),
        "essential_household_hours": float(h["ess_ok_blocks"].sum() * step_h),
        "deficit_household_hours": float(h["deficit_blocks"].sum() * step_h),
        "banded_hours_per_home": float(h["banded_blocks"].mean() * step_h),
        "energy_not_served_kwh": float(h["unserved_kwh"].sum()),
        "energy_curtailed_above_band_kwh": float(h["band_curtailed_kwh"].sum()),
        "demand_kwh": float(h["demand_kwh"].sum()),
        "fairness_outage_hours": fairness(h["shed_blocks"] * step_h),
        "fairness_total_curtailment_hours": fairness(burden),
        "dt_overload_hours": r.ledger.get("overload_blocks", 0) * step_h,
        "dt_peak_loading_pct": r.ledger.get("peak_loading_pct"),
        "by_segment": {},
    }
    for seg in sorted(h["segment"].unique()):
        m = h["segment"] == seg
        out["by_segment"][seg] = {
            "homes": int(m.sum()),
            "essential_supply_availability": availability(h, m),
            "outage_hours_per_home": float(h.loc[m, "shed_blocks"].mean() * step_h),
            "banded_hours_per_home": float(h.loc[m, "banded_blocks"].mean() * step_h),
        }
    inv = h[h["has_inverter"]]
    led = r.ledger
    flex = {
        "inverter_relay_kwh": led["inverter"]["relay_kwh"],
        "appliance_deferred_kwh": led.get("appliance", {}).get("deferred_kwh", 0.0),
        "ac_setpoint_kwh": led.get("appliance", {}).get("ac_avoided_kwh", 0.0),
        "community_battery_kwh": led.get("community_battery", {}).get("discharged_kwh", 0.0),
        "essential_band_kwh": float(h["band_curtailed_kwh"].sum()),
    }
    flex["demand_flexibility_mwh"] = (flex["inverter_relay_kwh"] + flex["appliance_deferred_kwh"]
                                      + flex["ac_setpoint_kwh"] + flex["essential_band_kwh"]) / 1000
    flex["total_mwh"] = flex["demand_flexibility_mwh"] + flex["community_battery_kwh"] / 1000
    out["flexibility"] = flex
    out["household_battery_cycles_added_per_year"] = float(inv["relay_cycles"].mean()) if len(inv) else 0.0
    out["reliability"] = reliability_metrics(r, step_h)
    for k, v in out["reliability"].items():
        out.setdefault(k, v)
    cb = led.get("community_battery")
    if cb:
        efc = cb["equivalent_full_cycles"]
        out["community_battery"] = {
            "equivalent_full_cycles": efc,
            "capacity_end_kwh": cb["capacity_kwh_end"],
            "nameplate_kwh": cb["nameplate_kwh"],
            "discharged_kwh": cb["discharged_kwh"],
            "charged_kwh": cb["charged_kwh"],
            "losses_kwh": cb["losses_kwh"],
        }
    return out
