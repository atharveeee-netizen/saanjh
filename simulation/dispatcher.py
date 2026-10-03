"""SAANJH deficit dispatcher: one explicit, documented policy.

Every 15-minute block the gateway compares the DT's expected draw (demand minus rooftop
PV, plus inverter recharge and appliance rebound that would start now) with its supply
limit (the DISCOM allocation, or the DT's own loading limit if lower). If there is a gap:

Step 1  Close it with flexibility that costs nobody their essentials:
        a. hold appliance rebound that would otherwise start now;
        b. open inverter relays (backed-up circuits move to the home's own battery, never
           below its reserve), least-used homes first;
        c. defer actuated appliances / raise AC setpoints, least-curtailed homes first;
        d. discharge the community battery, if it has enough energy for the whole
           expected event ("full support"). If it does not, its energy is reserved for
           keeping essential bands on (step 3).
Step 2  If still short, cap homes at the gentlest essential band in the ladder that
        closes the gap (critical homes keep their higher band). Only homes drawing above
        the band are affected.
Step 3  If still short at the lowest band, use the reserved community-battery energy.
Step 4  Only if still short, disconnect individual homes through their smart meters, in
        the smallest possible blocks (one home at a time). Fair rotation: the home with
        the least cumulative disconnection so far goes next, so the burden evens out
        across homes over the year. Critical homes are disconnected only after all others.

Fair-access rule for the community battery: when its energy is short of the event, it
is not spent lifting anyone above their essential band; it only tops up supply once
everyone is already limited to essentials.

Every block with an action produces a log entry with the reason, used by the API and UI.
"""
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Decision:
    gap_kw: float = 0.0
    hold: np.ndarray = None
    open_relays: np.ndarray = None
    curtail: np.ndarray = None
    band_level_w: float = None
    banded: np.ndarray = None
    shed: np.ndarray = None
    cb_kw: float = 0.0             # + discharge, - charge
    battery_mode: str = None
    covered: dict = field(default_factory=dict)
    reason: str = ""


def _take_until(order, values, need):
    """Pick items in ``order`` until their ``values`` sum to at least ``need``."""
    if need <= 0 or not len(order):
        return np.array([], dtype=int), 0.0
    v = values[order]
    cum = np.cumsum(v)
    k = int(np.searchsorted(cum, need - 1e-9)) + 1
    k = min(k, len(order))
    return order[:k], float(cum[k - 1])


class DeficitDispatcher:
    def __init__(self, cfg, fleet, inv, flex, band, cb, step_h):
        self.cfg = cfg
        self.fleet = fleet
        self.inv = inv
        self.flex = flex
        self.band = band
        self.cb = cb
        self.step_h = step_h
        self.mode = cfg["dispatch"].get("battery_mode", "auto")
        self.assumed_blocks = cfg["dispatch"]["assumed_event_blocks"]
        n = fleet.n
        self.cum_shed = np.zeros(n)
        self.event_age = 0
        self.charge_window = cfg["community_battery"]["charge_window_h"]

    def plan(self, loads, t, hour, limit_kw, pv_kw, temp_c, event_energy_kwh=None,
             charge_target_soc=None):
        n = self.fleet.n
        eligible = ~self.fleet.opted_out
        d = loads.total[:, t]
        bu = loads.backed_up[:, t]
        rech = self.inv.expected_recharge_kw(self.step_h)
        if self.flex is not None:
            reb, reb_forced = self.flex.rebound_split(loads, t)
        else:
            reb = reb_forced = np.zeros(n)
        draw0 = d - pv_kw + rech + reb + reb_forced
        gap = float(draw0.sum() - limit_kw)
        dec = Decision(gap_kw=gap, hold=np.zeros(n, bool), open_relays=np.zeros(n, bool),
                       curtail=np.zeros(n, bool), banded=np.zeros(n, bool), shed=np.zeros(n, bool))

        if gap <= 0:
            self.event_age = 0
            # Spare supply: recharge the community battery in solar hours.
            if self.cb is not None:
                in_window = self.charge_window[0] <= hour < self.charge_window[1]
                below_floor = self.cb.soc < self.cb.soc_min + 0.05
                if in_window or below_floor:
                    headroom = -gap * 0.9
                    dec.cb_kw = -min(headroom, self.cb.max_charge_kw(self.step_h, temp_c, charge_target_soc))
            return dec

        self.event_age += 1
        remaining = gap
        draw = draw0.copy()

        # Step 1a: hold rebound.
        if self.flex is not None:
            dec.hold = self.flex.mask.copy()
            remaining -= reb.sum()
            draw -= reb
            dec.covered["rebound_held_kw"] = float(reb.sum())

        # Step 1b: inverter relays (already-open relays keep delivering).
        avail = self.inv.available_kw(bu, self.step_h)
        relay_value = avail + np.where(self.inv.relay_open, 0.0, rech)   # opening also stops recharge
        already = self.inv.relay_open & eligible & (avail > 0)
        remaining -= relay_value[already].sum()
        draw -= np.where(already, relay_value, 0.0)
        cand = np.where(eligible & self.inv.mask & ~self.inv.relay_open & (avail > 0))[0]
        if remaining > 0 and len(cand):
            order = cand[np.lexsort((-avail[cand], self.inv.dispatch_steps[cand]))]
            picked, got = _take_until(order, relay_value, remaining)
            dec.open_relays[picked] = True
            remaining -= got
            draw[picked] -= relay_value[picked]
        dec.covered["relay_kw"] = float(relay_value[already | dec.open_relays].sum())

        # Step 1c: appliance deferral / AC setpoint.
        if self.flex is not None and remaining > 0:
            pot = self.flex.potential_kw(loads, t)
            cand = np.where(eligible & self.flex.mask & (pot > 0))[0]
            if len(cand):
                order = cand[np.argsort(self.flex.curtailed_steps[cand], kind="stable")]
                picked, got = _take_until(order, pot, remaining)
                dec.curtail[picked] = True
                remaining -= got
                draw[picked] -= pot[picked]
                dec.covered["appliance_kw"] = got

        # Step 1d: community battery, full support only if it can last the event.
        cb_max = self.cb.max_discharge_kw(self.step_h, temp_c) if self.cb is not None else 0.0
        dec.covered["battery_max_kw"] = cb_max
        if remaining > 0 and cb_max > 0:
            need = event_energy_kwh
            if need is None:
                need = remaining * max(1, self.assumed_blocks - self.event_age + 1) * self.step_h
            have = self.cb.usable_kwh() * self.cb.eta
            full = self.mode == "full" or (self.mode == "auto" and have >= need)
            dec.battery_mode = "full support" if full else "essential only"
            if full:
                dec.cb_kw = min(remaining, cb_max)
                remaining -= dec.cb_kw

        # Step 2: essential band, gentlest level that closes the gap.
        if remaining > 0:
            chosen = None
            for level in self.band.ladder_w:
                cut = self.band.reduction_kw(draw, level)
                if cut.sum() >= remaining - 1e-9:
                    chosen = level
                    break
            if chosen is None:
                chosen = self.band.ladder_w[-1]
                cut = self.band.reduction_kw(draw, chosen)
            dec.band_level_w = chosen
            dec.banded = cut > 1e-9
            remaining -= cut.sum()
            draw -= cut
            dec.covered["band_kw"] = float(cut.sum())

        # Step 3: reserved battery energy, now that everyone is on essentials.
        if remaining > 0 and dec.battery_mode == "essential only":
            extra = min(remaining, cb_max - dec.cb_kw)
            dec.cb_kw += extra
            remaining -= extra

        # Step 4: disconnect individual homes, fairest rotation.
        if remaining > 0:
            saving = np.maximum(0.0, draw)
            cand = np.where(saving > 0)[0]
            crit = self.fleet.critical[cand]
            order = cand[np.lexsort((-saving[cand], self.cum_shed[cand], crit))]
            picked, got = _take_until(order, saving, remaining)
            dec.shed[picked] = True
            remaining -= got
            dec.covered["shed_kw"] = got
        dec.covered["battery_kw"] = dec.cb_kw
        dec.reason = self._reason(dec)
        return dec

    def _reason(self, dec):
        parts = [f"Gap {dec.gap_kw:.1f} kW."]
        c = dec.covered
        if c.get("rebound_held_kw", 0) > 0.05:
            parts.append(f"Held {c['rebound_held_kw']:.1f} kW of appliance rebound.")
        if c.get("relay_kw", 0) > 0.05:
            parts.append(f"Inverter relays carried {c['relay_kw']:.1f} kW.")
        if c.get("appliance_kw", 0) > 0.05:
            parts.append(f"Deferred {c['appliance_kw']:.1f} kW of appliances.")
        if dec.cb_kw > 0.05:
            parts.append(f"Community battery {dec.cb_kw:.1f} kW ({dec.battery_mode}).")
        if dec.band_level_w is not None:
            parts.append(f"Band {dec.band_level_w:.0f} W applied to {int(dec.banded.sum())} homes "
                         f"because earlier steps left {c.get('band_kw', 0):.1f} kW uncovered.")
        if dec.shed.any():
            parts.append(f"Disconnected {int(dec.shed.sum())} homes ({c.get('shed_kw', 0):.1f} kW) "
                         "after all other steps were exhausted.")
        return " ".join(parts)
