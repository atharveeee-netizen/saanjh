import numpy as np
from simulation.config import (LOAD_PROFILES, PROB_AC, PROB_EV, PROB_WATER_HEATER, PROB_WATER_PUMP,
                               BATTERY_CAPACITY_WH, BATTERY_INVERTER_RATING_W, BATTERY_RESERVE_SOC)
from simulation.models.battery import Battery

class Household:
    def __init__(self, hid, has_battery, has_solar):
        self.hid = hid
        self.has_solar = has_solar
        self.battery = Battery(
            capacity_kwh=BATTERY_CAPACITY_WH/1000.0,
            inverter_rating_kw=BATTERY_INVERTER_RATING_W/1000.0,
            reserve_soc=BATTERY_RESERVE_SOC
        ) if has_battery else None
        
        self.has_ac = np.random.rand() < PROB_AC
        self.has_ev = np.random.rand() < PROB_EV
        self.has_water_heater = np.random.rand() < PROB_WATER_HEATER
        self.has_water_pump = np.random.rand() < PROB_WATER_PUMP
        
        # Current state
        self.participating = True
        self.participation_count = 0
        self.is_dispatched = False
        self.current_dispatch_kw = 0.0

    def get_base_load(self, hour):
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
                    cook_start = 18.5 + np.random.rand() * 0.5
                    if cook_start <= hour <= cook_start + 1.0:
                        load += profile["peak_add"] * (0.6 + 0.4 * np.random.rand())
        
        return load

    def get_deferrable_load(self, hour):
        load = 0
        if self.has_ac and hour >= 18.5:
            load += LOAD_PROFILES["ac"]["peak_add"] * (0.7 + 0.1 * np.random.rand())
        
        if self.has_ev and hour >= 20:
            load += LOAD_PROFILES["ev_charger"]["peak_add"]
            
        if self.has_water_heater and 18 <= hour <= 20:
            load += LOAD_PROFILES["water_heater"]["peak_add"] * (0.3 + 0.4 * np.random.rand())
            
        if self.has_water_pump and 17.5 <= hour <= 19.5:
            load += LOAD_PROFILES["water_pump"]["peak_add"] * 0.5
            
        return load

    def get_available_flexibility(self):
        """kW this home can shed right now."""
        flex_w = 0
        
        if self.has_ac:
            flex_w += LOAD_PROFILES["ac"]["peak_add"] * 0.7
        if self.has_ev:
            flex_w += LOAD_PROFILES["ev_charger"]["peak_add"]
        if self.has_water_heater:
            flex_w += LOAD_PROFILES["water_heater"]["peak_add"] * 0.3
        if self.has_water_pump:
            flex_w += LOAD_PROFILES["water_pump"]["peak_add"] * 0.5
            
        flex_kw = flex_w / 1000.0
        
        if self.battery is not None:
            flex_kw += self.battery.get_available_power()
            
        return flex_kw
        
    def dispatch_battery(self, power_kw):
        """Called by Aggregator to command a specific kW dispatch"""
        if self.battery is not None:
            self.is_dispatched = True
            self.current_dispatch_kw = power_kw
        
    def step(self, dt_min):
        if self.is_dispatched and self.battery is not None:
            self.battery.discharge(self.current_dispatch_kw, dt_min)
            self.participation_count += 1
            # Reset dispatch for next step. Aggregator must re-dispatch every step.
            self.is_dispatched = False 
            self.current_dispatch_kw = 0.0
            
        elif self.battery is not None:
            # Trickle charge
            self.battery.charge(0.2, dt_min)
