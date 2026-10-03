import numpy as np
import pandas as pd

"""
SAANJH Virtual Battery Aggregator
Inspired by NREL Virtual Battery Aggregator (BSD-3-Clause)
Adapted for SAANJH: Replaces CVXPY with analytical proportional fair-dispatch heuristics
to ensure CPU execution speed and SAANJH system invariants.
"""

class VirtualBatteryAggregator:
    def __init__(self, time_res_minutes=15):
        self.time_res_minutes = time_res_minutes
        self.households = []
        
    def register_households(self, households):
        self.households = households
        
    def get_available_flexibility(self):
        """
        Aggregates individual flexibility into a virtual battery envelope.
        Follows NREL's capacity summation and weighted SOC averaging.
        """
        total_p_available = 0.0
        total_e_available = 0.0
        total_capacity = 0.0
        weighted_soc_sum = 0.0
        
        for h in self.households:
            if h.participating and h.battery is not None:
                p_avail = h.get_available_flexibility() # instant kW
                
                # Check energy envelope (kWh) available to discharge down to min reserve
                e_avail = h.battery.capacity * (h.battery.soc - h.battery.min_soc)
                
                if p_avail > 0 and e_avail > 0:
                    total_p_available += p_avail
                    total_e_available += e_avail
                    total_capacity += h.battery.capacity
                    weighted_soc_sum += (h.battery.soc * h.battery.capacity)
                    
        agg_soc = (weighted_soc_sum / total_capacity) if total_capacity > 0 else 0.0
        
        return {
            "aggregate_power_kw": total_p_available,
            "aggregate_energy_kwh": total_e_available,
            "aggregate_capacity_kwh": total_capacity,
            "aggregate_soc": agg_soc
        }
        
    def dispatch(self, requested_power_kw):
        """
        Disaggregates a total power request back to individual DERs (batteries).
        Uses a fair proportional allocation strategy similar to NREL's min-max objective.
        """
        if requested_power_kw <= 0:
            return 0.0
            
        # Collect available capacities
        available_assets = []
        for h in self.households:
            if h.participating and h.battery is not None:
                p_avail = h.get_available_flexibility()
                if p_avail > 0:
                    available_assets.append({
                        "home": h,
                        "p_avail": p_avail
                    })
                    
        total_available = sum(a["p_avail"] for a in available_assets)
        if total_available == 0:
            return 0.0
            
        actual_dispatch = 0.0
        # Proportional dispatch (Fairness)
        # Power is dispatched relative to each battery's available contribution to the aggregate
        for asset in available_assets:
            proportion = asset["p_avail"] / total_available
            target_dispatch = requested_power_kw * proportion
            
            # Enforce physical limit at the edge node
            safe_dispatch = min(target_dispatch, asset["p_avail"])
            
            # Command the edge
            asset["home"].dispatch_battery(safe_dispatch)
            actual_dispatch += safe_dispatch
            
        return actual_dispatch
