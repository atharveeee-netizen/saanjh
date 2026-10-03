from simulation.config import BATTERY_CAPACITY_WH, BATTERY_INVERTER_RATING_W, BATTERY_RESERVE_SOC

class Battery:
    def __init__(self, capacity_kwh=None, inverter_rating_kw=None, reserve_soc=None):
        self.capacity = capacity_kwh if capacity_kwh is not None else (BATTERY_CAPACITY_WH / 1000.0)
        self.inverter_rating = inverter_rating_kw if inverter_rating_kw is not None else (BATTERY_INVERTER_RATING_W / 1000.0)
        self.min_soc = reserve_soc if reserve_soc is not None else BATTERY_RESERVE_SOC
        self.soc = 0.92 # Urban India typical evening state before grid deficit
        
    def get_available_power(self, dt_min=5):
        if self.soc > self.min_soc:
            energy_avail_kwh = (self.soc - self.min_soc) * self.capacity
            max_power_kw = energy_avail_kwh / (dt_min / 60.0)
            return min(self.inverter_rating, max_power_kw)
        return 0.0
        
    def discharge(self, power_kw, dt_min=5):
        if self.soc <= self.min_soc or power_kw <= 0:
            return 0.0
        energy_avail_kwh = (self.soc - self.min_soc) * self.capacity
        energy_req_kwh = power_kw * (dt_min / 60.0)
        energy_discharged = min(energy_req_kwh, energy_avail_kwh)
        self.soc -= energy_discharged / self.capacity
        # Hard physical constraint: Never drop below reserve
        self.soc = max(self.min_soc, self.soc)
        actual_power = energy_discharged / (dt_min / 60.0)
        return actual_power
        
    def charge(self, power_kw, dt_min=5):
        energy_kwh = power_kw * (dt_min / 60.0)
        self.soc += energy_kwh / self.capacity
        self.soc = min(1.0, self.soc)
