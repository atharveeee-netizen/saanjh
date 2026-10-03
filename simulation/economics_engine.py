import os
import json

def calculate_economics(peak_reduction_kw, num_participating_homes):
    # Hardware BOM assumptions (from docs/SUBMISSION.md)
    gateway_capex = 11275 + 2999 + 1639 + 2809 + 2139 + 299 + 540 + 720 # RPi CM4 + LoRa + Hub + Accessories
    node_capex = 2999 + 1639 + 1019 + 162 + 455 + 799 # LoRa + Base + Env Sensors
    
    total_gateway_capex = gateway_capex # 1 Gateway per transformer
    total_node_capex = node_capex * num_participating_homes
    
    total_capex = total_gateway_capex + total_node_capex
    
    # Installation and Maintenance (Illustrative Assumptions)
    installation_cost_per_node = 500 # ₹500 per home for electrician
    total_installation = installation_cost_per_node * num_participating_homes
    
    annual_maintenance = total_capex * 0.05 # 5% of CAPEX
    
    # Financial KPIs
    total_initial_investment = total_capex + total_installation
    
    cost_per_dependable_kw = total_initial_investment / peak_reduction_kw if peak_reduction_kw > 0 else 0
    
    return {
        "gateway_capex": int(gateway_capex),
        "node_capex_per_home": int(node_capex),
        "total_capex": int(total_capex),
        "total_installation": int(total_installation),
        "total_initial_investment": int(total_initial_investment),
        "annual_maintenance": int(annual_maintenance),
        "cost_per_dependable_kw": int(cost_per_dependable_kw)
    }

if __name__ == "__main__":
    # Test logic
    print(calculate_economics(54.0, 50))
