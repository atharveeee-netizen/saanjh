class Battery:
    def __init__(self, capacity_kwh=5.0, inverter_rating_kw=3.0, reserve_soc=0.2):
        self.capacity = capacity_kwh
        self.inverter_rating = inverter_rating_kw
        self.min_soc = reserve_soc
        self.soc = 1.0 # Start fully charged
        
    def get_available_power(self):
        if self.soc > self.min_soc:
            return self.inverter_rating
        return 0.0
        
    def discharge(self, power_kw, dt_min):
        energy_kwh = power_kw * (dt_min / 60.0)
        self.soc -= energy_kwh / self.capacity
        self.soc = max(self.min_soc, self.soc)
        
    def charge(self, power_kw, dt_min):
        energy_kwh = power_kw * (dt_min / 60.0)
        self.soc += energy_kwh / self.capacity
        self.soc = min(1.0, self.soc)
