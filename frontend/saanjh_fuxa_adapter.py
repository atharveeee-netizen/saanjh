"""
SAANJH Data Adapter for FUXA SCADA/HMI
Maps canonical simulation results and timeseries outputs into the FUXA SCADA data model.
Produces:
  1. frontend/fuxa/server/project.saanjh.fuxap (Official FUXA project file)
  2. docs/data/saanjh_tags.json (Tag namespace registry)
"""

import json
import csv
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DOCS_DATA = os.path.join(BASE_DIR, 'docs', 'data')

def load_canonical_data():
    with open(os.path.join(DOCS_DATA, 'timeseries_bundle.json'), 'r') as f:
        timeseries = json.load(f)
    
    with open(os.path.join(DOCS_DATA, 'comparison.json'), 'r') as f:
        comparison = json.load(f)
        
    with open(os.path.join(DOCS_DATA, 'discom_action_plan.json'), 'r') as f:
        discom = json.load(f)
        
    with open(os.path.join(DOCS_DATA, 'economics_scenarios.json'), 'r') as f:
        economics = json.load(f)

    fleet = []
    with open(os.path.join(DOCS_DATA, 'household_dispatch.csv'), 'r') as f:
        reader = csv.DictReader(f)
        for r in reader:
            fleet.append({
                "id": r["household_id"],
                "has_battery": r["has_battery"].lower() == "true",
                "has_solar": r["has_solar"].lower() == "true",
                "init_soc": float(r["initial_soc"]),
                "final_soc": float(r["final_soc"]),
                "avail_kw": float(r["available_flexibility_kw"]),
                "disp_kw": float(r["dispatched_power_kw"]),
                "delivered_kwh": float(r["energy_delivered_kwh"]),
                "reserve_limit": float(r["reserve_soc_limit"]),
                "participated": r["participated"].lower() == "true",
                "opted_out": r["opted_out"].lower() == "true",
                "comp_inr": float(r["compensation_inr"])
            })

    return timeseries, comparison, discom, economics, fleet

def build_fuxa_project():
    timeseries, comp, discom, econ, fleet = load_canonical_data()
    
    # Peak index = 37 (19:05 IST)
    idx_peak = 37
    active_load = timeseries["saanjh_load"][idx_peak]
    base_load = timeseries["baseline_load"][idx_peak]
    solar_kw = timeseries["solar_gen"][idx_peak]
    tail_volt = timeseries["saanjh_voltage"][idx_peak]
    tx_loading = timeseries["tx_loading_pct"][idx_peak]
    flex_disp = timeseries["flex_delivered"][idx_peak]
    flex_avail = timeseries["flex_available"][idx_peak]
    
    # FUXA Tag Definitions
    tags = {
        "SAANJH/FEEDER/active_power_kw": {
            "name": "active_power_kw",
            "type": "Number",
            "unit": "kW",
            "value": round(active_load, 2),
            "description": "Simulated active feeder demand under SAANJH control"
        },
        "SAANJH/FEEDER/baseline_power_kw": {
            "name": "baseline_power_kw",
            "type": "Number",
            "unit": "kW",
            "value": round(base_load, 2),
            "description": "Baseline unmanaged demand proxy"
        },
        "SAANJH/FEEDER/solar_kw": {
            "name": "solar_kw",
            "type": "Number",
            "unit": "kW",
            "value": round(solar_kw, 2),
            "description": "Feeder solar PV aggregate generation"
        },
        "SAANJH/FEEDER/tail_voltage_v": {
            "name": "tail_voltage_v",
            "type": "Number",
            "unit": "V",
            "value": round(tail_volt, 2),
            "description": "Simulated feeder tail Node 60 RMS voltage"
        },
        "SAANJH/FEEDER/thermal_limit_kw": {
            "name": "thermal_limit_kw",
            "type": "Number",
            "unit": "kW",
            "value": 80.75,
            "description": "Transformer 85% continuous thermal limit"
        },
        "SAANJH/TRANSFORMER/loading_pct": {
            "name": "loading_pct",
            "type": "Number",
            "unit": "%",
            "value": round(tx_loading, 1),
            "description": "Transformer loading percentage against 95 kW nominal rating"
        },
        "SAANJH/TRANSFORMER/rated_kva": {
            "name": "rated_kva",
            "type": "Number",
            "unit": "kVA",
            "value": 100.0,
            "description": "Transformer nameplate capacity rating"
        },
        "SAANJH/TRANSFORMER/stress_minutes": {
            "name": "stress_minutes",
            "type": "Number",
            "unit": "min",
            "value": comp["saanjh_overload_minutes"],
            "description": "Minutes above continuous thermal rating (60m vs 90m base)"
        },
        "SAANJH/FLEX/available_kw": {
            "name": "available_kw",
            "type": "Number",
            "unit": "kW",
            "value": round(flex_avail, 2),
            "description": "Aggregated fleet available discharge headroom"
        },
        "SAANJH/FLEX/dispatched_kw": {
            "name": "dispatched_kw",
            "type": "Number",
            "unit": "kW",
            "value": round(flex_disp, 2),
            "description": "Active flexibility dispatched to shave peak"
        },
        "SAANJH/FLEX/delivered_kwh": {
            "name": "delivered_kwh",
            "type": "Number",
            "unit": "kWh",
            "value": round(comp["flexibility_delivered_kwh"], 2),
            "description": "Total flexibility energy delivered during event"
        },
        "SAANJH/FLEET/participating_homes": {
            "name": "participating_homes",
            "type": "Number",
            "unit": "count",
            "value": comp["homes_participating"],
            "description": "Active participating household BESS inverters"
        },
        "SAANJH/FLEET/battery_homes": {
            "name": "battery_homes",
            "type": "Number",
            "unit": "count",
            "value": 42,
            "description": "Total residential battery storage systems on feeder"
        },
        "SAANJH/FLEET/opted_out": {
            "name": "opted_out",
            "type": "Number",
            "unit": "count",
            "value": 3,
            "description": "Homeowners exercising opt-out preference (H-18, H-55, H-56)"
        },
        "SAANJH/FORECAST/load_kw": {
            "name": "load_kw",
            "type": "Number",
            "unit": "kW",
            "value": round(active_load, 2),
            "description": "XGBoost 45-minute lookahead forecast"
        },
        "SAANJH/FORECAST/error": {
            "name": "error",
            "type": "Number",
            "unit": "RMSE kW",
            "value": 0.546,
            "description": "Model validation error on UCI test series"
        },
        "SAANJH/ECONOMICS/capex_per_kw": {
            "name": "capex_per_kw",
            "type": "Number",
            "unit": "INR/kW",
            "value": comp["cost_per_dependable_kw"],
            "description": "Base prototype scale capital investment per dependable kW"
        },
        "SAANJH/ECONOMICS/household_credit": {
            "name": "household_credit",
            "type": "Number",
            "unit": "INR/kWh",
            "value": 1.50,
            "description": "Incentive credit tariff for flexibility dispatch"
        },
        "SAANJH/EVENTS/solar_cliff": {
            "name": "solar_cliff",
            "type": "String",
            "value": "18:30 IST (-7.5 kW/30m drop)",
            "description": "Forecasted solar PV generation drop-off event"
        },
        "SAANJH/EVENTS/dispatch": {
            "name": "dispatch",
            "type": "String",
            "value": "18:35 - 19:20 IST (45 min duration)",
            "description": "Coordinated flexibility dispatch window"
        },
        "SAANJH/EVENTS/recovery": {
            "name": "recovery",
            "type": "String",
            "value": "20:30 IST (All reserves >= 70%)",
            "description": "Feeder stabilization and reserve preservation window"
        }
    }

    # FUXA Project JSON structure
    fuxa_project = {
        "version": "1.00",
        "name": "SAANJH_EcoStruxure_Grid_SCADA",
        "server": {
            "id": "saanjh_server",
            "name": "SAANJH Edge SCADA Driver",
            "type": "FuxaServer",
            "property": {
                "environment": "SAANJH DIGITAL TWIN SIMULATION / REPLAY",
                "feeder_id": "FDR-023",
                "transformer_id": "DT-100KVA-04"
            }
        },
        "devices": {
            "DEV_SAANJH_EDGE": {
                "name": "SAANJH_EDGE_DISPATCHER",
                "type": "Internal",
                "polling": 1000,
                "tags": tags
            }
        },
        "hmi": {
            "layout": {
                "navigation": {
                    "mode": "top",
                    "items": [
                        {"id": "v_feeder_overview", "name": "FEEDER OVERVIEW"},
                        {"id": "v_trends", "name": "TRENDS & TELEMETRY"},
                        {"id": "v_flex_fleet", "name": "FLEXIBILITY FLEET"},
                        {"id": "v_discom_decision", "name": "DISCOM / DECISION VIEW"}
                    ]
                }
            },
            "views": [
                {
                    "id": "v_feeder_overview",
                    "name": "FEEDER OVERVIEW",
                    "type": "view",
                    "description": "What is happening to Feeder FDR-023 right now?"
                },
                {
                    "id": "v_trends",
                    "name": "TRENDS & TELEMETRY",
                    "type": "view",
                    "description": "Baseline vs SAANJH Demand, Voltage, and Flexibility Curves"
                },
                {
                    "id": "v_flex_fleet",
                    "name": "FLEXIBILITY FLEET",
                    "type": "view",
                    "description": "60-Household Distributed BESS Asset Telemetry"
                },
                {
                    "id": "v_discom_decision",
                    "name": "DISCOM / DECISION VIEW",
                    "type": "view",
                    "description": "DISCOM Operator Action Plan & Economic Sensitivity Analysis"
                }
            ]
        }
    }

    # Save to server project file
    project_path = os.path.join(BASE_DIR, 'frontend', 'fuxa', 'server', 'project.saanjh.fuxap')
    with open(project_path, 'w', encoding='utf-8') as f:
        json.dump(fuxa_project, f, indent=2)
    print(f"Generated {project_path}")

    # Also save tags registry to docs/data/saanjh_tags.json
    tags_path = os.path.join(DOCS_DATA, 'saanjh_tags.json')
    with open(tags_path, 'w', encoding='utf-8') as f:
        json.dump(tags, f, indent=2)
    print(f"Generated {tags_path}")

if __name__ == '__main__':
    build_fuxa_project()
