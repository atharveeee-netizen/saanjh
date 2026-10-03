"""Forecasting dataset: a DT's unmanaged net demand (demand minus rooftop PV) per 15 min.

SIMULATED series from the calibrated household model (config/load_segments.yaml) on
real NASA POWER weather. In deployment the gateway reconstructs this series from the DT
meter by adding back what SAANJH itself changed. Covariates: air temperature and solar
availability (REAL DATA); a real deployment would use a day-ahead weather forecast,
here the observed values stand in for it (stated as a limitation).
"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from simulation.engine import Scenario

CACHE = os.path.join(ROOT, "ai_forecasting", "data")
STEPS = 96


def build_series(scenario_name, seed=0, scenario=None):
    path = os.path.join(CACHE, f"{scenario_name}_seed{seed}.csv")
    if os.path.exists(path):
        return pd.read_csv(path, parse_dates=["timestamp"])
    sc = scenario or Scenario(scenario_name, seed)
    rows = []
    for d, date in enumerate(sc.dates):
        _, info, loads, pvk, temp = sc.day_inputs(d)
        net = (loads.total - sc.fleet.pv_kwp[:, None] * pvk[None, :]).sum(axis=0)
        ts = pd.date_range(pd.Timestamp(date), periods=STEPS, freq="15min")
        rows.append(pd.DataFrame({"timestamp": ts, "net_kw": net, "temp_c": temp,
                                  "solar": pvk / sc.pv_max, "day": d,
                                  "cloudiness": float(info["cloudiness"])}))
    df = pd.concat(rows, ignore_index=True)
    os.makedirs(CACHE, exist_ok=True)
    df.to_csv(path, index=False)
    return df


def day_matrix(df, col="net_kw"):
    """Reshape a series into (days x 96)."""
    return df[col].to_numpy().reshape(-1, STEPS)
