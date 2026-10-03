"""Render result tables from simulation/results/results.json into marked doc sections.

A section in a Markdown file looks like:

    <!-- results:evening_peak:start -->
    ...generated content...
    <!-- results:evening_peak:end -->

Run ``python scripts/render_results.py`` after any simulation run. ``--check`` exits
non-zero if any file is out of date (used by the tests).
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "simulation", "results", "results.json")
TARGETS = ["README.md", os.path.join("docs", "WRITEUP.md")]


def kw(x):
    return f"{x:,.1f}"


def pct(x):
    return f"{x:,.0f}%"


def change(a, b, unit=""):
    d = b - a
    sign = "+" if d > 0 else ("−" if d < 0 else "±")
    if unit == "%":
        return f"{sign}{abs(d):,.0f} pts"
    return f"{sign}{abs(d):,.1f}{unit}"


def render_evening_peak(res):
    r = res["evening_peak_case"]
    b, s, f = r["baseline"], r["saanjh"], r["flexibility"]
    hh = r["households"]
    lines = [
        f"*{r['label']}. Scenario `{r['scenario']}`: {hh['homes']} homes on a "
        f"{r['transformer_rating_kva']} kVA DT, one day, seed {r['seed']}. "
        f"Forecast: {r['forecast']}.*",
        "",
        "| Metric | Baseline | SAANJH | Change |",
        "|---|---:|---:|---:|",
        f"| Peak DT load (kW) | {kw(b['peak_kw'])} | {kw(s['peak_kw'])} | {change(b['peak_kw'], s['peak_kw'])} |",
        f"| Peak DT loading | {pct(b['peak_loading_pct'])} | {pct(s['peak_loading_pct'])} | {change(b['peak_loading_pct'], s['peak_loading_pct'], '%')} |",
        f"| Time above DT rating (min) | {b['overload_minutes']} | {s['overload_minutes']} | {change(b['overload_minutes'], s['overload_minutes'])} |",
        f"| Energy above DT rating (kWh) | {kw(b['energy_above_rating_kwh'])} | {kw(s['energy_above_rating_kwh'])} | {change(b['energy_above_rating_kwh'], s['energy_above_rating_kwh'])} |",
        f"| Minimum tail-end voltage (V) | {kw(b['min_voltage_v'])} | {kw(s['min_voltage_v'])} | {change(b['min_voltage_v'], s['min_voltage_v'])} |",
        f"| Time below {kw(r['voltage_low_limit_v'])} V (min) | {b['low_voltage_minutes']} | {s['low_voltage_minutes']} | {change(b['low_voltage_minutes'], s['low_voltage_minutes'])} |",
        "",
        "| Flexibility ledger | Value |",
        "|---|---:|",
        f"| Flexibility requested (kWh) | {kw(f['required_kwh'])} |",
        f"| Flexibility delivered (kWh) | {kw(f['delivered_kwh'])} |",
        f"| … from inverter batteries (kWh) | {kw(f['battery_delivered_kwh'])} |",
        f"| … from deferred appliances (kWh) | {kw(f['appliance_deferred_kwh'])} |",
        f"| … from AC setpoint raise (kWh) | {kw(f['ac_setpoint_avoided_kwh'])} |",
        f"| Rebound added back later (kWh) | {kw(f['rebound_kwh'])} |",
        f"| Battery recharge added back (kWh) | {kw(f['recharge_kwh'])} |",
        f"| Battery conversion losses (kWh) | {kw(f['battery_losses_kwh'])} |",
        f"| Peak battery output / sum of inverter ratings (kW) | {kw(f['battery_peak_kw'])} / {kw(f['sum_inverter_ratings_kw'])} |",
        f"| Homes with inverter / with actuator / opted out | {hh['homes_with_inverter']} / {hh['homes_with_actuator']} / {hh['homes_opted_out']} |",
    ]
    return "\n".join(lines)


RENDERERS = {
    "evening_peak": render_evening_peak,
}


SCEN = {"peri_urban_low_income": "Peri-urban low-income DT", "mixed_urban": "Mixed urban DT"}
SEG = {"low_income": "Low-income", "middle": "Middle", "affluent": "Affluent"}


def _m(block, key):
    v = block.get(key)
    return None if v is None else v["mean"]


def _rng(block, key, scale=1.0, fmt="{:.1f}", unit=""):
    v = block.get(key)
    if v is None:
        return "–"
    f = lambda x: fmt.format(x * scale) + unit
    return f"{f(v['mean'])} ({f(v['p10'])}–{f(v['p90'])})"


def render_annual(res):
    a = res["annual"]
    lines = [f"*{a['label']}. Mean over {a['seeds']} Monte Carlo seeds, 365 days at 15-minute resolution, "
             f"weather for {a['site']['name'].title()} {a['site']['year']}; P10–P90 across seeds in brackets.*", ""]
    for name, s in a["scenarios"].items():
        b, v = s["baseline"], s["saanjh"]
        cal = s["calibration"]
        lines += [
            f"**{SCEN.get(name, name)}**: {s['homes']} homes on a {s['transformer_kva']} kVA DT "
            f"(segment mix {', '.join(f'{SEG[k]} {int(round(x * 100))}%' for k, x in s['segment_mix'].items())}). "
            f"Baseline calibrated to ESMI '{s['esmi_category'].replace('_', ' ')}' locations: "
            f"{cal['evening_minutes']:.0f} shortfall outage minutes per evening (target {cal['target_evening_minutes']:.1f}), "
            f"{cal['daily_minutes']:.0f} per day (target {cal['target_daily_minutes']:.1f}).",
            "",
            "| Metric | Baseline | SAANJH |",
            "|---|---:|---:|",
            f"| Essential-supply availability in deficit windows | {_rng(b, 'essential_supply_availability', 100, '{:.0f}', '%')} | {_rng(v, 'essential_supply_availability', 100, '{:.0f}', '%')} |",
            f"| Outage hours per home per year (full disconnection) | {_rng(b, 'outage_hours_per_home')} | {_rng(v, 'outage_hours_per_home')} |",
            f"| Hours on essential band per home per year | {_rng(b, 'banded_hours_per_home')} | {_rng(v, 'banded_hours_per_home')} |",
            f"| Energy not served (kWh/year) | {_rng(b, 'energy_not_served_kwh', fmt='{:,.0f}')} | {_rng(v, 'energy_not_served_kwh', fmt='{:,.0f}')} |",
            f"| Energy curtailed above the band (kWh/year) | {_rng(b, 'energy_curtailed_above_band_kwh', fmt='{:,.0f}')} | {_rng(v, 'energy_curtailed_above_band_kwh', fmt='{:,.0f}')} |",
            f"| DT peak loading | {_m(b, 'dt_peak_loading_pct'):.0f}% | {_m(v, 'dt_peak_loading_pct'):.0f}% |",
            f"| Fairness of outage hours across homes (Gini, 0 = equal) | {_m(b, 'fairness_outage_gini'):.2f} | {_m(v, 'fairness_outage_gini'):.2f} |",
            "",
            "| Essential-supply availability by segment | Baseline | SAANJH |",
            "|---|---:|---:|",
        ]
        for seg in [k for k in SEG if k in b["by_segment"]]:
            sb, sv = b["by_segment"][seg], v["by_segment"][seg]
            lines.append(f"| {SEG.get(seg, seg)} | {sb['essential_supply_availability']['mean'] * 100:.0f}% | "
                         f"{sv['essential_supply_availability']['mean'] * 100:.0f}% |")
        f = v["flexibility"]
        cb = v.get("community_battery", {})
        lines += [
            "",
            f"Household-hours of essential supply preserved per year: "
            f"{s['essential_household_hours_preserved']['mean']:,.0f}. "
            f"Flexibility delivered per year: {f['demand_flexibility_mwh']['mean']:.1f} MWh of demand flexibility "
            f"(inverter relays {f['inverter_relay_kwh']['mean'] / 1000:.1f} MWh, essential band "
            f"{f['essential_band_kwh']['mean'] / 1000:.2f} MWh, appliances "
            f"{(f['appliance_deferred_kwh']['mean'] + f['ac_setpoint_kwh']['mean']) / 1000:.2f} MWh) plus "
            f"{f['community_battery_kwh']['mean'] / 1000:.1f} MWh from the community battery"
            + (f" ({cb['equivalent_full_cycles']['mean']:.0f} equivalent full cycles)" if cb else "")
            + f". Extra cycles on household inverter batteries (average over homes with an inverter): "
            f"{v['household_battery_cycles_added_per_year']['mean']:.1f} per year.",
            "",
        ]
    return "\n".join(lines).rstrip()


def render_sensitivity(res):
    sens = res.get("sensitivity")
    if not sens:
        return "*Sensitivity runs not yet available.*"
    label = {"essential_band_w": "Essential band floor (W)", "community_battery_kwh": "Community battery (kWh)",
             "inverter_relay_participation": "Inverter owners enrolled", "segment_mix": "Segment mix",
             "deficit_share": "Share of outages caused by shortfall", "shortfall_depth": "Shortfall depth",
             "forecast": "Battery reserve policy"}
    lines = [f"*SIMULATED. Each row changes one input; mean of {sens['seeds']} seeds. "
             "Availability = essential-supply availability in deficit windows.*", "",
             "| Input | Value | " + " | ".join(f"{SCEN[n]}: baseline / SAANJH availability, SAANJH outage h" for n in sens["scenarios"]) + " |",
             "|---|---|" + "---:|" * len(sens["scenarios"])]
    names = list(sens["scenarios"])
    params = list(sens["scenarios"][names[0]])
    for p in params:
        for i, row in enumerate(sens["scenarios"][names[0]][p]):
            cells = []
            for n in names:
                r = sens["scenarios"][n][p][i]
                cells.append(f"{r['baseline']['essential_supply_availability']['mean'] * 100:.0f}% / "
                             f"{r['saanjh']['essential_supply_availability']['mean'] * 100:.0f}%, "
                             f"{r['saanjh']['outage_hours_per_home']['mean']:.1f} h")
            lines.append(f"| {label.get(p, p)} | {row['value']} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


RENDERERS["annual"] = render_annual
RENDERERS["sensitivity"] = render_sensitivity


def load_results():
    with open(RESULTS, "r", encoding="utf-8") as f:
        return json.load(f)


def render_file(path, res):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    pattern = re.compile(r"(<!-- results:(\w+):start -->\n)(.*?)(<!-- results:\2:end -->)", re.S)

    def sub(m):
        name = m.group(2)
        if name not in RENDERERS:
            raise KeyError(f"No renderer for section '{name}' in {path}")
        return m.group(1) + RENDERERS[name](res) + "\n" + m.group(4)

    starts = len(re.findall(r"<!-- results:\w+:start -->", text))
    new, n = pattern.subn(sub, text)
    if n != starts:
        raise ValueError(f"{path}: {starts} result markers but only {n} well-formed sections")
    return text, new


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if any file is out of date")
    args = ap.parse_args(argv)
    res = load_results()
    stale = []
    for rel in TARGETS:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        old, new = render_file(path, res)
        if old != new:
            if args.check:
                stale.append(rel)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new)
                print(f"Updated {rel}")
    if stale:
        print("Out of date: " + ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
