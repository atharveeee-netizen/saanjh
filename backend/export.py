"""Build the replay data served by the API and bundled into the static UI.

    python backend/export.py

Reads the year-long results and re-runs seed 0 of each scenario for a handful of replay
days, recording per-phase load and running a PyPSA power flow for tail-end voltage.
Writes backend/data/ and copies it to ui/public/data/ (for the static build).
All values are SIMULATED; identifiers are anonymised demo IDs.
"""
import json
import math
import os
import shutil
import sys
from datetime import date as Date

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from simulation.config import load_config
from simulation.economics_engine import household_compensation, load_inputs
from simulation.engine import Scenario, run
from simulation.validators.pypsa_validator import run_power_flow

OUT = os.path.join(ROOT, "backend", "data")
UI_DATA = os.path.join(ROOT, "ui", "public", "data")
RES = os.path.join(ROOT, "simulation", "results")
LABEL = "SIMULATED on inputs calibrated to real data"

DTS = {
    "peri_urban_low_income": {
        "id": "DT-0423", "name": "DT-0423, 100 kVA", "location_label": "Peri-urban ward, Lucknow district",
        "feeder_11kv": "FDR-11kV-07", "circle": "Demo Circle", "division": "Division 2",
        "subdivision": "Sub-division 4"},
    "mixed_urban": {
        "id": "DT-0187", "name": "DT-0187, 100 kVA", "location_label": "Urban ward, Lucknow",
        "feeder_11kv": "FDR-11kV-12", "circle": "Demo Circle", "division": "Division 2",
        "subdivision": "Sub-division 4"},
}
SEG = {"low_income": "Low-income", "middle": "Middle", "affluent": "Affluent"}


def r1(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), 1)


def pick_days(ts_s, n_events=8):
    """Replay days: the deepest shortfall evenings across seasons, a heatwave and a calm day."""
    ts = ts_s.copy()
    ts["deficit_kwh"] = ts["unmanaged_gap_kw"].clip(lower=0) * 0.25
    daily = ts.groupby(["day", "date", "season", "day_type"])["deficit_kwh"].sum().reset_index()
    chosen = []
    for season in ["summer", "monsoon", "post_monsoon", "winter", "spring"]:
        g = daily[(daily.season == season) & (daily.deficit_kwh > 0)].sort_values("deficit_kwh")
        if len(g):
            chosen.append(int(g.iloc[int(len(g) * 0.85)]["day"]))
            if len(g) > 4:
                chosen.append(int(g.iloc[len(g) // 2]["day"]))
    calm = daily[daily.deficit_kwh == 0]
    if len(calm):
        chosen.append(int(calm.iloc[len(calm) // 2]["day"]))
    hw = daily[(daily.day_type == "heatwave") & (daily.deficit_kwh > 0)]
    if len(hw):
        chosen.append(int(hw.sort_values("deficit_kwh").iloc[-1]["day"]))
    chosen = sorted(set(chosen))[: n_events + 2]
    # The featured day: the post-monsoon event used in the README figure if present.
    feat = daily[daily.day.isin(chosen) & (daily.deficit_kwh > 0)]
    featured = int(feat.sort_values("deficit_kwh").iloc[int(len(feat) * 0.7)]["day"]) if len(feat) else chosen[0]
    return chosen, featured, daily.set_index("day")


def forecasts_for(scenario):
    path = os.path.join(ROOT, "ai_forecasting", "forecasts", f"{scenario}_seed0.json")
    if not os.path.exists(path):
        return {}, None
    with open(path, encoding="utf-8") as f:
        fc = json.load(f)
    model = "chronos2" if "chronos2" in fc else ("xgboost_quantile" if "xgboost_quantile" in fc else next(iter(fc)))
    return fc[model], model


def export_dt(scenario, meta_dt, econ_rate):
    cfg = load_config()
    sc = Scenario(scenario, 0)
    ts_s = pd.read_csv(os.path.join(RES, "timeseries", f"{scenario}_saanjh.csv"))
    ts_b = pd.read_csv(os.path.join(RES, "timeseries", f"{scenario}_baseline.csv"))
    days, featured, daily = pick_days(ts_s)
    r_s = run(sc, "saanjh", record_days=days)
    r_b = run(sc, "baseline", record_days=days)
    fc, fc_model = forecasts_for(scenario)
    with open(os.path.join(RES, "annual", f"{scenario}_events.json"), encoding="utf-8") as f:
        events_raw = [e for e in json.load(f) if e.get("kind") == "event"]
    dt_id = meta_dt["id"]
    num = dt_id.split("-")[1]
    out_dir = os.path.join(OUT, f"dt_{dt_id}")
    os.makedirs(out_dir, exist_ok=True)

    # ---------------- events with measurement and verification against the baseline
    events = []
    cb_max = cfg["community_battery"]["capacity_kwh"]
    for i, e in enumerate(events_raw):
        d = Date.fromisoformat(e["date"])
        day_idx = (d - sc.dates[0]).days
        h0, m0 = map(int, e["start"].split(":"))
        h1, m1 = map(int, e["end"].split(":")) if e["end"] != "24:00" else (24, 0)
        b0, b1 = (h0 * 60 + m0) // 15, (h1 * 60 + m1) // 15
        bs = ts_b[ts_b.day == day_idx].iloc[b0:b1]
        ss = ts_s[ts_s.day == day_idx].iloc[b0:b1]
        base_outage = float(bs["homes_shed"].sum() * 15)
        saanjh_outage = float(ss["homes_shed"].sum() * 15)
        deficit = ss["unmanaged_gap_kw"].clip(lower=0)
        events.append({
            "id": f"EV-{num}-{d:%m%d}-{h0:02d}{m0:02d}",
            "dt_id": dt_id, "date": e["date"], "start": e["start"], "end": e["end"],
            "duration_min": int(e["blocks"] * 15), "status": "planned",
            "peak_gap_kw": r1(e["peak_gap_kw"]),
            "plan": {"battery_kwh": r1(e["battery_kwh"]), "relay_kwh": r1(e["relay_kwh"]),
                     "appliance_kwh": r1(e["appliance_kwh"]), "lowest_band_w": e.get("lowest_band_w"),
                     "homes_banded_max": e["homes_banded_max"], "homes_shed_max": e["homes_shed_max"]},
            "mv": {
                "baseline_outage_home_minutes": base_outage, "saanjh_outage_home_minutes": saanjh_outage,
                "outage_minutes_avoided": base_outage - saanjh_outage,
                "deficit_kwh": r1(deficit.sum() * 0.25),
                "battery_kwh": r1(e["battery_kwh"]),
                "dfpo_kwh": r1(e["relay_kwh"] + e["appliance_kwh"] + float(ss["band_curtailed_kw"].sum() * 0.25)),
                "essential_supply_pct": r1(100 * (1 - ss["homes_shed"].sum() / max(1, len(ss) * sc.fleet.n))),
                "baseline_essential_supply_pct": r1(100 * (1 - bs["homes_shed"].sum() / max(1, len(bs) * sc.fleet.n))),
            },
            "decision_log": [{"time": x["time"] + " IST", "by": "SAANJH gateway", "kind": "automatic",
                              "text": x["text"]} for x in e["entries"]],
        })
    events.sort(key=lambda x: (x["date"], x["start"]))
    by_block = {}
    for ev in events:
        d = Date.fromisoformat(ev["date"])
        day_idx = (d - sc.dates[0]).days
        h0, m0 = map(int, ev["start"].split(":"))
        h1, m1 = map(int, ev["end"].split(":")) if ev["end"] != "24:00" else (24, 0)
        for b in range((h0 * 60 + m0) // 15, (h1 * 60 + m1) // 15):
            by_block[(day_idx, b)] = ev["id"]

    # ---------------- replay days
    v_nom = cfg["electrical"]["voltage_nominal_v"]
    day_list = []
    for di in days:
        s = r_s.timeseries[r_s.timeseries.day == di].reset_index(drop=True)
        b = r_b.timeseries[r_b.timeseries.day == di].reset_index(drop=True)
        pf = run_power_flow(s["net_kw"].clip(lower=0), cfg)
        pfb = run_power_flow(b["net_kw"].clip(lower=0), cfg)
        f = fc.get(str(di))
        blocks = []
        for t in range(len(s)):
            row = s.iloc[t]
            phase_kw = [row["phase_r_kw"], row["phase_y_kw"], row["phase_b_kw"]]
            blocks.append({
                "t": t, "time": f"{t // 4:02d}:{t % 4 * 15:02d}",
                "demand_kw": r1(row["demand_kw"]), "pv_kw": r1(row["pv_kw"]),
                "allocation_kw": r1(row["allocation_kw"]) if row["cut_fraction"] > 0 else None,
                "cut_pct": r1(row["cut_fraction"] * 100),
                "net_kw": r1(row["net_kw"]), "baseline_net_kw": r1(b.iloc[t]["net_kw"]),
                "loading_pct": r1(row["loading_pct"]),
                "phase_a": [r1(max(0.0, p) * 1000 / v_nom) for p in phase_kw],
                "tail_voltage_v": r1(pf["voltage_v"].iloc[t]),
                "baseline_tail_voltage_v": r1(pfb["voltage_v"].iloc[t]),
                "battery_kw": r1(row["battery_kw"]), "battery_soc_pct": r1(row["battery_soc"] * 100),
                "relay_kw": r1(row["relay_kw"]), "appliance_kw": r1(row["appliance_reduction_kw"]),
                "recharge_kw": r1(row["recharge_kw"]), "rebound_kw": r1(row["rebound_kw"]),
                "band_level_w": None if pd.isna(row["band_level_w"]) else int(row["band_level_w"]),
                "homes_banded": int(row["homes_banded"]), "homes_shed": int(row["homes_shed"]),
                "baseline_homes_shed": int(b.iloc[t]["homes_shed"]),
                "event_id": by_block.get((di, t)),
                "feeder_kw": [r1(row[f"feeder_{k + 1}_kw"]) for k in range(sc.fleet.n_lt_feeders)],
                "feeder_banded": [int(row[f"feeder_{k + 1}_banded"]) for k in range(sc.fleet.n_lt_feeders)],
                "feeder_shed": [int(row[f"feeder_{k + 1}_shed"]) for k in range(sc.fleet.n_lt_feeders)],
                "forecast_p10_kw": r1(f["demand_q"][0][t]) if f else None,
                "forecast_p50_kw": r1(f["demand_q"][1][t]) if f else None,
                "forecast_p90_kw": r1(f["demand_q"][2][t]) if f else None,
                "deficit_p50_kw": r1(f["block_p50"][t]) if f else None,
                "deficit_p90_kw": r1(f["block_p90"][t]) if f else None,
            })
        date = str(s["date"].iloc[0])
        info = daily.loc[di]
        forecast = {"model": fc_model, "available": bool(f),
                    "evening_deficit_kwh": {k: r1(v) for k, v in f["window_kwh_q"].items()} if f else None,
                    "plan": plan_text(f, cb_max, cfg) if f else None}
        with open(os.path.join(out_dir, f"day_{date}.json"), "w", encoding="utf-8") as fh:
            json.dump({"dt_id": dt_id, "date": date, "day_type": info["day_type"], "season": info["season"],
                       "homes": sc.fleet.n, "label": LABEL, "blocks": blocks, "forecast": forecast}, fh)
        day_list.append({"date": date, "day_type": info["day_type"], "season": info["season"],
                         "deficit_kwh": r1(info["deficit_kwh"]), "featured": di == featured,
                         "events": sorted({e for (d_, _), e in by_block.items() if d_ == di})})

    with open(os.path.join(out_dir, "days.json"), "w", encoding="utf-8") as fh:
        json.dump(day_list, fh, indent=1)
    with open(os.path.join(out_dir, "events.json"), "w", encoding="utf-8") as fh:
        json.dump(events, fh)

    # ---------------- households
    hs = pd.read_csv(os.path.join(RES, "annual", f"{scenario}_saanjh_homes.csv"))
    hb = pd.read_csv(os.path.join(RES, "annual", f"{scenario}_baseline_homes.csv"))
    fleet = sc.fleet
    band = cfg["essential_band"]
    rows = []
    for i in range(fleet.n):
        flex = "inverter relay" if fleet.relay_enrolled[i] else ("appliance" if fleet.has_actuator[i] else "none")
        rows.append({
            "id": f"HH-{num}-{i + 1:03d}", "segment": SEG[fleet.segment[i]], "lt_feeder": int(fleet.feeder[i] + 1),
            "phase": "RYB"[int(fleet.phase[i])],
            "enrolment": "opted out" if fleet.opted_out[i] else "enrolled",
            "flexibility": flex, "has_inverter": bool(fleet.has_inverter[i]), "has_pv": bool(fleet.has_pv[i]),
            "critical": bool(fleet.critical[i]),
            "band_w": int(band["critical_band_w"] if fleet.critical[i] else band["band_w"]),
            "outage_hours_year": r1(hs.loc[i, "shed_blocks"] * 0.25),
            "baseline_outage_hours_year": r1(hb.loc[i, "shed_blocks"] * 0.25),
            "banded_hours_year": r1(hs.loc[i, "banded_blocks"] * 0.25),
            "curtailment_minutes_year": int((hs.loc[i, "shed_blocks"] + hs.loc[i, "banded_blocks"]) * 15),
            "battery_kwh_lent_year": r1(hs.loc[i, "relay_kwh"]),
            "credits_year_rs": r1(hs.loc[i, "relay_kwh"] * econ_rate),
            "consent": {"recorded": not fleet.opted_out[i], "method": "read aloud by local operator, recorded",
                        "language": ["Hindi", "Hindi", "English"][i % 3], "label": "SIMULATED demo record"},
        })
    with open(os.path.join(out_dir, "households.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh)

    # Per-home demand profile on the featured day (for the household drawer).
    _, _, loads, pvk, _ = sc.day_inputs(featured)
    s = r_s.timeseries[r_s.timeseries.day == featured]
    profiles = {"date": str(sc.dates[featured]),
                "band_w_by_block": [None if pd.isna(x) else int(x) for x in s["band_level_w"]],
                "homes": {f"HH-{num}-{i + 1:03d}": [round(float(x) * 1000) for x in loads.total[i]]
                          for i in range(fleet.n)}}
    with open(os.path.join(out_dir, "household_profiles.json"), "w", encoding="utf-8") as fh:
        json.dump(profiles, fh)

    # ---------------- monthly report
    mb = pd.read_csv(os.path.join(RES, "annual", f"{scenario}_baseline_monthly.csv"))
    ms = pd.read_csv(os.path.join(RES, "annual", f"{scenario}_saanjh_monthly.csv"))
    ts_s["month"] = pd.to_datetime(ts_s["date"]).dt.month
    flex_m = ts_s.groupby("month").apply(lambda g: float(((g["relay_kw"] + g["appliance_reduction_kw"]
                                                           + g["band_curtailed_kw"]) * 0.25).sum()),
                                         include_groups=False)
    batt_m = ts_s.groupby("month").apply(lambda g: float((g["battery_kw"].clip(lower=0) * 0.25).sum()),
                                         include_groups=False)
    report = []
    for _, row in ms.iterrows():
        m = int(row["month"])
        base = mb[mb.month == m].iloc[0]
        report.append({"month": m, "deficit_hours": r1(row["deficit_hours"]),
                       "baseline_outage_hours_per_home": r1(base["outage_hours_per_home"]),
                       "saanjh_outage_hours_per_home": r1(row["outage_hours_per_home"]),
                       "banded_home_hours": r1(row["banded_home_hours"]),
                       "demand_flexibility_kwh": r1(flex_m.get(m, 0.0)),
                       "community_battery_kwh": r1(batt_m.get(m, 0.0))})
    with open(os.path.join(out_dir, "reports.json"), "w", encoding="utf-8") as fh:
        json.dump({"dt_id": dt_id, "year": cfg["site"]["year"], "label": LABEL, "months": report}, fh, indent=1)

    homes_by_seg = {SEG[k]: int(v) for k, v in pd.Series(fleet.segment).value_counts().items()}
    dt = {**meta_dt, "rating_kva": float(cfg["scenarios"][scenario]["transformer_kva"]), "homes": fleet.n,
          "homes_by_segment": homes_by_seg, "lt_feeders": fleet.n_lt_feeders, "scenario": scenario, "label": LABEL}
    return dt, events


def plan_text(f, cb_kwh, cfg):
    q = f["window_kwh_q"]
    usable = (cfg["community_battery"]["soc_max"] - cfg["community_battery"]["soc_min"]) * cb_kwh
    reserve = min(usable, q["0.9"] if "0.9" in q else q[0.9])
    return [
        {"step": "Pre-charge community battery in solar hours", "detail": f"to {cfg['community_battery']['soc_max'] * 100:.0f}% (09:00–16:00)"},
        {"step": "Keep battery reserve for the evening", "detail": f"{reserve:.0f} kWh (P90 of forecast evening deficit)"},
        {"step": "If a shortfall is ordered", "detail": "hold appliance rebound, open inverter relays, then discharge the battery"},
        {"step": "If the gap remains", "detail": "apply the gentlest essential band that closes it (1,000 → 750 → 500 W)"},
        {"step": "Expected disconnections", "detail": "none unless the shortfall exceeds the P90 forecast"},
    ]


def protocol_samples(event):
    """Example payloads SAANJH would exchange with a DISCOM ADMS/DERMS (illustrative)."""
    start = f"{event['date']}T{event['start']}:00+05:30"
    return {
        "label": "Illustrative payloads in the style of OpenADR 2.0b and IEEE 2030.5; not certified implementations.",
        "openadr_event": {
            "eiEvent": {
                "eventDescriptor": {"eventID": event["id"], "modificationNumber": 0, "priority": 1,
                                    "marketContext": "http://demo-discom.example/dfpo",
                                    "eventStatus": "far", "createdDateTime": f"{event['date']}T12:00:00+05:30"},
                "eiActivePeriod": {"properties": {"dtstart": {"date-time": start},
                                                  "duration": {"duration": f"PT{event['duration_min']}M"}}},
                "eiEventSignals": {"eiEventSignal": [{
                    "signalName": "LOAD_DISPATCH", "signalType": "delta", "signalID": "SIG-1",
                    "currentValue": {"payloadFloat": {"value": event["peak_gap_kw"]}},
                    "itemBase": {"itemDescription": "RealPower", "itemUnits": "W", "siScaleCode": "k"}}]},
                "eiTarget": {"resourceID": [event["dt_id"]]},
            }
        },
        "ieee2030_5_dercontrol": {
            "DERControl": {
                "mRID": event["id"].replace("-", ""), "description": f"SAANJH essential band for {event['dt_id']}",
                "interval": {"start": start, "duration": event["duration_min"] * 60},
                "DERControlBase": {"opModMaxLimW": {"value": 500, "multiplier": 0},
                                   "opModConnect": True},
                "randomizeStart": 120, "randomizeDuration": 0,
            }
        },
        "flexibility_report": {
            "dt_id": event["dt_id"], "event_id": event["id"],
            "delivered_kwh": event["mv"]["dfpo_kwh"], "battery_kwh": event["mv"]["battery_kwh"],
            "outage_minutes_avoided": event["mv"]["outage_minutes_avoided"],
        },
    }


FLEET_EXTRA = {"peri_urban_low_income": ["DT-0431", "DT-0452"], "mixed_urban": ["DT-0192", "DT-0205"]}


def export_fleet(featured_date):
    """Transformers in the sub-division ranked by the next day's deficit risk.
    Seed 0 of each scenario is the DT shown in full; seeds 1-2 stand in for neighbouring
    DTs of the same type (forecast only). Forecast: seasonal-naive demand quantiles turned
    into a deficit forecast with the shortfall-risk model."""
    from ai_forecasting.dataset import build_series
    from ai_forecasting.deficit_forecast import deficit_quantiles
    from ai_forecasting.models import SeasonalNaive
    mc = pd.read_csv(os.path.join(RES, "montecarlo.csv"))
    cfg = load_config()
    rows = []
    for scenario, meta in DTS.items():
        ids = [meta["id"]] + FLEET_EXTRA[scenario]
        for seed, dt_id in enumerate(ids):
            sc = Scenario(scenario, seed)
            day = next(i for i, d in enumerate(sc.dates) if str(d) == featured_date)
            df = build_series(scenario, seed, sc)
            q = np.maximum(SeasonalNaive().forecast(df, day), 0)
            solar = df["solar"].to_numpy()[day * 96:(day + 1) * 96]
            dq = deficit_quantiles(sc.alloc, q, solar, float(df["cloudiness"].iloc[day * 96]), seed=seed, day=day)
            m = mc[(mc.scenario == scenario) & (mc.seed == seed) & (mc.policy == "saanjh")]
            mix = cfg["scenarios"][scenario]["segment_mix"]
            rows.append({
                "dt_id": dt_id, "name": f"{dt_id}, 100 kVA", "location_label": meta["location_label"],
                "homes": sc.fleet.n, "rating_kva": float(cfg["scenarios"][scenario]["transformer_kva"]),
                "segment_mix": ", ".join(f"{SEG[k]} {int(v * 100)}%" for k, v in mix.items()),
                "risk_p90_kwh": r1(dq["window_kwh_q"][0.9]), "risk_p50_kwh": r1(dq["window_kwh_q"][0.5]),
                "p_any": round(dq["p_any_deficit"], 2), "forecast_p50": [r1(x) for x in q[1][::4]],
                "drillable": seed == 0,
                "outage_hours_year": r1(float(m["outage_hours_per_home"].iloc[0])) if len(m) else None,
            })
    with open(os.path.join(OUT, "fleet.json"), "w", encoding="utf-8") as fh:
        json.dump({"date": featured_date, "label": LABEL, "rows": rows}, fh, indent=1)


def main():
    os.makedirs(OUT, exist_ok=True)
    e, _ = load_inputs()
    rate = household_compensation(e, load_config())["rate_per_kwh"]
    dts, all_events = [], []
    for scenario, meta_dt in DTS.items():
        dt, events = export_dt(scenario, meta_dt, rate)
        dts.append(dt)
        all_events += events
        print(f"{dt['id']}: {len(events)} events")
    with open(os.path.join(OUT, "dts.json"), "w", encoding="utf-8") as fh:
        json.dump(dts, fh, indent=1)
    with open(os.path.join(OUT, "dt_DT-0423", "days.json"), encoding="utf-8") as fh:
        featured = next(d["date"] for d in json.load(fh) if d["featured"])
    export_fleet(featured)
    sample_ev = max((ev for ev in all_events if ev["dt_id"] == "DT-0423"), key=lambda ev: ev["peak_gap_kw"] or 0)
    with open(os.path.join(OUT, "protocol_samples.json"), "w", encoding="utf-8") as fh:
        json.dump(protocol_samples(sample_ev), fh, indent=1)
    with open(os.path.join(RES, "results.json"), encoding="utf-8") as fh:
        res = json.load(fh)
    meta = {"label": LABEL, "generated_from": "simulation/results/results.json",
            "annual": res.get("annual"), "economics": res.get("economics"),
            "forecast": {k: v for k, v in res.get("forecast", {}).items() if k != "label"},
            "sensitivity": res.get("sensitivity"),
            "compensation_rate_per_kwh": rate}
    with open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh)
    if os.path.isdir(os.path.join(ROOT, "ui")):
        if os.path.exists(UI_DATA):
            shutil.rmtree(UI_DATA)
        shutil.copytree(OUT, UI_DATA)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
