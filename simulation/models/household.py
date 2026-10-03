import numpy as np
from simulation.config import (LOAD_PROFILES, PROB_AC, PROB_EV, PROB_WATER_HEATER, PROB_WATER_PUMP,
                               BATTERY_CAPACITY_WH, BATTERY_INVERTER_RATING_W, BATTERY_AVAILABLE_SOC, BATTERY_RESERVE_SOC)

class Household:
    def __init__(self, hid, has_battery, has_solar):
        self.hid = hid
        self.has_battery = has_battery
        self.has_solar = has_solar
        
        self.has_ac = np.random.rand() < PROB_AC
        self.has_ev = np.random.rand() < PROB_EV
        self.has_water_heater = np.random.rand() < PROB_WATER_HEATER
        self.has_water_pump = np.random.rand() < PROB_WATER_PUMP
        
        # Current state
        self.battery_soc = 1.0 if has_battery else 0.0
        self.participation_count = 0
        self.is_dispatched = False
        self.dispatch_remaining_min = 0

    def get_base_load(self, hour):
        """Non-deferrable load that cannot be shifted."""
        load = 0
        for category, profile in LOAD_PROFILES.items():
            if profile["deferrable"]:
                continue
            
            if category == "lighting":
                if hour >= 18:
                    load += profile["base"] + profile["peak_add"]
                elif hour >= 17:
                    load += profile["base"] * 0.5
            elif category == "fans":
                load += profile["base"]
            elif category == "tv":
                if hour >= 18.5:
                    load += profile["base"]
            elif category == "refrigerator":
                load += profile["base"]
            elif category == "cooking":
                if 18.5 <= hour <= 20.5:
                    # Stochastic: cooking happens at slightly different times per home
                    cook_start = 18.5 + np.random.rand() * 0.5
                    if cook_start <= hour <= cook_start + 1.0:
                        load += profile["peak_add"] * (0.6 + 0.4 * np.random.rand())
        
        return load

    def get_deferrable_load(self, hour):
        """Load that SAANJH can shift or reduce."""
        load = 0
        if self.has_ac and hour >= 18.5:
            # AC duty cycle: runs ~70-80% of the time
            load += LOAD_PROFILES["ac"]["peak_add"] * (0.7 + 0.1 * np.random.rand())
        
        if self.has_ev and hour >= 20:
            load += LOAD_PROFILES["ev_charger"]["peak_add"]
            
        if self.has_water_heater and 18 <= hour <= 20:
            load += LOAD_PROFILES["water_heater"]["peak_add"] * (0.3 + 0.4 * np.random.rand())
            
        if self.has_water_pump and 17.5 <= hour <= 19.5:
            load += LOAD_PROFILES["water_pump"]["peak_add"] * 0.5
            
        return load

    def get_available_flexibility(self):
        """Watts this home can shed right now."""
        flex = 0
        
        if self.is_dispatched:
            return 0
            
        if self.has_ac:
            flex += LOAD_PROFILES["ac"]["peak_add"] * 0.7
        if self.has_ev:
            flex += LOAD_PROFILES["ev_charger"]["peak_add"]
        if self.has_water_heater:
            flex += LOAD_PROFILES["water_heater"]["peak_add"] * 0.3
        if self.has_water_pump:
            flex += LOAD_PROFILES["water_pump"]["peak_add"] * 0.5
            
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
                energy_used_wh = BATTERY_INVERTER_RATING_W * (dt_min / 60)
                self.battery_soc -= energy_used_wh / BATTERY_CAPACITY_WH
                
        # Recharge battery slowly if not dispatched
        elif self.has_battery and self.battery_soc < 1.0:
            recharge_wh = 200 * (dt_min / 60) # 200W charging
            self.battery_soc = min(1.0, self.battery_soc + recharge_wh / BATTERY_CAPACITY_WH)
