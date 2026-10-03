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
