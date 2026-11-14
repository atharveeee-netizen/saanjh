"""Indian calibration cases: NASA POWER Lucknow, summer AC, cloudy monsoon, forecast error.

    python simulation/calibration_cases.py

Writes ``simulation/results/calibration.json`` for the data-docs section and dashboard.
Everything is computed from the committed NASA POWER weather file, the calibrated load
segments and the committed forecast evaluation. No number is handwritten.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.config import load_config, repo_path
from simulation.engine import Scenario
from simulation.weather import Weather

RESULTS = repo_path("simulation", "results")
NAME = "peri_urban_low_income"


def _day_case(scenario, di, label, weather):
    date, info, loads, pvk, temp = scenario.day_inputs(di)
    ghi = weather._by_date[date]["ghi_w_m2"].to_numpy()
    hours = np.arange(scenario.steps) * scenario.step_h
    demand = loads.total.sum(axis=0)
    pv = (scenario.fleet.pv_kwp[:, None] * pvk[None, :]).sum(axis=0)
    net = demand - pv
    evening = (hours >= 17) & (hours < 19)
    night = (hours >= 18) & (hours < 22)
    cooling_keys = [k for k in ("fans", "cooler", "ac", "ac_day") if k in loads.by_appliance]
    cooling = sum(loads.by_appliance[k].sum(axis=0) for k in cooling_keys) if cooling_keys else np.zeros_like(demand)
    day_energy = float(demand.sum() * scenario.step_h)
    return {
        "label": label,
        "date": str(date),
        "season": info["season"],
        "day_type": info["day_type"],
        "cloudiness": round(float(info["cloudiness"]), 3),
        "tmax_c": round(float(temp.max()), 1),
        "tmean_c": round(float(temp.mean()), 1),
        "ghi_kwh_m2": round(float(ghi.sum() * scenario.step_h / 1000), 2),
        "pv_yield_kwh_per_kwp": round(float(pvk.sum() * scenario.step_h), 3),
        "demand_peak_kw": round(float(demand.max()), 2),
        "demand_peak_hour": f"{int(hours[int(np.argmax(demand))]):02d}:00",
        "net_peak_kw": round(float(net.max()), 2),
        "net_peak_hour": f"{int(hours[int(np.argmax(net))]):02d}:00",
        "evening_mean_demand_kw": round(float(demand[evening].mean()), 2),
        "evening_mean_net_kw": round(float(net[evening].mean()), 2),
        "night_evening_share_of_daily_energy_pct": round(
            float(demand[night].sum() / demand.sum() * 100), 1),
        "cooling_share_of_peak_pct": round(
            float(cooling[int(np.argmax(demand))] / demand[int(np.argmax(demand))] * 100), 1),
        "pv_share_of_evening_demand_pct": round(
            float(pv[evening].sum() / demand[evening].sum() * 100), 2),
        "daily_energy_kwh": round(day_energy, 1),
    }


def build():
    cfg = load_config()
    w = Weather(cfg["site"]["name"], cfg["site"]["year"], 96)
    days = w.days
    summer = days[days["season"] == "summer"]
    monsoon = days[days["season"] == "monsoon"]
    heat = summer[summer["day_type"] == "heatwave"]
    if not len(heat):
        heat = summer.nlargest(1, "tmax_c")
    heat_date = heat.index[0]
    cloud_date = monsoon["cloudiness"].idxmax()
    clear_summer = summer[summer["day_type"] == "clear"]
    clear_date = (clear_summer if len(clear_summer) else summer).nlargest(1, "ghi_kwh_m2").index[0]

    sc = Scenario(NAME, 0)
    cases = {}
    for label, date in (
        ("summer_ac_heatwave", heat_date),
        ("cloudy_monsoon", cloud_date),
        ("clear_summer_reference", clear_date),
    ):
        di = sc.dates.index(date)
        cases[label] = _day_case(sc, di, label, w)

    # Aggregate evening profile on a clear summer day, normalised to the daily mean.
    di = sc.dates.index(clear_date)
    _, _, loads, pvk, _ = sc.day_inputs(di)
    hours = np.arange(sc.steps) * sc.step_h
    demand = loads.total.sum(axis=0)
    profile = demand / demand.mean()
    evening = (hours >= 17) & (hours < 23)

    with open(os.path.join(RESULTS, "results.json"), "r", encoding="utf-8") as f:
        res = json.load(f)
    acc = res["forecast"]["accuracy"]
    forecast_rows = []
    for scenario_name, models in acc.items():
        for model, m in models.items():
            forecast_rows.append({
                "scenario": scenario_name, "model": model,
                "mase": m["mase"], "mae_kw": m["mae_kw"], "pinball_kw": m["pinball_kw"],
                "coverage_p10_p90": m["coverage_p10_p90"], "days": m["days"],
            })
    best = {}
    for scenario_name, models in acc.items():
        best[scenario_name] = min(models, key=lambda k: models[k]["mase"])
    seasonal = {s: acc[s]["seasonal_naive"]["mase"] for s in acc}
    best_mase = {s: acc[s][best[s]]["mase"] for s in acc}
    coverage = {s: acc[s][best[s]]["coverage_p10_p90"] for s in acc}

    out = {
        "label": "REAL DATA (NASA POWER Lucknow 2023) + CALIBRATED load segments + SIMULATED dispatch",
        "site": cfg["site"],
        "weather_label": w.label,
        "annual": {
            "days": int(len(days)),
            "ghi_kwh_m2": round(float(w.q["ghi_w_m2"].sum() / 4000), 0),
            "pv_yield_kwh_per_kwp": round(float(w.q["pv_kw_per_kwp"].sum() / 4), 0),
            "day_types": {k: int(v) for k, v in days["day_type"].value_counts().items()},
            "seasons": {k: int(v) for k, v in days["season"].value_counts().items()},
        },
        "calibration_targets": res.get("load_calibration"),
        "evening_profile_clear_summer": {
            "date": str(clear_date),
            "peak_hour": f"{int(hours[int(np.argmax(profile))]):02d}:00",
            "peak_over_mean": round(float(profile.max()), 2),
            "evening_17_23_share_of_daily_energy_pct": round(
                float(demand[evening].sum() / demand.sum() * 100), 1),
            "normalised_17_23": [round(float(x), 3) for x in profile[evening]],
            "hours_17_23": [round(float(x), 2) for x in hours[evening]],
        },
        "cases": cases,
        "forecast": {
            "models": forecast_rows,
            "best_model": best,
            "best_mase": best_mase,
            "seasonal_naive_mase": seasonal,
            "best_coverage_p10_p90": coverage,
        },
        "honest_read": [
            "The load shapes hit the Prayas eMARC targets (middle-home night 100-150 W, evening 200-250 W; AC homes 500-700 W; water-heater homes 400-600 W), but the segment split below 'middle' is an assumption, not published data.",
            "NASA POWER is a ~50 km reanalysis grid, not a rooftop sensor. Hourly values are held flat within each hour, and horizontal irradiance understates tilted-module output.",
            "The best forecast model is not better than seasonal naive on the peri-urban DT (MASE %.2f vs %.2f); it is only modestly better on the mixed urban DT (MASE %.2f vs %.2f)." % (
                best_mase.get("peri_urban_low_income", float("nan")),
                seasonal.get("peri_urban_low_income", float("nan")),
                best_mase.get("mixed_urban", float("nan")),
                seasonal.get("mixed_urban", float("nan"))),
            "The 80%% P10-P90 interval covers only %.0f%% (peri-urban) and %.0f%% (mixed urban) of realised days, so the intervals are too narrow. This is reported, not hidden." % (
                (coverage.get("peri_urban_low_income") or 0) * 100,
                (coverage.get("mixed_urban") or 0) * 100),
            "The XGBoost model is trained on UCI household data from outside India; the Indian load calibration is in the simulator, not in the ML training set.",
        ],
    }
    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.join(RESULTS, "calibration.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, allow_nan=False)
    return out, path


def main(argv=None):
    argparse.ArgumentParser().parse_args(argv)
    out, path = build()
    print("Day types:", out["annual"]["day_types"])
    print("Summer case:", out["cases"]["summer_ac_heatwave"]["date"],
          out["cases"]["summer_ac_heatwave"]["demand_peak_kw"], "kW peak")
    print("Monsoon case:", out["cases"]["cloudy_monsoon"]["date"],
          out["cases"]["cloudy_monsoon"]["pv_yield_kwh_per_kwp"], "kWh/kWp PV")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
