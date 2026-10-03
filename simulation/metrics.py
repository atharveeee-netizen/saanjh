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
