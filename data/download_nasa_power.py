"""Download hourly irradiance and temperature from the NASA POWER API.

REAL DATA. Parameters: ALLSKY_SFC_SW_DWN (all-sky surface shortwave irradiance, W/m²)
and T2M (air temperature at 2 m, °C). Times are requested in local solar time (LST);
for Indian longitudes LST is within ~40 minutes of IST.

Usage:
    python data/download_nasa_power.py --lat 26.85 --lon 80.95 --year 2023 --name lucknow

Writes data/raw/nasa_power/<name>_<year>.csv. If the API is unreachable the script exits
with an error; the simulator then falls back to a clearly labelled synthetic profile
(see simulation/weather.py).
"""
import argparse
import json
import os
import sys

import pandas as pd
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "raw", "nasa_power")
API = "https://power.larc.nasa.gov/api/temporal/hourly/point"


def download(lat, lon, year, name):
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN,T2M",
        "community": "RE",
        "latitude": lat,
        "longitude": lon,
        "start": f"{year}0101",
        "end": f"{year}1231",
        "format": "JSON",
        "time-standard": "LST",
    }
    r = requests.get(API, params=params, timeout=120)
    r.raise_for_status()
    payload = r.json()
    p = payload["properties"]["parameter"]
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(list(p["T2M"].keys()), format="%Y%m%d%H"),
        "ghi_w_m2": list(p["ALLSKY_SFC_SW_DWN"].values()),
        "temp_c": list(p["T2M"].values()),
    })
    # NASA POWER uses -999 for missing values.
    df = df.replace(-999.0, float("nan"))
    df["ghi_w_m2"] = df["ghi_w_m2"].clip(lower=0)
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{name}_{year}.csv")
    df.to_csv(path, index=False)
    meta = {
        "source": "NASA POWER hourly API",
        "url": r.url,
        "latitude": lat,
        "longitude": lon,
        "year": year,
        "parameters": ["ALLSKY_SFC_SW_DWN", "T2M"],
        "time_standard": "LST",
        "rows": len(df),
        "missing_ghi": int(df["ghi_w_m2"].isna().sum()),
        "label": "REAL DATA",
    }
    with open(path.replace(".csv", ".json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    return path, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--name", required=True)
    a = ap.parse_args()
    try:
        path, meta = download(a.lat, a.lon, a.year, a.name)
    except Exception as exc:  # network or API failure
        print(f"NASA POWER download failed: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Wrote {path} ({meta['rows']} rows, {meta['missing_ghi']} missing irradiance values)")


if __name__ == "__main__":
    main()
