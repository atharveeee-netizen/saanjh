"""Publication-style figures for the README and write-up, generated from results files.

    python scripts/make_figures.py

Writes SVG and PNG to docs/figures/. Plain style: white background, labelled axes with
units, hairline horizontal gridlines, direct labels plus a legend, no in-chart titles
(captions live in the documents). Colours: SAANJH blue, baseline orange (a validated
colour-blind-safe pair), community battery aqua.
"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
RES = os.path.join(ROOT, "simulation", "results")
OUT = os.path.join(ROOT, "docs", "figures")

SAANJH, BASE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#1D2421", "#56605B", "#E2E5E2"
SCEN_LABEL = {"peri_urban_low_income": "Peri-urban low-income DT", "mixed_urban": "Mixed urban DT"}
SEG_LABEL = {"low_income": "Low-income", "middle": "Middle", "affluent": "Affluent"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID,
    "grid.linewidth": 0.8, "legend.frameon": False, "figure.facecolor": "white", "axes.facecolor": "white",
    "svg.fonttype": "none",
})


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, f"{name}.svg"), bbox_inches="tight")
    fig.savefig(os.path.join(OUT, f"{name}.png"), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"docs/figures/{name}.svg")


def results():
    with open(os.path.join(RES, "results.json"), encoding="utf-8") as f:
        return json.load(f)


def fig_availability(res):
    ann = res["annual"]["scenarios"]
    rows = []
    for sc, s in ann.items():
        for seg in ("low_income", "middle", "affluent"):
            if seg in s["baseline"]["by_segment"]:
                rows.append((f"{SCEN_LABEL[sc]}\n{SEG_LABEL[seg]}",
                             s["baseline"]["by_segment"][seg]["essential_supply_availability"]["mean"] * 100,
                             s["saanjh"]["by_segment"][seg]["essential_supply_availability"]["mean"] * 100))
    fig, ax = plt.subplots(figsize=(7.5, 0.55 * len(rows) + 1))
    y = np.arange(len(rows))[::-1]
    h = 0.34
    ax.barh(y + h / 2 + 0.02, [r[2] for r in rows], height=h, color=SAANJH, label="SAANJH")
    ax.barh(y - h / 2 - 0.02, [r[1] for r in rows], height=h, color=BASE, label="Baseline (rotational shedding)")
    for yi, r in zip(y, rows):
        ax.text(r[2] + 0.8, yi + h / 2 + 0.02, f"{r[2]:.0f}%", va="center", fontsize=8.5, color=INK)
        ax.text(r[1] + 0.8, yi - h / 2 - 0.02, f"{r[1]:.0f}%", va="center", fontsize=8.5, color=INK)
    ax.set_yticks(y, [r[0] for r in rows], fontsize=8.5, color=INK)
    ax.set_xlim(0, 108)
    ax.set_xlabel("Essential-supply availability during deficit windows (%)")
    ax.grid(axis="x", color=GRID)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=9)
    save(fig, "availability_by_segment")


def fig_event_day(name="peri_urban_low_income"):
    p_s = os.path.join(RES, "timeseries", f"{name}_saanjh.csv")
    p_b = os.path.join(RES, "timeseries", f"{name}_baseline.csv")
    if not (os.path.exists(p_s) and os.path.exists(p_b)):
        print("timeseries missing; skipping event-day figure")
        return None
    s, b = pd.read_csv(p_s), pd.read_csv(p_b)
    ts = s.copy()
    ts["deficit_kwh"] = ts["unmanaged_gap_kw"].clip(lower=0) * 0.25
    by_day = ts[(ts["hour"] >= 16)].groupby("day")["deficit_kwh"].sum()
    day = int(by_day[by_day > 0].sort_values().index[int(0.9 * (by_day > 0).sum())])
    s, b = s[s["day"] == day], b[b["day"] == day]
    hrs = s["hour"].to_numpy()
    fig, ax = plt.subplots(figsize=(8, 4))
    cut = s["cut_fraction"].to_numpy() > 0
    for i in np.where(cut)[0]:
        ax.axvspan(hrs[i], hrs[i] + 0.25, color="#F1F2EF", lw=0)
    unmanaged = s["demand_kw"] - s["pv_kw"]
    ax.plot(hrs, unmanaged, color=MUTED, lw=1.2, ls=(0, (2, 2)), label="Unmanaged demand")
    alloc = np.where(cut, s["allocation_kw"], np.nan)
    ax.step(hrs, alloc, where="post", color=INK, lw=1.2, label="Supply allocation during shortfall")
    ax.plot(hrs, b["net_kw"], color=BASE, lw=2, label="Baseline: DT load after shedding")
    ax.plot(hrs, s["net_kw"], color=SAANJH, lw=2, label="SAANJH: DT load")
    ax.fill_between(hrs, 0, s["battery_kw"].clip(lower=0), color=AQUA, alpha=0.35, lw=0,
                    label="Community battery discharge")
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 3), [f"{h:02d}:00" for h in range(0, 25, 3)])
    ax.set_ylabel("Power (kW)")
    ax.set_xlabel(f"Time of day, {s['date'].iloc[0]} ({s['day_type'].iloc[0]} day)")
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper left", fontsize=8.5)
    save(fig, f"event_day_{name}")
    base_out = int((b["homes_shed"] > 0).sum())
    return {"date": s["date"].iloc[0], "day_type": s["day_type"].iloc[0], "baseline_blocks_with_shedding": base_out,
            "saanjh_max_homes_shed": int(s["homes_shed"].max()), "saanjh_max_homes_banded": int(s["homes_banded"].max())}


def fig_sensitivity(res):
    sens = res.get("sensitivity", {}).get("scenarios")
    if not sens:
        return
    params = [("community_battery_kwh", "Community battery size (kWh)"),
              ("essential_band_w", "Essential band floor (W)"),
              ("inverter_relay_participation", "Share of inverter owners enrolled")]
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.4))
    for ax, (param, xlabel) in zip(axes, params):
        for name, marker in (("peri_urban_low_income", "o"), ("mixed_urban", "s")):
            rows = sens[name].get(param, [])
            xs = [float(r["value"]) for r in rows]
            ys = [r["saanjh"]["essential_supply_availability"]["mean"] * 100 for r in rows]
            yb = [r["baseline"]["essential_supply_availability"]["mean"] * 100 for r in rows]
            o = np.argsort(xs)
            xs, ys, yb = np.array(xs)[o], np.array(ys)[o], np.array(yb)[o]
            ls = "-" if name == "peri_urban_low_income" else (0, (4, 2))
            ax.plot(xs, ys, color=SAANJH, lw=2, ls=ls, marker=marker, ms=5,
                    label=f"SAANJH, {SCEN_LABEL[name].split(' DT')[0].lower()}")
            ax.plot(xs, yb, color=BASE, lw=1.5, ls=ls, label=f"Baseline, {SCEN_LABEL[name].split(' DT')[0].lower()}")
        ax.set_xlabel(xlabel)
        ax.set_ylim(40, 101)
        ax.set_ylabel("Essential-supply availability (%)")
    axes[0].legend(fontsize=7.5, loc="lower right")
    fig.tight_layout()
    save(fig, "sensitivity")


def fig_monthly(name="peri_urban_low_income"):
    pb = os.path.join(RES, "annual", f"{name}_baseline_monthly.csv")
    ps = os.path.join(RES, "annual", f"{name}_saanjh_monthly.csv")
    if not (os.path.exists(pb) and os.path.exists(ps)):
        return
    b, s = pd.read_csv(pb), pd.read_csv(ps)
    fig, ax = plt.subplots(figsize=(8, 3.4))
    x = b["month"].to_numpy()
    w = 0.38
    ax.bar(x - w / 2 - 0.02, b["outage_hours_per_home"], width=w, color=BASE, label="Baseline")
    ax.bar(x + w / 2 + 0.02, s["outage_hours_per_home"], width=w, color=SAANJH, label="SAANJH")
    ax.set_xticks(range(1, 13), ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    ax.set_ylabel("Outage hours per home")
    ax.legend(fontsize=8.5)
    save(fig, f"monthly_outages_{name}")


def fig_load_profiles():
    p = os.path.join(RES, "load_profiles.csv")
    if not os.path.exists(p):
        return
    d = pd.read_csv(p)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
    colors = {"low_income": BASE, "middle": SAANJH, "affluent": AQUA}
    for ax, season in zip(axes, ["post_monsoon", "summer"]):
        for seg in ("low_income", "middle", "affluent"):
            g = d[(d["segment"] == seg) & (d["season"] == season)]
            ax.plot(g["hour"], g["mean_w"], color=colors[seg], lw=2, label=SEG_LABEL[seg])
            ax.text(24.2, g["mean_w"].iloc[-1], SEG_LABEL[seg], fontsize=8, va="center", color=INK)
        if season == "post_monsoon":
            ax.axhspan(100, 150, xmin=0, xmax=5 / 24, color="#EEF0ED", lw=0)
            ax.axhspan(200, 250, xmin=20.5 / 24, xmax=21.5 / 24, color="#EEF0ED", lw=0)
            ax.text(0.3, 38, "eMARC target, night: 100–150 W (middle homes)", fontsize=7.5, color=MUTED)
            ax.annotate("eMARC target, 21:00: 200–250 W", xy=(21, 200), xytext=(12.6, 6), fontsize=7.5,
                        color=MUTED, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
        ax.set_xlim(0, 24)
        ax.set_ylim(0, 650)
        ax.set_xticks(range(0, 25, 6), [f"{h:02d}:00" for h in range(0, 25, 6)])
        ax.set_xlabel("Time of day")
        ax.text(0, 1.03, {"post_monsoon": "Non-summer (Oct–Nov)", "summer": "Summer (Apr–Jun)"}[season],
                transform=ax.transAxes, fontsize=9.5, color=INK)
    axes[0].set_ylabel("Mean household load (W)")
    axes[1].legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    save(fig, "load_profiles")


def main():
    res = results()
    fig_load_profiles()
    if "annual" in res:
        fig_availability(res)
        fig_monthly()
        info = fig_event_day()
        if info:
            path = os.path.join(RES, "results.json")
            res = results()
            res.setdefault("figures", {})["event_day"] = info
            with open(path, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2)
    if "sensitivity" in res:
        fig_sensitivity(res)


if __name__ == "__main__":
    main()
