"""Unit economics and ownership models, computed from simulation outputs.

    python simulation/economics_engine.py

Inputs: config/economics.yaml (every value with a low/base/high range and a source or
ASSUMPTION note) and simulation/results/results.json (energy, hours and cycles from the
year-long runs and the forecast decision-value runs). Nothing here is hardcoded as a
result: paybacks, NPVs and per-household costs are all computed.

Cash-flow conventions (per DT, per year, rupees):
* DISCOM energy-sales gain: energy that baseline load shedding would have left unserved
  but SAANJH serves, sold at the residential tariff.
* Community-battery charging is bought in solar hours; peak shaving avoids evening
  purchases.
* Households that lend their inverter batteries are paid per kWh at least their battery
  wear plus the extra electricity lost in charging (a margin above cost).
* Value of lost load (VoLL) is a societal benefit and is never counted as DISCOM cash.
"""
import copy
import json
import math
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.config import load_config, repo_path

ECON_PATH = repo_path("config", "economics.yaml")
RESULTS = repo_path("simulation", "results", "results.json")
OPERATING_MODES = {
    "reliability_only": "full reserve (no peak shaving)",
    "with_peak_shaving": None,     # filled with the best forecast policy found
}


def load_inputs(case="base", overrides=None):
    with open(ECON_PATH, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    def pick(node):
        if isinstance(node, dict) and "base" in node:
            return node[case] if case in node else node["base"]
        if isinstance(node, dict):
            return {k: pick(v) for k, v in node.items()}
        return node

    vals = pick(raw)
    for path, value in (overrides or {}).items():
        d = vals
        keys = path.split(".")
        for k in keys[:-1]:
            d = d[k]
        d[keys[-1]] = value
    return vals, raw


def annuity(rate, years):
    return rate / (1 - (1 + rate) ** -years) if rate > 0 else 1 / years


def npv(rate, flows):
    return sum(f / (1 + rate) ** t for t, f in enumerate(flows))


def expected_counts(cfg, scenario):
    sc = cfg["scenarios"][scenario]
    n = sc["num_homes"]
    part = cfg.get("participation", {}).get("inverter_relay", 1.0)
    inv = sum(n * share * cfg["segments"][s]["ownership"]["inverter"] for s, share in sc["segment_mix"].items())
    act = sum(n * share * cfg["segments"][s]["ownership"]["actuator"] for s, share in sc["segment_mix"].items())
    return {"homes": n, "inverter_homes": inv, "relay_nodes": inv * part, "actuators": act}


def household_compensation(e, cfg):
    hb, ib = e["household_battery"], cfg["inverter_battery"]
    dod = ib["initial_soc"] - ib["reserve_soc"]
    eta_d = math.sqrt(ib["round_trip_efficiency"])
    wear = hb["battery_price"] / (hb["cycle_life_at_shallow_dod"] * ib["capacity_kwh"] * dod * eta_d)
    charging_loss = e["tariffs"]["residential_tariff_per_kwh"] * (1 / ib["round_trip_efficiency"] - 1)
    return {"wear_per_kwh": wear, "charging_loss_per_kwh": charging_loss,
            "rate_per_kwh": hb["compensation_margin"] * (wear + charging_loss)}


def scenario_economics(res, cfg, scenario, mode="reliability_only", e=None):
    e = e or load_inputs()[0]
    ann = res["annual"]["scenarios"][scenario]
    counts = expected_counts(cfg, scenario)
    cb_cfg = {**cfg["community_battery"], **cfg["scenarios"][scenario].get("community_battery", {})}
    hw, t, op, vs = e["hardware"], e["tariffs"], e["operations"], e["value_streams"]
    r, years = e["general"]["discount_rate"], int(e["general"]["horizon_years"])

    # ---- capex
    battery_pack = cb_cfg["capacity_kwh"] * (hw["lfp_new_pack_per_kwh"] * hw["second_life_share_of_new"]
                                             + hw["repurposing_bms_per_kwh"])
    battery_capex = battery_pack + cb_cfg["power_kw"] * hw["pcs_per_kw"] + hw["enclosure_fire_safety"] \
        + hw["battery_installation_civil"]
    edge_capex = hw["dt_gateway"] + hw["head_end_integration_per_dt"] \
        + counts["relay_nodes"] * hw["relay_node"] + counts["actuators"] * hw["appliance_actuator"] \
        + counts["homes"] * hw["smart_meter_load_limit_per_home"]
    capex = battery_capex + edge_capex

    # ---- simulation outputs (mean over seeds)
    sa, ba = ann["saanjh"], ann["baseline"]
    flex = sa["flexibility"]
    relay_kwh = flex["inverter_relay_kwh"]["mean"]
    cb_out = sa["community_battery"]["discharged_kwh"]["mean"]
    cb_in = sa["community_battery"]["charged_kwh"]["mean"]
    efc = sa["community_battery"]["equivalent_full_cycles"]["mean"]
    unserved_gain = ba["energy_not_served_kwh"]["mean"] - sa["energy_not_served_kwh"]["mean"]
    peak_shaving = 0.0
    availability = sa["essential_supply_availability"]["mean"]
    outage_hours = sa["outage_hours_per_home"]["mean"]
    if mode == "with_peak_shaving":
        dv = res.get("forecast", {}).get("decision_value", {}).get(scenario, {})
        full = dv.get(OPERATING_MODES["reliability_only"])
        policy = best_peak_policy(dv)
        if full and policy:
            p = dv[policy]
            peak_shaving = p["peak_shaving_kwh"]
            # Extra battery throughput and charging for shaving, and the reliability cost,
            # measured as differences against the full-reserve runs on the same seeds.
            extra_out = peak_shaving
            cb_out += extra_out
            cb_in += extra_out / cb_cfg["round_trip_efficiency"]
            efc += p["battery_cycles"] - full["battery_cycles"]
            availability += p["essential_supply_availability"] - full["essential_supply_availability"]
            outage_hours += p["outage_hours_per_home"] - full["outage_hours_per_home"]

    comp = household_compensation(e, cfg)
    # ---- DISCOM annual cash flows
    revenue_sales = unserved_gain * t["residential_tariff_per_kwh"]
    avoided_peak = peak_shaving * t["peak_power_purchase_per_kwh"]
    dfpo_kw = cb_cfg["power_kw"]
    dfpo_value = dfpo_kw * vs["dfpo_value_per_kw_month"] * 12
    dt_deferral = 0.0
    if ba["dt_overload_hours"]["mean"] > 0 and sa["dt_overload_hours"]["mean"] == 0:
        dt_deferral = vs["dt_augmentation_cost"] * r
    benefits = revenue_sales + avoided_peak + dfpo_value + dt_deferral
    charging_cost = cb_in * t["solar_hours_purchase_per_kwh"]
    compensation = relay_kwh * comp["rate_per_kwh"]
    operator = op["local_operator_fee_per_month"] * 12
    technician = op["technician_visits_per_year"] * op["technician_visit_cost"]
    maintenance = op["node_maintenance_share"] * edge_capex + op["battery_om_share"] * battery_capex
    opex = charging_cost + compensation + operator + technician + maintenance + op["communications_per_year"]

    # ---- battery life and replacement
    fade = cb_cfg["fade_per_efc"]
    years_to_eol = (1 - op["battery_end_of_life_capacity"]) / (fade * efc) if efc > 0 else float("inf")
    life = min(op["battery_calendar_life_years"], years_to_eol)
    flows = [-capex] + [benefits - opex] * years
    k = life
    while k < years:
        flows[int(math.ceil(k))] -= battery_capex
        k += life
    discom_npv = npv(r, flows)
    annualised_cost = edge_capex * annuity(r, years) + battery_capex * annuity(r, min(life, years)) + opex
    net_annual = benefits - opex
    payback = capex / net_annual if net_annual > 0 else None

    preserved = ann["essential_household_hours_preserved"]["mean"]
    societal = societal_value(res, scenario, e)
    homes = counts["homes"]
    net_cost_per_year = max(0.0, annualised_cost - benefits)
    return {
        "scenario": scenario, "mode": mode,
        "counts": {k2: round(v, 1) for k2, v in counts.items()},
        "capex": {"community_battery": battery_capex, "edge_and_integration": edge_capex, "total": capex},
        "annual": {
            "benefit_energy_sales": revenue_sales, "benefit_avoided_peak_purchase": avoided_peak,
            "benefit_dfpo": dfpo_value, "benefit_dt_deferral": dt_deferral, "benefits_total": benefits,
            "cost_battery_charging": charging_cost, "cost_household_compensation": compensation,
            "cost_local_operator": operator, "cost_technician": technician, "cost_maintenance": maintenance,
            "cost_communications": op["communications_per_year"], "opex_total": opex,
            "net_cash": net_annual,
        },
        "battery_life_years": life, "battery_equivalent_full_cycles_per_year": efc,
        "discom_npv": discom_npv, "simple_payback_years": payback,
        "annualised_cost": annualised_cost,
        "net_cost_per_home_per_month": net_cost_per_year / homes / 12,
        "cost_per_household_hour_preserved": annualised_cost / preserved if preserved > 0 else None,
        "net_cost_per_household_hour_preserved": net_cost_per_year / preserved if preserved > 0 else None,
        "household_hours_preserved": preserved,
        "capex_per_dfpo_kw": capex / dfpo_kw if dfpo_kw else None,
        "home_inverter_cost_per_backup_hour": home_inverter_benchmark(e, ba["outage_hours_per_home"]["mean"]),
        "utility_bess_per_kw": e["benchmarks"]["utility_bess_per_kw"],
        "essential_supply_availability": availability, "outage_hours_per_home": outage_hours,
        "peak_shaving_kwh": peak_shaving,
        "household": {
            "low_income_upfront": 0.0, "low_income_monthly_charge": 0.0,
            "inverter_compensation_rate_per_kwh": comp["rate_per_kwh"],
            "inverter_wear_per_kwh": comp["wear_per_kwh"],
            "inverter_charging_loss_per_kwh": comp["charging_loss_per_kwh"],
            "inverter_home_annual_payment": compensation / counts["relay_nodes"] if counts["relay_nodes"] else 0.0,
            "inverter_home_annual_net": (compensation - relay_kwh * (comp["wear_per_kwh"] + comp["charging_loss_per_kwh"]))
            / counts["relay_nodes"] if counts["relay_nodes"] else 0.0,
        },
        "local_operator": {"annual_fee": operator, "monthly_fee": op["local_operator_fee_per_month"]},
        "societal_voll_benefit": societal,
    }


def home_inverter_benchmark(e, outage_hours):
    """What one household pays per hour of backup if it buys its own inverter and battery
    to ride through the baseline outage hours (charging energy ignored, so a lower bound)."""
    b = e["benchmarks"]
    kit, life = b["home_inverter_kit"], b["home_inverter_battery_life_years"]
    yearly = kit * annuity(e["general"]["discount_rate"], life)
    return yearly / outage_hours if outage_hours > 0 else None


def best_peak_policy(dv):
    """Reserve policy (fixed or forecast-based) with the most peak shaving whose
    availability is within 0.5 percentage points of the full-reserve runs; None if none."""
    full = dv.get(OPERATING_MODES["reliability_only"])
    if not full:
        return None
    ok = [(p, v) for p, v in dv.items() if p != OPERATING_MODES["reliability_only"]
          and v["essential_supply_availability"] >= full["essential_supply_availability"] - 0.005]
    if not ok:
        return None
    return max(ok, key=lambda pv: pv[1]["peak_shaving_kwh"])[0]


def societal_value(res, scenario, e):
    """VoLL x reduction in unserved energy, split by segment using seed-0 per-home tables."""
    import pandas as pd
    base = repo_path("simulation", "results", "annual", f"{scenario}_baseline_homes.csv")
    sa = repo_path("simulation", "results", "annual", f"{scenario}_saanjh_homes.csv")
    if not (os.path.exists(base) and os.path.exists(sa)):
        return None
    b, s = pd.read_csv(base), pd.read_csv(sa)
    total = 0.0
    for seg in b["segment"].unique():
        d = b.loc[b.segment == seg, "unserved_kwh"].sum() - s.loc[s.segment == seg, "unserved_kwh"].sum()
        total += d * e["value_streams"]["voll_per_kwh"][seg]
    return total


OWNERSHIP = {
    "A_discom": {"name": "A. DISCOM-owned", "owner_discount_rate": None},
    "B_community": {"name": "B. Community-owned (RWA / cooperative / SHG)", "owner_discount_rate": 0.12,
                    "grant_share": 0.3},
    "B_community_no_grant": {"name": "B'. Community-owned, no grant", "owner_discount_rate": 0.12,
                             "grant_share": 0.0},
    "C_aggregator": {"name": "C. Third-party aggregator", "owner_discount_rate": 0.15, "grant_share": 0.0},
}


def recommended_model(models):
    """Highest DISCOM NPV among models that need no outside grant."""
    fair = {k: v for k, v in models.items() if v.get("grant_share", 0.0) == 0.0}
    return max(fair, key=lambda k: fair[k]["discom_npv"])


def ownership_models(base_econ, e):
    """Cash flows under three ownership models for one scenario's base economics.

    In B and C the owner buys the battery and nodes and runs the service; the DISCOM pays
    an availability fee per kW-month plus the household compensation pass-through. The fee
    is set so the owner earns its required return (NPV = 0 at its discount rate).
    B may receive a capital grant (e.g. a state or CSR scheme) [ASSUMPTION grant_share].
    """
    years = int(e["general"]["horizon_years"])
    r_d = e["general"]["discount_rate"]
    kw = base_econ["capex"]["total"] / base_econ["capex_per_dfpo_kw"]
    a = base_econ["annual"]
    discom_benefit = a["benefits_total"]
    owner_opex = a["opex_total"]
    out = {}
    for key, m in OWNERSHIP.items():
        if key == "A_discom":
            out[key] = {"name": m["name"], "owner": "DISCOM", "discom_npv": base_econ["discom_npv"],
                        "fee_per_kw_month": None, "owner_npv": base_econ["discom_npv"]}
            continue
        r_o = m["owner_discount_rate"]
        capex = base_econ["capex"]["total"] * (1 - m["grant_share"])
        # Owner pays capex (net of any grant), yearly opex and battery replacements, exactly
        # as the DISCOM would in model A. The DISCOM pays a level fee F per kW-month set so
        # the owner's NPV is zero at its own discount rate.
        cost = [capex] + [owner_opex] * years
        life = base_econ["battery_life_years"]
        k = life
        while k < years:
            cost[int(math.ceil(k))] += base_econ["capex"]["community_battery"]
            k += life
        need = npv(r_o, cost) * annuity(r_o, years)
        fee = need / (kw * 12)
        discom_flows = [0.0] + [discom_benefit - fee * kw * 12] * years
        out[key] = {"name": m["name"], "owner": m["name"].split(". ", 1)[1], "fee_per_kw_month": fee,
                    "discom_npv": npv(r_d, discom_flows), "owner_npv": 0.0,
                    "owner_discount_rate": r_o, "grant_share": m["grant_share"]}
    return out


TORNADO_INPUTS = [
    "hardware.lfp_new_pack_per_kwh", "hardware.second_life_share_of_new", "hardware.pcs_per_kw",
    "hardware.enclosure_fire_safety", "hardware.battery_installation_civil", "hardware.relay_node",
    "tariffs.residential_tariff_per_kwh", "tariffs.solar_hours_purchase_per_kwh",
    "tariffs.peak_power_purchase_per_kwh", "value_streams.dfpo_value_per_kw_month",
    "operations.local_operator_fee_per_month", "operations.battery_calendar_life_years",
    "household_battery.cycle_life_at_shallow_dod", "general.discount_rate",
]


def tornado(res, cfg, scenario, mode):
    base_vals, raw = load_inputs()
    base = scenario_economics(res, cfg, scenario, mode, base_vals)["discom_npv"]
    rows = []
    for path in TORNADO_INPUTS:
        node = raw
        for k in path.split("."):
            node = node[k]
        out = {}
        for case in ("low", "high"):
            vals = copy.deepcopy(base_vals)
            d = vals
            ks = path.split(".")
            for k in ks[:-1]:
                d = d[k]
            d[ks[-1]] = node[case]
            out[case] = scenario_economics(res, cfg, scenario, mode, vals)["discom_npv"]
        rows.append({"input": path, "low_value": node["low"], "high_value": node["high"],
                     "npv_at_low": out["low"], "npv_at_high": out["high"],
                     "swing": abs(out["high"] - out["low"]), "note": node.get("note", "")})
    rows.sort(key=lambda x: -x["swing"])
    return {"base_npv": base, "rows": rows}


def run_all():
    with open(RESULTS, "r", encoding="utf-8") as f:
        res = json.load(f)
    cfg = load_config()
    e, raw = load_inputs()
    out = {"label": "Computed from config/economics.yaml and simulation results", "scenarios": {}}
    for name in res["annual"]["scenarios"]:
        modes = {}
        for mode in ("reliability_only", "with_peak_shaving"):
            modes[mode] = scenario_economics(res, cfg, name, mode, e)
        dv = res.get("forecast", {}).get("decision_value", {}).get(name, {})
        out["scenarios"][name] = {
            **modes,
            "peak_shaving_policy": best_peak_policy(dv),
            "ownership": ownership_models(modes["reliability_only"], e),
            "recommended_ownership": recommended_model(ownership_models(modes["reliability_only"], e)),
            "tornado": tornado(res, cfg, name, "reliability_only"),
        }
    res["economics"] = out
    with open(RESULTS, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    return out


if __name__ == "__main__":
    out = run_all()
    for name, s in out["scenarios"].items():
        m = s["reliability_only"]
        print(f"\n{name}: capex Rs {m['capex']['total']:,.0f}, benefits Rs {m['annual']['benefits_total']:,.0f}/yr, "
              f"opex Rs {m['annual']['opex_total']:,.0f}/yr, NPV Rs {m['discom_npv']:,.0f}, "
              f"net cost per home Rs {m['net_cost_per_home_per_month']:.0f}/month, "
              f"Rs {m['cost_per_household_hour_preserved']:.1f} per household-hour preserved")
        p = s["with_peak_shaving"]
        print(f"  with peak shaving ({s['peak_shaving_policy']}): NPV Rs {p['discom_npv']:,.0f}, "
              f"net cost per home Rs {p['net_cost_per_home_per_month']:.0f}/month")
        for k, v in s["ownership"].items():
            print(f"  {v['name']}: DISCOM NPV Rs {v['discom_npv']:,.0f}"
                  + (f", fee Rs {v['fee_per_kw_month']:,.0f}/kW-month" if v["fee_per_kw_month"] else ""))
        for row in s["tornado"]["rows"][:5]:
            print(f"  tornado {row['input']}: {row['npv_at_low']:,.0f} .. {row['npv_at_high']:,.0f}")
