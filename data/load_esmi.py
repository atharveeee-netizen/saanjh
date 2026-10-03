"""Load Prayas ESMI minute-wise voltage data and compute outage statistics.

REAL DATA, downloaded manually. The ESMI dataset (CC0) is on Harvard Dataverse at
https://doi.org/10.7910/DVN/CLLZZM. Downloading needs a short guestbook form, so this
repo cannot fetch it automatically:

  1. Open the DOI above, choose a file such as "ESMI voltage data 2019 Jan-June.csv"
     and "ESMI location information.tab", fill in the guestbook and download.
  2. Put the files in data/raw/esmi/.
  3. Run:  python data/load_esmi.py --locations "Lucknow"   (substring match, optional)

The script writes data/processed/esmi_stats.json. The simulator uses that file to
calibrate the baseline outage pattern when it exists; otherwise it uses the published
ESMI Uttar Pradesh summary figures in config/saanjh.yaml (outage_calibration), which are
also REAL DATA, but aggregated.

Definitions (docs/PROJECT_BRIEF.md): an outage minute has voltage < 130 V; a low-voltage
minute has 130 V <= voltage < the configured low limit (default 0.94 x 230 V).

Two file layouts are accepted, detected automatically:
  * wide:  one row per location-day; columns "Location name", "Date" and one column per
           minute ("00:00", "00:01", ... or "00:00:00", ...)
  * long:  one row per minute; columns for location, a timestamp and a voltage
TODO: confirm the column names against the real 2019 files after the first manual
download; the format fixture in data/samples/ follows the wide layout.
"""
import argparse
import glob
import json
import os
import re

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw", "esmi")
OUT = os.path.join(ROOT, "data", "processed", "esmi_stats.json")
OUTAGE_V = 130.0
EVENING = (17, 23)
MINUTE_COL = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")


def _read(path):
    sep = "\t" if path.endswith(".tab") else ","
    return pd.read_csv(path, sep=sep, low_memory=False)


def to_long(df):
    """Return a frame with columns location, timestamp, voltage."""
    minute_cols = [c for c in df.columns if MINUTE_COL.match(str(c).strip())]
    if len(minute_cols) >= 60:
        loc_col = next(c for c in df.columns if "location" in str(c).lower())
        date_col = next(c for c in df.columns if "date" in str(c).lower())
        long = df.melt(id_vars=[loc_col, date_col], value_vars=minute_cols,
                       var_name="clock", value_name="voltage")
        clock = long["clock"].astype(str).str.slice(0, 5)
        long["timestamp"] = pd.to_datetime(long[date_col].astype(str) + " " + clock,
                                           errors="coerce", dayfirst=False)
        long = long.rename(columns={loc_col: "location"})
        return long[["location", "timestamp", "voltage"]].dropna(subset=["timestamp"])
    loc_col = next(c for c in df.columns if "location" in str(c).lower())
    ts_col = next(c for c in df.columns if any(k in str(c).lower() for k in ("time", "date")))
    v_col = next(c for c in df.columns if "volt" in str(c).lower())
    out = df.rename(columns={loc_col: "location", ts_col: "timestamp", v_col: "voltage"})
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    return out[["location", "timestamp", "voltage"]].dropna(subset=["timestamp"])


def location_stats(g, low_v):
    g = g.dropna(subset=["voltage"]).sort_values("timestamp")
    v = pd.to_numeric(g["voltage"], errors="coerce")
    hours = g["timestamp"].dt.hour
    days = g["timestamp"].dt.date.nunique()
    outage = v < OUTAGE_V
    low = (v >= OUTAGE_V) & (v < low_v)
    by_hour = outage.groupby(hours).sum() / max(days, 1)
    evening = outage[(hours >= EVENING[0]) & (hours < EVENING[1])].sum()
    # Count distinct outages (runs of consecutive outage minutes).
    # A new outage starts when an outage minute follows a non-outage minute or a gap.
    gap = g["timestamp"].diff() != pd.Timedelta(minutes=1)
    starts = int((outage & (~outage.shift(1, fill_value=False) | gap)).sum())
    return {
        "days_with_data": int(days),
        "coverage": float(len(g) / max(days * 1440, 1)),
        "outage_hours_per_day": float(outage.sum() / 60 / max(days, 1)),
        "evening_outage_minutes_per_day": float(evening / max(days, 1)),
        "evening_share_of_outage": float(evening / outage.sum()) if outage.sum() else 0.0,
        "outages_per_day": float(starts / max(days, 1)),
        "low_voltage_hours_per_day": float(low.sum() / 60 / max(days, 1)),
        "outage_minutes_by_hour": {int(h): float(m) for h, m in by_hour.items()},
    }


def compute_stats(paths, location_filter=None, low_v=0.94 * 230):
    frames = [to_long(_read(p)) for p in paths]
    df = pd.concat(frames, ignore_index=True)
    if location_filter:
        df = df[df["location"].astype(str).str.contains(location_filter, case=False)]
    stats = {str(loc): location_stats(g, low_v) for loc, g in df.groupby("location")}
    if stats:
        keys = ["outage_hours_per_day", "evening_outage_minutes_per_day",
                "evening_share_of_outage", "outages_per_day", "low_voltage_hours_per_day"]
        stats_all = {k: float(np.mean([s[k] for s in stats.values()])) for k in keys}
    else:
        stats_all = {}
    return {"label": "REAL DATA (Prayas ESMI minute-wise voltage)", "files": [os.path.basename(p) for p in paths],
            "location_filter": location_filter, "locations": stats, "mean": stats_all}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--locations", default=None, help="substring filter on location name")
    ap.add_argument("--files", nargs="*", default=None)
    a = ap.parse_args()
    paths = a.files or sorted(glob.glob(os.path.join(RAW_DIR, "ESMI*voltage*.*")))
    if not paths:
        raise SystemExit("No ESMI files found in data/raw/esmi/. See the instructions at the top of this file.")
    stats = compute_stats(paths, a.locations)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f"Wrote {OUT} for {len(stats['locations'])} locations")
    print(json.dumps(stats["mean"], indent=2))


if __name__ == "__main__":
    main()
