"""Inverter-battery flexibility through a relay on the inverter's mains input.

Opening the relay puts the home's backed-up circuits on the inverter battery, so the
power "delivered" is exactly the backed-up load the home stops drawing from the grid,
capped by the inverter rating and by the energy left above the reserve. An inverter
cannot export to the grid, so it can never deliver more than the home's own backed-up
load.

The relay is normally closed: if the node fails, the inverter stays on grid.

Energy accounting (all kWh):
    cell energy out  = SOC drop x capacity
    AC energy served = cell energy out x discharge efficiency
    AC energy drawn when recharging = SOC gain x capacity / charge efficiency
Round-trip efficiency is split equally between charge and discharge.
"""
import math


class InverterBatteryFlex:
    def __init__(self, cfg):
        self.capacity_kwh = cfg["capacity_kwh"]
        self.inverter_kw = cfg["inverter_kw"]
        self.reserve_soc = cfg["reserve_soc"]
        self.target_soc = cfg.get("target_soc", 1.0)
        self.charge_kw = cfg["charge_kw"]
        self.outage_floor_soc = cfg.get("outage_floor_soc", 0.2)
        eta = math.sqrt(cfg["round_trip_efficiency"])
        self.eta_charge = eta
        self.eta_discharge = eta
        self.soc = cfg["initial_soc"]
        self.relay_open = False
        self.release_step = None  # step at which a pending release closes the relay

        # Ledger
        self.ac_delivered_kwh = 0.0   # AC energy served to the home from the battery
        self.cell_out_kwh = 0.0       # energy taken out of the cells
        self.ac_recharge_kwh = 0.0    # AC energy drawn from the grid to recharge
        self.cell_in_kwh = 0.0        # energy put back into the cells
        self.dispatch_steps = 0
        self.min_soc_seen = self.soc

    # ---------------------------------------------------------------- capability
    def energy_above_reserve_kwh(self):
        return max(0.0, (self.soc - self.reserve_soc) * self.capacity_kwh)

    def available_kw(self, backed_up_kw, step_h):
        """Power the home would stop drawing from the grid if the relay opened now."""
        ac_energy = self.energy_above_reserve_kwh() * self.eta_discharge
        return max(0.0, min(self.inverter_kw, backed_up_kw, ac_energy / step_h))

    # ---------------------------------------------------------------- control
    def open_relay(self):
        self.relay_open = True
        self.release_step = None

    def schedule_release(self, step):
        if self.relay_open and self.release_step is None:
            self.release_step = step

    def force_close(self):
        self.relay_open = False
        self.release_step = None

    # ---------------------------------------------------------------- physics
    def step(self, t, backed_up_kw, step_h, grid_available=True):
        """Advance one step. Returns (kW served from battery, kW drawn to recharge).

        ``grid_available=False`` models a supply outage: the inverter carries its
        backed-up load regardless of the relay (this is what home inverters are for),
        and it may use the full battery, not only the part above SAANJH's reserve.
        """
        if self.release_step is not None and t >= self.release_step:
            self.force_close()

        if not grid_available:
            return self._discharge(backed_up_kw, step_h, floor_soc=self.outage_floor_soc), 0.0

        if self.relay_open:
            served = self._discharge(backed_up_kw, step_h, floor_soc=self.reserve_soc)
            self.dispatch_steps += 1
            if self.soc <= self.reserve_soc + 1e-9:
                self.force_close()
            return served, 0.0

        return 0.0, self._recharge(step_h)

    def _discharge(self, load_kw, step_h, floor_soc):
        usable_cell = max(0.0, (self.soc - floor_soc) * self.capacity_kwh)
        served_kw = max(0.0, min(self.inverter_kw, load_kw,
                                 usable_cell * self.eta_discharge / step_h))
        cell_out = served_kw * step_h / self.eta_discharge
        self.soc -= cell_out / self.capacity_kwh
        self.soc = max(floor_soc, self.soc)
        self.ac_delivered_kwh += served_kw * step_h
        self.cell_out_kwh += cell_out
        self.min_soc_seen = min(self.min_soc_seen, self.soc)
        return served_kw

    def _recharge(self, step_h):
        if self.soc >= self.target_soc - 1e-9:
            return 0.0
        cell_needed = (self.target_soc - self.soc) * self.capacity_kwh
        draw_kw = min(self.charge_kw, cell_needed / self.eta_charge / step_h)
        cell_in = draw_kw * step_h * self.eta_charge
        self.soc = min(self.target_soc, self.soc + cell_in / self.capacity_kwh)
        self.ac_recharge_kwh += draw_kw * step_h
        self.cell_in_kwh += cell_in
        return draw_kw
