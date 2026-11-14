"""The 154 kW feeder stress profile used by the hardware-in-the-loop replay.

The profile is a smooth 24-hour, 15-minute curve with an evening peak of exactly
154.0 kW. It is not a measured feeder; it is the stress case the prototype replays as
the "grid" while real nodes respond. Keeping it in one place means the dashboard, the
gateway and the docs all show the same curve.
"""
import csv
import math
import os
import random

BLOCKS = 96
STEP_MIN = 15
PEAK_KW = 154.0
DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data",
                            "feeder_stress_profile.csv")


def stress_profile(peak_kw=PEAK_KW, seed=11):
    rng = random.Random(seed)
    rows = []
    for b in range(BLOCKS):
        h = b * STEP_MIN / 60.0
        base = 48.0
        morning = 25.0 * math.exp(-((h - 8.0) / 2.5) ** 2)
        afternoon = 15.0 * math.exp(-((h - 15.0) / 3.0) ** 2)
        evening = 85.0 * math.exp(-((h - 19.5) / 2.0) ** 2)
        noise = rng.uniform(-1.2, 1.2)
        rows.append({"block": b, "hour": round(h, 2),
                     "load_kw": max(30.0, base + morning + afternoon + evening + noise)})
    scale = peak_kw / max(r["load_kw"] for r in rows)
    for r in rows:
        r["load_kw"] = round(r["load_kw"] * scale, 2)
    return rows


def load_profile(path=None):
    path = path or DEFAULT_PATH
    if not os.path.exists(path):
        write_profile(path)
    with open(path, "r", encoding="utf-8") as f:
        return [{"block": int(r["block"]), "hour": float(r["hour"]),
                 "load_kw": float(r["load_kw"])} for r in csv.DictReader(f)]


def write_profile(path=None):
    path = path or DEFAULT_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rows = stress_profile()
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["block", "hour", "load_kw"])
        w.writeheader()
        w.writerows(rows)
    return path


def at(profile, hour):
    """Linear interpolation of the 15-minute profile at an arbitrary hour."""
    h = hour % 24
    x = h / (STEP_MIN / 60.0)
    i = int(x) % len(profile)
    j = (i + 1) % len(profile)
    frac = x - int(x)
    return profile[i]["load_kw"] * (1 - frac) + profile[j]["load_kw"] * frac


if __name__ == "__main__":
    p = write_profile()
    prof = load_profile(p)
    print(f"Wrote {p}: peaking at {max(r['load_kw'] for r in prof):.1f} kW at "
          f"{max(prof, key=lambda r: r['load_kw'])['hour']:.2f} h")
