"""Weather, rooftop PV output and day types.

REAL DATA when data/processed/weather_<site>_<year>.csv exists (built from NASA POWER by
``python simulation/weather.py --site lucknow --year 2023``). Otherwise a SIMULATED
fallback is generated from a clear-sky shape with day-type cloudiness, and every result
built on it is labelled as such.

PV model: P = kWp x GHI/1000 x PR x (1 + gamma x (T_cell - 25)),
T_cell = T_air + (NOCT - 20)/800 x GHI. Horizontal irradiance is used for rooftop
modules, which slightly understates tilted-module output (stated as a limitation).
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.config import repo_path

PR = 0.80          # [ASSUMPTION] performance ratio (inverter, wiring, soiling)
GAMMA = -0.004     # [ASSUMPTION] crystalline-Si temperature coefficient per degC
NOCT = 45.0        # [ASSUMPTION]

SEASON_BY_MONTH = {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "summer",
                   5: "summer", 6: "summer", 7: "monsoon", 8: "monsoon", 9: "monsoon",
                   10: "post_monsoon", 11: "post_monsoon"}


def processed_path(site, year):
    return repo_path("data", "processed", f"weather_{site}_{year}.csv")


def build_processed(site, year):
    """Convert the raw NASA POWER download into 15-minute rows with day types."""
    raw = repo_path("data", "raw", "nasa_power", f"{site}_{year}.csv")
    df = pd.read_csv(raw, parse_dates=["timestamp"])
    df = df.set_index("timestamp").sort_index()
    # Hourly averages, held constant within the hour at 15-minute resolution.
    idx = pd.date_range(df.index.min(), df.index.max() + pd.Timedelta(minutes=45), freq="15min")
    q = df.reindex(idx, method="ffill")
    q.index.name = "timestamp"
    q = q.reset_index()
    q.to_csv(processed_path(site, year), index=False)
    return q


def pv_kw_per_kwp(ghi, temp_c):
    ghi = np.asarray(ghi, dtype=float)
    t_cell = np.asarray(temp_c, dtype=float) + (NOCT - 20) / 800 * ghi
    return np.clip(ghi / 1000 * PR * (1 + GAMMA * (t_cell - 25)), 0, None)


def classify_days(daily):
    """Label each day clear / cloudy / monsoon / heatwave.

    heatwave: daily maximum air temperature >= 40 degC (IMD plains threshold; IMD also
              requires a departure from normal, which we do not model).
    monsoon:  a Jul-Sep day.
    cloudy:   any other day with irradiance below 75% of the month's 90th percentile.
    clear:    otherwise.
    """
    p90 = daily.groupby("month")["ghi_kwh_m2"].transform(lambda s: s.quantile(0.9))
    types = np.where(daily["tmax_c"] >= 40, "heatwave",
             np.where(daily["season"] == "monsoon", "monsoon",
             np.where(daily["ghi_kwh_m2"] < 0.75 * p90, "cloudy", "clear")))
    return types


class Weather:
    """Year of 15-minute weather with per-day summaries."""

    def __init__(self, site="lucknow", year=2023, steps_per_day=96, seed=0):
        self.site, self.year = site, year
        path = processed_path(site, year)
        if not os.path.exists(path) and os.path.exists(
                repo_path("data", "raw", "nasa_power", f"{site}_{year}.csv")):
            build_processed(site, year)
        if os.path.exists(path):
            q = pd.read_csv(path, parse_dates=["timestamp"])
            self.label = f"REAL DATA (NASA POWER hourly, {site} {year})"
            self.is_real = True
        else:
            # TODO: replace with real data by running data/download_nasa_power.py
            q = synthetic_year(year, steps_per_day, seed)
            self.label = "SIMULATED (synthetic clear-sky profile with day-type cloudiness)"
            self.is_real = False
        q["date"] = q["timestamp"].dt.date
        q["pv_kw_per_kwp"] = pv_kw_per_kwp(q["ghi_w_m2"], q["temp_c"])
        self.q = q
        days = q.groupby("date").agg(ghi_kwh_m2=("ghi_w_m2", lambda s: s.sum() / 4000),
                                     tmax_c=("temp_c", "max"), tmean_c=("temp_c", "mean"))
        days["month"] = [d.month for d in days.index]
        days["season"] = days["month"].map(SEASON_BY_MONTH)
        days["day_type"] = classify_days(days)
        p90 = days.groupby("month")["ghi_kwh_m2"].transform(lambda x: x.quantile(0.9))
        days["cloudiness"] = (1 - days["ghi_kwh_m2"] / p90).clip(0, 1)
        self.days = days
        self.dates = list(days.index)
        self._by_date = {d: g for d, g in q.groupby("date")}

    def day(self, date):
        g = self._by_date[date]
        return g["pv_kw_per_kwp"].to_numpy(), g["temp_c"].to_numpy()


def synthetic_year(year, steps_per_day=96, seed=0):
    """SIMULATED fallback weather for when NASA POWER data is unavailable."""
    rng = np.random.default_rng(seed)
    rows = []
    step_h = 24 / steps_per_day
    for date in pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D"):
        season = SEASON_BY_MONTH[date.month]
        clearness = {"winter": 0.7, "spring": 0.8, "summer": 0.85,
                     "monsoon": 0.55, "post_monsoon": 0.75}[season] * rng.uniform(0.6, 1.15)
        tmax = {"winter": 23, "spring": 33, "summer": 41, "monsoon": 34,
                "post_monsoon": 30}[season] + rng.normal(0, 2)
        for k in range(steps_per_day):
            h = k * step_h
            x = (h - 12.25) / 6.25
            ghi = 1000 * clearness * np.cos(x * np.pi / 2) if abs(x) < 1 else 0.0
            temp = tmax - 9 + 9 * np.cos((h - 15) / 24 * 2 * np.pi)
            rows.append({"timestamp": date + pd.Timedelta(hours=h),
                         "ghi_w_m2": max(0.0, ghi), "temp_c": temp})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="lucknow")
    ap.add_argument("--year", type=int, default=2023)
    a = ap.parse_args()
    build_processed(a.site, a.year)
    w = Weather(a.site, a.year)
    print(w.label)
    print(w.days["day_type"].value_counts().to_string())
    print("Annual PV yield per kWp (kWh):", round(w.q["pv_kw_per_kwp"].sum() / 4, 0))
