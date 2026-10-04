"""Evaluate day-ahead forecasts by accuracy and by the value of the decisions they drive.

    python ai_forecasting/evaluate.py            # full evaluation (Chronos if installed)
    python ai_forecasting/evaluate.py --no-chronos

1. Accuracy (rolling origin, seed 0 of each scenario): every model forecasts each test day
   (days 28-364) from data before that day's midnight. Metrics: MASE against the
   seasonal-naive scale, mean pinball loss over P10/P50/P90, and P10-P90 coverage.
   XGBoost is retrained every 30 days on all earlier days (expanding window), so no
   test day is ever in its training data.
2. Deficit forecast calibration: does the forecast P10-P90 range of evening (17:00-24:00)
   deficit energy contain the realised value?
3. Decision value: year-long engine runs where the community battery shaves the evening
   peak (18:00-22:00) but keeps back a reserve for deficits, set by
   (a) no forecast: a fixed 50% of usable energy,
   (b) seasonal-naive deficit forecast P90,
   (c) XGBoost P90, (d) Chronos P90,
   compared with (e) keeping the battery fully reserved (no peak shaving).
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from ai_forecasting.dataset import STEPS, build_series
from ai_forecasting.deficit_forecast import BatteryPlanner, deficit_quantiles
from ai_forecasting.models import QUANTILES, SeasonalNaive, WeeklyNaive, XGBoostQuantile
from simulation.engine import Scenario, run
from simulation.metrics import run_metrics

RESULTS = os.path.join(ROOT, "simulation", "results")
FC_DIR = os.path.join(ROOT, "ai_forecasting", "forecasts")
CACHE = os.path.join(ROOT, "ai_forecasting", "cache")   # Chronos forecasts (slow on CPU) are cached here
SCENARIOS = ["peri_urban_low_income", "mixed_urban"]
FIRST_DAY = 28
EVENING = (68, 96)


def pinball(y, q):
    return float(np.mean([np.mean(np.maximum(a * (y - q[i]), (a - 1) * (y - q[i])))
                          for i, a in enumerate(QUANTILES)]))


def xgb_crossfit(df, days):
    """Expanding-window XGBoost: at the start of each 30-day block, retrain on all days
    before it and forecast the block. No test day is ever in its own training data."""
    from ai_forecasting.models import _features
    X_full = _features(df)
    out = {}
    for start in range(days[0], days[-1] + 1, 30):
        model = XGBoostQuantile(train_days=start).fit(df)
        for d in range(start, min(start + 30, days[-1] + 1)):
            X = X_full.iloc[d * STEPS:(d + 1) * STEPS]
            out[d] = np.sort(np.vstack([model.models[q].predict(X) for q in QUANTILES]), axis=0)
    return out


def all_forecasts(df, use_chronos, chronos=None, key=None):
    """Forecasts for every test day, cached per scenario/seed/model in ai_forecasting/cache."""
    days = list(range(FIRST_DAY, len(df) // STEPS))
    path = os.path.join(CACHE, f"{key}.npz") if key else None
    cached = {}
    if path and os.path.exists(path):
        z = np.load(path)
        cached = {name: {d: z[name][i] for i, d in enumerate(days)} for name in z.files if name.startswith("chronos")}
    # The fast models are always recomputed; only Chronos forecasts are reused from cache.
    fc = {"seasonal_naive": {d: SeasonalNaive().forecast(df, d) for d in days},
          "weekly_naive": {d: WeeklyNaive().forecast(df, d) for d in days},
          "xgboost_quantile": xgb_crossfit(df, days), **cached}
    if use_chronos and chronos is not None and not cached:
        out = {}
        for i in range(0, len(days), 32):
            out.update(chronos.forecast_batch(df, days[i:i + 32]))
        fc[chronos.name] = out
    if path:
        os.makedirs(CACHE, exist_ok=True)
        np.savez_compressed(path, **{name: np.stack([f[d] for d in days]) for name, f in fc.items()})
    return fc


def accuracy(df, fc):
    y = df["net_kw"].to_numpy().reshape(-1, STEPS)
    # MASE scale: MAE of the lag-96 naive forecast (same block yesterday) over the whole
    # series, so the scale reflects every season rather than one quiet winter month.
    scale = np.mean(np.abs(y[1:].ravel() - y[:-1].ravel()))
    out = {}
    for name, f in fc.items():
        days = sorted(f)
        maes, pins, cover = [], [], []
        for d in days:
            q = f[d]
            maes.append(np.mean(np.abs(y[d] - q[1])))
            pins.append(pinball(y[d], q))
            cover.append(np.mean((y[d] >= q[0]) & (y[d] <= q[2])))
        out[name] = {"mase": float(np.mean(maes) / scale), "mae_kw": float(np.mean(maes)),
                     "pinball_kw": float(np.mean(pins)),
                     "coverage_p10_p90": float(np.mean(cover)) if name != "weekly_naive" else None,
                     "days": len(days)}
    return out


def deficit_forecasts(sc, df, fc_model):
    out = {}
    for d, q in fc_model.items():
        out[d] = deficit_quantiles(sc.alloc, np.maximum(q, 0), df["solar"].to_numpy()[d * STEPS:(d + 1) * STEPS],
                                   float(df["cloudiness"].iloc[d * STEPS]), seed=sc.seed, day=d, window=EVENING)
    return out


def realised_evening_deficit(sc):
    out = {}
    for d in range(len(sc.dates)):
        _, _, loads, pvk = sc.day_inputs(d)[:4]
        _, depth, _ = sc.shortfall_day(d, loads, pvk)
        total = (loads.total - sc.fleet.pv_kwp[:, None] * pvk[None, :]).sum(axis=0)
        out[d] = float((depth * np.maximum(total, 0))[EVENING[0]:EVENING[1]].sum() * 0.25)
    return out


def _decision_task(args):
    name, seed, policy_name, mode, forecasts, param = args
    sc = Scenario(name, seed)
    planner = BatteryPlanner(mode, forecasts=forecasts, quantile=param if mode == "forecast" else 0.9,
                             fixed_share=param if mode == "fixed" else 0.5)
    r = run(sc, "saanjh", forecaster=planner, record_days=[])
    m = run_metrics(r)
    cb = r.ledger.get("community_battery", {})
    return {"scenario": name, "seed": seed, "policy": policy_name,
            "essential_supply_availability": m["essential_supply_availability"],
            "outage_hours_per_home": m["outage_hours_per_home"],
            "peak_shaving_kwh": cb.get("peak_shaving_kwh", 0.0),
            "battery_cycles": cb.get("equivalent_full_cycles", 0.0)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-chronos", action="store_true")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--workers", type=int, default=max(1, min(30, (os.cpu_count() or 2) - 2)))
    a = ap.parse_args(argv)
    t0 = time.time()
    chronos = None
    chronos_note = "not run (--no-chronos)"
    need_chronos = not all(os.path.exists(os.path.join(CACHE, f"{n}_seed{s}.npz")) for n in SCENARIOS for s in range(a.seeds))
    if not a.no_chronos and not need_chronos:
        chronos_note = "amazon/chronos-2 (zero-shot, cached forecasts)"
        class _C:  # marker so cached chronos forecasts are used
            name = "chronos2"; uses_covariates = True
        chronos = _C()
    elif not a.no_chronos:
        try:
            from ai_forecasting.models import ChronosForecaster
            chronos = ChronosForecaster()
            chronos_note = f"{chronos.variant} (zero-shot)"
        except Exception as exc:
            chronos_note = f"unavailable: {exc}"
            print("Chronos unavailable, continuing without it:", exc)

    report = {"label": "Forecasts of SIMULATED DT demand on REAL weather (see ai_forecasting/README.md)",
              "chronos": chronos_note, "accuracy": {}, "deficit_calibration": {}, "decision_value": {}}
    decision_tasks = []
    for name in SCENARIOS:
        for seed in range(a.seeds):
            sc = Scenario(name, seed)
            df = build_series(name, seed, sc)
            fc = all_forecasts(df, chronos is not None, chronos, key=f"{name}_seed{seed}")
            if seed == 0:
                report["accuracy"][name] = accuracy(df, fc)
                if chronos is not None:
                    report["accuracy"][name][chronos.name]["uses_covariates"] = chronos.uses_covariates
                realised = realised_evening_deficit(sc)
                report["deficit_calibration"][name] = {}
                save = {}
            planners = {"seasonal_naive": "seasonal_naive", "xgboost_quantile": "xgboost_quantile"}
            if chronos is not None:
                planners[chronos.name] = chronos.name
            defs = {}
            for label, key in planners.items():
                defs[label] = deficit_forecasts(sc, df, fc[key])
                if seed == 0:
                    days = sorted(defs[label])
                    lo = np.array([defs[label][d]["window_kwh_q"][0.1] for d in days])
                    hi = np.array([defs[label][d]["window_kwh_q"][0.9] for d in days])
                    yv = np.array([realised[d] for d in days])
                    report["deficit_calibration"][name][label] = {
                        "coverage_p10_p90": float(np.mean((yv >= lo) & (yv <= hi))),
                        "share_of_days_above_p90": float(np.mean(yv > hi)),
                        "mean_p90_kwh": float(hi.mean()), "mean_realised_kwh": float(yv.mean())}
                    save[label] = {int(d): {"block_p10": defs[label][d]["block_q"][0].round(2).tolist(),
                                            "block_p50": defs[label][d]["block_q"][1].round(2).tolist(),
                                            "block_p90": defs[label][d]["block_q"][2].round(2).tolist(),
                                            "window_kwh_q": defs[label][d]["window_kwh_q"],
                                            "demand_q": np.round(fc[label][d], 2).tolist()}
                                   for d in days}
            if seed == 0:
                os.makedirs(FC_DIR, exist_ok=True)
                with open(os.path.join(FC_DIR, f"{name}_seed0.json"), "w", encoding="utf-8") as f:
                    json.dump(save, f)
            slim = {label: {d: {"window_kwh_q": v["window_kwh_q"]} for d, v in dd.items()} for label, dd in defs.items()}
            decision_tasks += [(name, seed, "full reserve (no peak shaving)", "full_reserve", None, None)]
            decision_tasks += [(name, seed, f"fixed {int(sh * 100)}% reserve (no forecast)", "fixed", None, sh)
                               for sh in (0.25, 0.5, 0.75)]
            decision_tasks += [(name, seed, f"{label} P{qn} reserve", "forecast", slim[label], q)
                               for label in slim for q, qn in ((0.9, "90"), (0.97, "97"), (0.995, "99.5"))]
        print(f"{name}: forecasts done at {time.time() - t0:.0f} s")

    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        rows = list(ex.map(_decision_task, decision_tasks, chunksize=1))
    dv = pd.DataFrame(rows)
    dv.to_csv(os.path.join(RESULTS, "forecast_decision_value.csv"), index=False)
    for name in SCENARIOS:
        g = dv[dv.scenario == name].groupby("policy", sort=False).mean(numeric_only=True)
        report["decision_value"][name] = {p: {k: float(v) for k, v in row.items() if k != "seed"}
                                          for p, row in g.iterrows()}
    report["decision_value_seeds"] = a.seeds

    path = os.path.join(RESULTS, "results.json")
    data = json.load(open(path, encoding="utf-8"))
    data["forecast"] = report
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(json.dumps({k: report[k] for k in ("accuracy", "deficit_calibration", "decision_value")}, indent=1))
    print(f"Done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
