import numpy as np
from simulation.config import LOAD_PROFILES, PROB_AC, PROB_EV, BATTERY_CAPACITY_WH, BATTERY_INVERTER_RATING_W, BATTERY_AVAILABLE_SOC, BATTERY_RESERVE_SOC

class Household:
    def __init__(self, hid, has_battery, has_solar):
        self.hid = hid
        self.has_battery = has_battery
        self.has_solar = has_solar
        
        self.has_ac = np.random.rand() < PROB_AC
        self.has_ev = np.random.rand() < PROB_EV
        
        # Current state
        self.battery_soc = 1.0 if has_battery else 0.0
        self.participation_count = 0
        self.is_dispatched = False
        self.dispatch_remaining_min = 0

    def get_base_load(self, hour):
        # Time-varying base load based on hour (16 to 22)
        load = 0
        for category, profile in LOAD_PROFILES.items():
            if profile["deferrable"]:
                continue
            
            # Simple heuristic for when appliances are used
            if category == "lighting" and hour >= 18:
                load += profile["base"] + profile["peak_add"] * np.random.rand()
            elif category == "fans":
                load += profile["base"] + profile["peak_add"] * np.random.rand()
            elif category == "tv" and hour >= 19:
                load += profile["base"] + profile["peak_add"] * np.random.rand()
            elif category == "refrigerator":
                load += profile["base"] + profile["peak_add"] * np.random.rand()
            elif category == "cooking" and 18 <= hour <= 20:
                load += profile["base"] + profile["peak_add"] * np.random.rand()
        
        return load

    def get_deferrable_load(self, hour):
        load = 0
        if self.has_ac and 19 <= hour <= 22:
            load += LOAD_PROFILES["ac"]["peak_add"] * 0.8 # Average duty cycle
        
        if self.has_ev and hour >= 20:
            load += LOAD_PROFILES["ev_charger"]["peak_add"]
            
        return load

    def get_available_flexibility(self):
        flex = 0
        
        if self.is_dispatched:
            return 0
            
        # Deferrable loads that can be turned off
        # Simplified: assume if it's evening, AC and EV might be on and can be deferred
        if self.has_ac:
            flex += LOAD_PROFILES["ac"]["peak_add"] * 0.8
        if self.has_ev:
            flex += LOAD_PROFILES["ev_charger"]["peak_add"]
            
        # Battery discharge
        if self.has_battery and self.battery_soc > BATTERY_RESERVE_SOC:
            flex += BATTERY_INVERTER_RATING_W
            
        return flex
        
    def dispatch(self, duration_min):
        self.is_dispatched = True
        self.dispatch_remaining_min = duration_min
        self.participation_count += 1
        
    def step(self, dt_min):
        if self.is_dispatched:
            self.dispatch_remaining_min -= dt_min
            if self.dispatch_remaining_min <= 0:
                self.is_dispatched = False
                self.dispatch_remaining_min = 0
            
            # Discharge battery if we're using it for flexibility
            if self.has_battery and self.battery_soc > BATTERY_RESERVE_SOC:
                # Discharging at inverter rating
                energy_used_wh = BATTERY_INVERTER_RATING_W * (dt_min / 60)
                self.battery_soc -= energy_used_wh / BATTERY_CAPACITY_WH
                
        # Recharge battery slowly if not dispatched
        elif self.has_battery and self.battery_soc < 1.0:
            recharge_wh = 200 * (dt_min / 60) # 200W charging
            self.battery_soc = min(1.0, self.battery_soc + recharge_wh / BATTERY_CAPACITY_WH)
