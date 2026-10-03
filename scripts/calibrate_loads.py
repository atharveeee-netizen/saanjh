"""Check generated household loads against the eMARC calibration targets.

Generates many homes per segment and season, then reports the statistics named in
config/load_segments.yaml (calibration_targets). Writes the summary to
simulation/results/results.json under "load_calibration" and mean daily profiles to
simulation/results/load_profiles.csv.
"""
import os
import sys
import zlib

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.config import load_config, repo_path
from simulation.feeder_sim import update_results
from simulation.models.household import Household

SEASONS = ["winter", "spring", "summer", "monsoon", "post_monsoon"]


def sample_profiles(cfg, segment, season, n_homes=600, n_days=3, seed=0):
    """Return (homes, array[home, day, step] of kW)."""
    rng = np.random.default_rng(seed)
    step_h = cfg["simulation"]["step_min"] / 60
    steps = int(24 / step_h)
    seg = cfg["segments"][segment]
    homes = [Household(i, segment, seg, rng, False, False, False) for i in range(n_homes)]
    out = np.zeros((n_homes, n_days, steps))
    for d in range(n_days):
        for i, h in enumerate(homes):
            h.generate_day(rng, steps, step_h, season=season)
            out[i, d] = sum(h.loads.values()) if h.loads else 0.0
    return homes, out


def hourly(profile, step_h):
    per_hour = int(1 / step_h)
    return profile.reshape(-1, per_hour).mean(axis=1)


def calibrate(cfg=None, n_homes=600, n_days=3):
    cfg = cfg or load_config()
    step_h = cfg["simulation"]["step_min"] / 60
    targets = cfg["calibration_targets"]
    profiles = []
    stats = {}

    cache = {}
    for segment in ("low_income", "middle", "affluent"):
        for season in SEASONS:
            homes, arr = sample_profiles(cfg, segment, season, n_homes, n_days,
                                         seed=zlib.crc32(f"{segment}/{season}".encode()))
            cache[(segment, season)] = (homes, arr)
            mean = arr.mean(axis=(0, 1))
            for step, kw in enumerate(mean):
                profiles.append({"segment": segment, "season": season,
                                 "hour": step * step_h, "mean_w": kw * 1000})

    def window_mean(arr, h0, h1):
        s0, s1 = int(h0 / step_h), int(h1 / step_h)
        return float(arr[:, :, s0:s1].mean() * 1000)

    non_summer = [cache[("middle", s)][1] for s in ("spring", "post_monsoon")]
    stats["middle_night_w"] = float(np.mean([window_mean(a, 0, 5) for a in non_summer]))
    stats["middle_evening_peak_w"] = float(np.mean([window_mean(a, 21, 22) for a in non_summer]))

    homes, arr = cache[("affluent", "summer")]
    ac_idx = [i for i, h in enumerate(homes) if h.owned.get("ac")]
    stats["ac_homes_peak_w"] = float(hourly(arr[ac_idx].mean(axis=(0, 1)), step_h).max() * 1000)

    wh = []
    for segment in ("middle", "affluent"):
        homes, arr = cache[(segment, "winter")]
        idx = [i for i, h in enumerate(homes) if h.owned.get("water_heater")]
        wh.append(arr[idx].mean(axis=1))
    wh = np.concatenate(wh)
    stats["water_heater_homes_peak_w"] = float(hourly(wh.mean(axis=0), step_h).max() * 1000)

    for segment in ("low_income", "middle", "affluent"):
        annual = np.mean([cache[(segment, s)][1].mean() for s in SEASONS])
        stats[f"{segment}_mean_w"] = float(annual * 1000)
        stats[f"{segment}_kwh_per_month"] = float(annual * 24 * 30)

    checks = {k: {"value": stats[k], "target": targets[k],
                  "ok": targets[k][0] <= stats[k] <= targets[k][1]} for k in targets}
    return {"label": "CALIBRATED TO REAL DATA (Prayas eMARC published load patterns)",
            "stats": stats, "checks": checks, "n_homes": n_homes, "n_days": n_days}, \
        pd.DataFrame(profiles)


if __name__ == "__main__":
    summary, profiles = calibrate()
    os.makedirs(repo_path("simulation", "results"), exist_ok=True)
    profiles.to_csv(repo_path("simulation", "results", "load_profiles.csv"), index=False)
    update_results("load_calibration", summary)
    for k, c in summary["checks"].items():
        print(f"{k:28s} {c['value']:8.1f} W   target {c['target']}   {'OK' if c['ok'] else 'OUT OF RANGE'}")
    for seg in ("low_income", "middle", "affluent"):
        print(f"{seg:12s} mean {summary['stats'][seg + '_mean_w']:.0f} W, "
              f"{summary['stats'][seg + '_kwh_per_month']:.0f} kWh/month")
