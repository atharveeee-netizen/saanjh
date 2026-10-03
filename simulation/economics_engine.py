import os
import json
import pandas as pd

def calculate_economics(peak_reduction_kw, num_participating_homes):
    """
    Computes multi-stakeholder illustrative unit economics across Low, Base, and High scenarios.
    Explicitly distinguishes engineering assumptions from measured hardware costs.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    results_dir = os.path.join(base_dir, 'simulation', 'data', 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    # Measured Prototype Hardware BOM (Base)
    measured_node_bom = 2999 + 1639 + 1019 + 162 + 455 + 799 # ₹7,073 (WisBlock + Sensors)
    measured_gateway_bom = 11275 + 2999 + 1639 + 2809 + 2139 + 299 + 540 + 720 # ₹22,420 (CM4 + LoRa HAT)
    
    scenarios = {
        "LOW_COST_MASS_PRODUCTION": {
            "node_capex": 3500, # Bulk PCB + SMD assembly
            "gateway_capex": 12000,
            "installation_per_home": 300,
            "annual_maintenance_pct": 0.03,
            "discom_tariff_savings_per_kwh": 3.0,
            "household_incentive_per_kwh": 1.5,
            "annual_dispatched_hours": 120
        },
        "BASE_PROTOTYPE_SCALE": {
            "node_capex": measured_node_bom, # ₹7,073
            "gateway_capex": measured_gateway_bom, # ₹22,420
            "installation_per_home": 500,
            "annual_maintenance_pct": 0.05,
            "discom_tariff_savings_per_kwh": 2.5,
            "household_incentive_per_kwh": 1.5,
            "annual_dispatched_hours": 90
        },
        "HIGH_CONTINGENCY": {
            "node_capex": 9500,
            "gateway_capex": 28000,
            "installation_per_home": 1000,
            "annual_maintenance_pct": 0.08,
            "discom_tariff_savings_per_kwh": 2.0,
            "household_incentive_per_kwh": 1.2,
            "annual_dispatched_hours": 60
        }
    }
    
    scenario_results = {}
    table_rows = []
    
    for s_name, s in scenarios.items():
        total_capex = s["gateway_capex"] + (s["node_capex"] * num_participating_homes)
        total_installation = s["installation_per_home"] * num_participating_homes
        total_initial_investment = total_capex + total_installation
        
        annual_maintenance = total_capex * s["annual_maintenance_pct"]
        cost_per_dependable_kw = total_initial_investment / peak_reduction_kw if peak_reduction_kw > 0 else 0
        cost_per_home = total_initial_investment / num_participating_homes if num_participating_homes > 0 else 0
        
        # Energy and revenue modeling
        # Avg ~1.4 kWh dispatched per event per participating household
        annual_kwh_per_home = 1.4 * (s["annual_dispatched_hours"] / 1.5)
        annual_household_benefit = annual_kwh_per_home * s["household_incentive_per_kwh"]
        total_feeder_kwh_annual = annual_kwh_per_home * num_participating_homes
        
        discom_annual_peaking_savings = total_feeder_kwh_annual * s["discom_tariff_savings_per_kwh"]
        discom_flexibility_cost = total_feeder_kwh_annual * s["household_incentive_per_kwh"] + annual_maintenance
        discom_net_annual_benefit = discom_annual_peaking_savings - discom_flexibility_cost
        
        res = {
            "total_capex": int(total_capex),
            "total_installation": int(total_installation),
            "total_initial_investment": int(total_initial_investment),
            "cost_per_dependable_kw": int(cost_per_dependable_kw),
            "cost_per_home": int(cost_per_home),
            "annual_operator_maintenance": int(annual_maintenance),
            "annual_household_benefit": int(annual_household_benefit),
            "discom_net_annual_benefit": int(discom_net_annual_benefit)
        }
        scenario_results[s_name] = res
        
        # Stakeholder table entries
        table_rows.append({"Scenario": s_name, "Stakeholder": "Household", "CAPEX_INR": 0, "OPEX_INR": 0, "Annual_Revenue_Benefit_INR": int(annual_household_benefit), "Annual_Cost_INR": 0, "Net_Benefit_INR": int(annual_household_benefit), "Key_Assumption": "Zero upfront cost; compensated ₹1.5/kWh for battery wear"})
        table_rows.append({"Scenario": s_name, "Stakeholder": "Operator/Aggregator", "CAPEX_INR": int(total_capex), "OPEX_INR": int(annual_maintenance), "Annual_Revenue_Benefit_INR": int(annual_maintenance * 1.5), "Annual_Cost_INR": int(annual_maintenance), "Net_Benefit_INR": int(annual_maintenance * 0.5), "Key_Assumption": "Earns aggregator service fee from DISCOM"})
        table_rows.append({"Scenario": s_name, "Stakeholder": "DISCOM", "CAPEX_INR": int(total_initial_investment), "OPEX_INR": int(discom_flexibility_cost), "Annual_Revenue_Benefit_INR": int(discom_annual_peaking_savings), "Annual_Cost_INR": int(discom_flexibility_cost), "Net_Benefit_INR": int(discom_net_annual_benefit), "Key_Assumption": "Defers ₹45k/kW BESS & avoids expensive spot power"})

    # Export scenario results
    with open(os.path.join(results_dir, 'economics_scenarios.json'), 'w') as f:
        json.dump(scenario_results, f, indent=4)
        
    pd.DataFrame(table_rows).to_csv(os.path.join(results_dir, 'economics_stakeholder_matrix.csv'), index=False)
    
    base_res = scenario_results["BASE_PROTOTYPE_SCALE"]
    return {
        "gateway_capex": int(measured_gateway_bom),
        "node_capex_per_home": int(measured_node_bom),
        "total_capex": base_res["total_capex"],
        "total_installation": base_res["total_installation"],
        "total_initial_investment": base_res["total_initial_investment"],
        "annual_maintenance": base_res["annual_operator_maintenance"],
        "cost_per_dependable_kw": base_res["cost_per_dependable_kw"],
        "cost_per_home": base_res["cost_per_home"],
        "annual_household_benefit": base_res["annual_household_benefit"]
    }

if __name__ == "__main__":
    print(calculate_economics(44.95, 39))
