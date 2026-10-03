"""Community battery at the distribution transformer (second-life EV packs).

The pack sits on the DT's low-voltage bus behind a power conversion system (PCS). It
charges when the DT has spare supply (preferably in solar hours, the cheapest
Time-of-Day block) and discharges during deficit windows. Its energy adds to the DT's
supply allocation for everyone on the transformer; the dispatcher decides how it is used
(see simulation/dispatcher.py for the fair-access rule).

Modelled: usable SOC window, round-trip efficiency split equally between charge and
discharge, capacity fade per equivalent full cycle, and a power derate when ambient
temperature exceeds a threshold. All parameters are in config/saanjh.yaml with labels.
"""
import math


class CommunityBattery:
    def __init__(self, cfg):
        self.nameplate_kwh = cfg["capacity_kwh"]
        self.power_kw = cfg["power_kw"]
        self.eta = math.sqrt(cfg["round_trip_efficiency"])
        self.soc_min = cfg["soc_min"]
        self.soc_max = cfg["soc_max"]
        self.fade_per_efc = cfg["fade_per_efc"]
        self.derate_start_c = cfg["derate_start_c"]
        self.derate_per_c = cfg["derate_per_c"]
        self.soc = cfg.get("initial_soc", self.soc_max)
        self.efc = 0.0               # equivalent full cycles (discharge throughput / capacity)
        self.discharged_kwh = 0.0    # AC energy delivered
        self.charged_kwh = 0.0       # AC energy drawn
        self.cell_out_kwh = 0.0
        self.cell_in_kwh = 0.0
        self.initial_soc = self.soc
        self.capacity_kwh = self.nameplate_kwh
        self.fade_loss_kwh = 0.0     # stored energy lost when capacity fades

    def apply_fade(self):
        """Update capacity from cycles so far (called once a day). SOC fraction is kept,
        so the stored energy lost to fade is booked in ``fade_loss_kwh``."""
        new_cap = self.nameplate_kwh * max(0.0, 1.0 - self.fade_per_efc * self.efc)
        self.fade_loss_kwh += self.soc * (self.capacity_kwh - new_cap)
        self.capacity_kwh = new_cap

    def stored_kwh(self):
        return self.soc * self.capacity_kwh

    def usable_kwh(self, floor_soc=None):
        floor = self.soc_min if floor_soc is None else max(self.soc_min, floor_soc)
        return max(0.0, (self.soc - floor) * self.capacity_kwh)

    def power_limit_kw(self, temp_c):
        over = max(0.0, temp_c - self.derate_start_c)
        return self.power_kw * max(0.0, 1.0 - self.derate_per_c * over)

    def max_discharge_kw(self, step_h, temp_c, floor_soc=None):
        return min(self.power_limit_kw(temp_c), self.usable_kwh(floor_soc) * self.eta / step_h)

    def max_charge_kw(self, step_h, temp_c, target_soc=None):
        target = self.soc_max if target_soc is None else min(self.soc_max, target_soc)
        room = max(0.0, (target - self.soc) * self.capacity_kwh)
        return min(self.power_limit_kw(temp_c), room / self.eta / step_h)

    def discharge(self, kw, step_h, temp_c, floor_soc=None):
        kw = max(0.0, min(kw, self.max_discharge_kw(step_h, temp_c, floor_soc)))
        cell = kw * step_h / self.eta
        cap = self.capacity_kwh
        self.soc -= cell / cap
        self.efc += cell / self.nameplate_kwh
        self.discharged_kwh += kw * step_h
        self.cell_out_kwh += cell
        return kw

    def charge(self, kw, step_h, temp_c, target_soc=None):
        kw = max(0.0, min(kw, self.max_charge_kw(step_h, temp_c, target_soc)))
        cell = kw * step_h * self.eta
        self.soc += cell / self.capacity_kwh
        self.charged_kwh += kw * step_h
        self.cell_in_kwh += cell
        return kw
