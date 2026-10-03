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

import numpy as np


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
        if abs(self.soc - floor_soc) < 1e-12:
            self.soc = floor_soc
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


class InverterFleet:
    """Vectorised version of InverterBatteryFlex for every home on a DT.

    Homes without an inverter have ``mask=False`` and always return zero. Discharge and
    recharge are split so the engine can cap recharge inside a home's essential band.
    """

    def __init__(self, cfg, mask):
        self.mask = np.asarray(mask, dtype=bool)
        n = len(self.mask)
        self.capacity_kwh = cfg["capacity_kwh"]
        self.inverter_kw = cfg["inverter_kw"]
        self.reserve_soc = cfg["reserve_soc"]
        self.target_soc = cfg.get("target_soc", 1.0)
        self.charge_kw = cfg["charge_kw"]
        self.outage_floor_soc = cfg.get("outage_floor_soc", 0.2)
        self.eta = math.sqrt(cfg["round_trip_efficiency"])
        self.stagger = cfg.get("release_stagger_steps", 0)
        self.soc = np.where(self.mask, cfg["initial_soc"], 0.0)
        self.relay_open = np.zeros(n, dtype=bool)
        self.release_step = np.full(n, -1)
        self.ac_delivered_kwh = np.zeros(n)
        self.cell_out_kwh = np.zeros(n)
        self.ac_recharge_kwh = np.zeros(n)
        self.cell_in_kwh = np.zeros(n)
        self.relay_kwh = np.zeros(n)          # delivered to SAANJH (relay open, grid present)
        self.outage_kwh = np.zeros(n)         # delivered as ordinary backup during outages
        self.dispatch_steps = np.zeros(n, dtype=int)
        self.min_soc_relay = np.where(self.mask, cfg["initial_soc"], 1.0)
        self.initial_soc = self.soc.copy()

    def available_kw(self, backed_up_kw, step_h):
        ac = np.maximum(0.0, self.soc - self.reserve_soc) * self.capacity_kwh * self.eta / step_h
        return np.where(self.mask, np.minimum(np.minimum(self.inverter_kw, backed_up_kw), ac), 0.0)

    def expected_recharge_kw(self, step_h):
        need = np.maximum(0.0, self.target_soc - self.soc) * self.capacity_kwh / self.eta / step_h
        on_grid = self.mask & ~self.relay_open
        return np.where(on_grid, np.minimum(self.charge_kw, need), 0.0)

    def open(self, homes):
        self.relay_open[homes] = True
        self.release_step[homes] = -1

    def schedule_release(self, t, rng):
        pending = self.relay_open & (self.release_step < 0)
        self.release_step[pending] = t + rng.integers(0, self.stagger + 1, pending.sum())

    def cancel_release(self):
        self.release_step[self.relay_open] = -1

    def process_releases(self, t):
        """Close relays whose staggered release time has come (call before planning)."""
        closing = self.relay_open & (self.release_step >= 0) & (t >= self.release_step)
        self.relay_open[closing] = False
        self.release_step[closing] = -1

    def discharge(self, t, backed_up_kw, step_h, grid_on):
        """Serve backed-up load from the battery. Returns kW served per home."""
        self.just_closed = np.zeros(len(self.mask), dtype=bool)

        outage = self.mask & ~grid_on
        relay = self.mask & grid_on & self.relay_open
        floor = np.where(outage, self.outage_floor_soc, self.reserve_soc)
        usable = np.maximum(0.0, self.soc - floor) * self.capacity_kwh
        served = np.minimum(np.minimum(self.inverter_kw, backed_up_kw), usable * self.eta / step_h)
        served = np.where(outage | relay, np.maximum(served, 0.0), 0.0)
        cell = served * step_h / self.eta
        # served is limited by the energy above the floor, so SOC never crosses it; a
        # battery already below the floor (after an outage) serves nothing and is unchanged.
        self.soc = self.soc - cell / self.capacity_kwh
        self.soc = np.where(np.abs(self.soc - floor) < 1e-12, floor, self.soc)
        e = served * step_h
        self.ac_delivered_kwh += e
        self.cell_out_kwh += cell
        self.relay_kwh += np.where(relay, e, 0.0)
        self.outage_kwh += np.where(outage, e, 0.0)
        self.dispatch_steps += relay
        self.min_soc_relay = np.where(relay & (served > 0), np.minimum(self.min_soc_relay, self.soc),
                                      self.min_soc_relay)
        exhausted = relay & (self.soc <= self.reserve_soc + 1e-9)
        self.relay_open[exhausted] = False
        self.release_step[exhausted] = -1
        self.just_closed = exhausted   # these homes start recharging next block
        return served

    def recharge(self, step_h, grid_on, max_kw=None):
        """Recharge homes that are on grid with the relay closed. Returns kW drawn."""
        want = self.expected_recharge_kw(step_h) * grid_on * ~getattr(self, "just_closed", False)
        if max_kw is not None:
            want = np.minimum(want, np.maximum(0.0, max_kw))
        cell = want * step_h * self.eta
        self.soc = np.minimum(self.target_soc, self.soc + cell / self.capacity_kwh)
        self.ac_recharge_kwh += want * step_h
        self.cell_in_kwh += cell
        return want
