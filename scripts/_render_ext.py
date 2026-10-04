"""Renderers for forecasting and economics sections (imported by render_results.py)."""

SCEN = {"peri_urban_low_income": "Peri-urban low-income DT", "mixed_urban": "Mixed urban DT"}
MODEL = {"seasonal_naive": "Seasonal naive", "weekly_naive": "Weekly naive",
         "xgboost_quantile": "XGBoost quantile", "chronos2": "Chronos-2 (zero-shot)",
         "chronos_bolt": "Chronos-Bolt (zero-shot)"}


def rupees(x):
    """Indian digit grouping: Rs 12,34,567."""
    neg = x < 0
    s = str(int(round(abs(x))))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("−" if neg else "") + "Rs " + s


def _model_label(text):
    for k, m in MODEL.items():
        text = text.replace(k, m)
    return text


def render_forecast_accuracy(res):
    f = res.get("forecast")
    if not f:
        return "*Not yet evaluated.*"
    lines = [f"*{f['label']}. Day-ahead, 96 blocks, issued at midnight; test days 28–364 of seed 0. "
             f"MASE below 1 beats yesterday's profile. Chronos: {f['chronos']}.*", ""]
    for name, acc in f["accuracy"].items():
        lines += [f"**{SCEN.get(name, name)}**", "",
                  "| Model | MASE | MAE (kW) | Pinball loss (kW) | P10–P90 coverage |", "|---|---:|---:|---:|---:|"]
        for m, v in acc.items():
            cov = "–" if v.get("coverage_p10_p90") is None else f"{v['coverage_p10_p90'] * 100:.0f}%"
            lines.append(f"| {MODEL.get(m, m)} | {v['mase']:.2f} | {v['mae_kw']:.1f} | {v['pinball_kw']:.2f} | {cov} |")
        cal = f["deficit_calibration"].get(name, {})
        if cal:
            lines += ["", "| Evening deficit-energy forecast from | P10–P90 coverage | Days above P90 | Mean P90 (kWh) | Mean realised (kWh) |",
                      "|---|---:|---:|---:|---:|"]
            for m, v in cal.items():
                lines.append(f"| {MODEL.get(m, m)} | {v['coverage_p10_p90'] * 100:.0f}% | {v['share_of_days_above_p90'] * 100:.0f}% | "
                             f"{v['mean_p90_kwh']:.1f} | {v['mean_realised_kwh']:.1f} |")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_forecast_decision(res):
    f = res.get("forecast")
    if not f:
        return "*Not yet evaluated.*"
    names = list(f["decision_value"])
    lines = [f"*SIMULATED. Year-long SAANJH runs, mean of {f['decision_value_seeds']} seeds. The community battery "
             "shaves the 18:00–22:00 peak but keeps a deficit reserve set by each policy.*", "",
             "| Reserve policy | " + " | ".join(f"{SCEN[n]}: availability / outage h / peak shaved (MWh)" for n in names) + " |",
             "|---|" + "---:|" * len(names)]
    for pol in f["decision_value"][names[0]]:
        cells = []
        for n in names:
            v = f["decision_value"][n].get(pol)
            cells.append("–" if v is None else f"{v['essential_supply_availability'] * 100:.1f}% / "
                         f"{v['outage_hours_per_home']:.1f} h / {v['peak_shaving_kwh'] / 1000:.1f}")
        lines.append(f"| {_model_label(pol)} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_economics(res):
    ec = res.get("economics")
    if not ec:
        return "*Not yet computed.*"
    names = list(ec["scenarios"])
    lines = ["*Computed by simulation/economics_engine.py from config/economics.yaml (base case) and the "
             "year-long results. Per DT, DISCOM-owned model.*", "",
             "| | " + " | ".join(SCEN[n] for n in names) + " |", "|---|" + "---:|" * len(names)]
    rows = [
        ("Up-front cost (community battery + edge)", lambda m: rupees(m["capex"]["total"])),
        ("…of which community battery", lambda m: rupees(m["capex"]["community_battery"])),
        ("Annual DISCOM benefits", lambda m: rupees(m["annual"]["benefits_total"])),
        ("Annual operating cost", lambda m: rupees(m["annual"]["opex_total"])),
        ("DISCOM NPV over 10 years", lambda m: rupees(m["discom_npv"])),
        ("Simple payback", lambda m: "does not pay back" if m["simple_payback_years"] is None
         else f"{m['simple_payback_years']:.1f} years"),
        ("Up-front cost to a low-income household", lambda m: rupees(m["household"]["low_income_upfront"])),
        ("Net cost per home per month if spread across the DT", lambda m: rupees(m["net_cost_per_home_per_month"])),
        ("Cost per household-hour of essential supply preserved",
         lambda m: rupees(m["cost_per_household_hour_preserved"]) if m["cost_per_household_hour_preserved"] else "–"),
        ("Same hour from a home inverter the family buys itself",
         lambda m: rupees(m["home_inverter_cost_per_backup_hour"]) if m["home_inverter_cost_per_backup_hour"] else "–"),
        ("Up-front cost per kW of flexibility (utility BESS benchmark)",
         lambda m: f"{rupees(m['capex_per_dfpo_kw'])} ({rupees(m['utility_bess_per_kw'])})"),
        ("Payment to an inverter home per kWh lent (wear + charging loss)",
         lambda m: f"Rs {m['household']['inverter_compensation_rate_per_kwh']:.1f} "
                   f"(Rs {m['household']['inverter_wear_per_kwh']:.1f} + Rs {m['household']['inverter_charging_loss_per_kwh']:.1f})"),
        ("Societal value of lost load avoided per year (not DISCOM cash)",
         lambda m: rupees(m["societal_voll_benefit"]) if m["societal_voll_benefit"] is not None else "–"),
    ]
    for label, fn in rows:
        lines.append(f"| {label} | " + " | ".join(fn(ec["scenarios"][n]["reliability_only"]) for n in names) + " |")
    lines.append("")
    for n, s in ec["scenarios"].items():
        p = s["with_peak_shaving"]
        if s["peak_shaving_policy"]:
            lines.append(f"{SCEN[n]}: if the community battery also shaves the evening peak, using the reserve policy that "
                         f"shaves most while keeping availability within 0.5 points of a fully reserved battery "
                         f"({_model_label(s['peak_shaving_policy'])}), "
                         f"the DISCOM NPV becomes {rupees(p['discom_npv'])} and the net cost per home "
                         f"{rupees(p['net_cost_per_home_per_month'])} per month.")
        else:
            lines.append(f"{SCEN[n]}: no forecast policy shaved the peak while keeping availability within 0.5 points "
                         "of the fully reserved battery, so no peak-shaving value is counted.")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_ownership(res):
    ec = res.get("economics")
    if not ec:
        return "*Not yet computed.*"
    owner = {"A_discom": "DISCOM", "B_community": "Community cooperative / SHG (30% capital grant assumed)",
             "B_community_no_grant": "Community cooperative / SHG, no grant",
             "C_aggregator": "Registered aggregator"}
    lines = []
    for n, s in ec["scenarios"].items():
        lines += [f"**{SCEN[n]}**", "", "| Model | Owner of battery and nodes | Availability fee paid by DISCOM | DISCOM NPV (10 years) |",
                  "|---|---|---:|---:|"]
        for k, m in s["ownership"].items():
            fee = "–" if m["fee_per_kw_month"] is None else f"Rs {m['fee_per_kw_month']:,.0f} per kW-month"
            lines.append(f"| {m['name']} | {owner[k]} | {fee} | {rupees(m['discom_npv'])} |")
        rec = s["ownership"][s["recommended_ownership"]]["name"]
        lines += ["", f"Highest DISCOM NPV without an outside grant: **{rec}**.", ""]
    return "\n".join(lines).rstrip()


def render_tornado(res):
    ec = res.get("economics")
    if not ec:
        return "*Not yet computed.*"
    lines = []
    for n, s in ec["scenarios"].items():
        t = s["tornado"]
        lines += [f"**{SCEN[n]}** (base DISCOM NPV {rupees(t['base_npv'])})", "",
                  "| Input | Low → high | DISCOM NPV at low | DISCOM NPV at high |", "|---|---|---:|---:|"]
        for r in t["rows"][:5]:
            lines.append(f"| `{r['input']}` | {r['low_value']:,} → {r['high_value']:,} | "
                         f"{rupees(r['npv_at_low'])} | {rupees(r['npv_at_high'])} |")
        lines.append("")
    return "\n".join(lines).rstrip()


EXTRA = {
    "forecast_accuracy": render_forecast_accuracy,
    "forecast_decision": render_forecast_decision,
    "economics": render_economics,
    "ownership": render_ownership,
    "tornado": render_tornado,
}


def _lc(name):
    return name[0].lower() + name[1:]


def render_headline(res):
    a = res["annual"]["scenarios"]
    sens = res.get("sensitivity", {}).get("scenarios", {})
    parts = []
    for n, s in a.items():
        b, v = s["baseline"], s["saanjh"]
        parts.append(
            f"On the simulated {_lc(SCEN[n])} ({s['homes']} homes), homes kept their essential supply during "
            f"{v['essential_supply_availability']['mean'] * 100:.0f}% of supply-shortfall time with SAANJH, against "
            f"{b['essential_supply_availability']['mean'] * 100:.0f}% under today's rotational load shedding, and full "
            f"disconnection fell from {b['outage_hours_per_home']['mean']:.0f} to {v['outage_hours_per_home']['mean']:.1f} "
            f"hours per home per year (mean of {res['annual']['seeds']} Monte Carlo runs).")
    nb = []
    for n, rows in sens.items():
        for r in rows.get("community_battery_kwh", []):
            if str(r["value"]) == "0":
                nb.append(f"{r['saanjh']['essential_supply_availability']['mean'] * 100:.0f}% on the {_lc(SCEN[n])}")
    if nb:
        parts.append("Most of the gain comes from the shared community battery: without it, essential-supply "
                     "availability is " + " and ".join(nb) + ".")
    return " ".join(parts)


EXTRA["headline"] = render_headline


def render_readme_results(res):
    a = res["annual"]["scenarios"]
    names = list(a)
    lines = [f"*SIMULATED on inputs calibrated to real data. Mean of {res['annual']['seeds']} Monte Carlo runs over one year "
             "(Lucknow 2023 weather). Full tables, ranges and sensitivity: [docs/WRITEUP.md](docs/WRITEUP.md).*", "",
             "| Metric | " + " | ".join(f"{SCEN[n]}: baseline → SAANJH" for n in names) + " |",
             "|---|" + "---:|" * len(names)]
    rows = [
        ("Essential-supply availability in deficit windows", lambda s, p: f"{s[p]['essential_supply_availability']['mean'] * 100:.0f}%"),
        ("Outage hours per home per year", lambda s, p: f"{s[p]['outage_hours_per_home']['mean']:.1f}"),
        ("Energy not served (kWh/year)", lambda s, p: f"{s[p]['energy_not_served_kwh']['mean']:,.0f}"),
        ("Hours on essential band per home per year", lambda s, p: f"{s[p]['banded_hours_per_home']['mean']:.1f}"),
    ]
    for label, fn in rows:
        lines.append(f"| {label} | " + " | ".join(f"{fn(a[n], 'baseline')} → {fn(a[n], 'saanjh')}" for n in names) + " |")
    ec = res.get("economics", {}).get("scenarios", {})
    if ec:
        lines.append("| Net cost per home per month (DISCOM-owned) | " + " | ".join(
            rupees(ec[n]["reliability_only"]["net_cost_per_home_per_month"]) for n in names) + " |")
        lines.append("| Cost per household-hour of essential supply preserved | " + " | ".join(
            rupees(ec[n]["reliability_only"]["cost_per_household_hour_preserved"]) for n in names) + " |")
    return "\n".join(lines)


EXTRA["readme_results"] = render_readme_results
