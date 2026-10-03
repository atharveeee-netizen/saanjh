"""Appliance flexibility for homes with an installed actuator.

Only homes with ``has_actuator=True`` (a smart plug or contactor on a geyser, pump or EV
charger, or a controllable AC) can offer this. Nothing is counted for homes without one.

* Deferrable appliances (``flex: defer``): energy that would have been used during an event
  is queued and served later. An appliance waits at most ``max_defer_min``; after the
  event its queued energy comes back (rebound) at up to the appliance's rated power, with
  restarts staggered across homes. Total appliance energy over a run is unchanged.
* ACs (``flex: setpoint``): a setpoint raise cuts AC power by ``ac_setpoint_reduction``.
  A share ``ac_rebound_share`` of the avoided energy comes back after the event as extra
  pull-down load; the rest is a real saving (the room ran slightly warmer).
"""
import numpy as np


class ApplianceFlex:
    def __init__(self, household, cfg):
        self.household = household
        self.cfg = cfg
        self.max_defer_min = cfg["max_defer_min"]
        self.ac_reduction = cfg["ac_setpoint_reduction"]
        self.ac_rebound_share = cfg["ac_rebound_share"]
        self.rebound_stagger_steps = cfg["rebound_stagger_steps"]

        self.queue_kwh = {}
        self.deferred_steps = {}
        self.rebound_start = {}
        self.ac_queue_kwh = 0.0

        # Ledger
        self.scheduled_kwh = 0.0     # deferrable energy the home wanted
        self.served_kwh = 0.0        # deferrable energy actually served (incl. rebound)
        self.deferred_kwh = 0.0      # energy moved out of event steps
        self.rebound_kwh = 0.0       # energy served later as rebound
        self.ac_avoided_kwh = 0.0
        self.ac_rebound_kwh = 0.0
        self.curtailed_steps = 0

    def _max_steps(self, name, step_h):
        return int(self.max_defer_min.get(name, 60) // (step_h * 60))

    def _rated_kw(self, name):
        spec = self.household.seg_cfg["appliances"][name]
        rated = spec.get("session", {}).get("kw", 0.0) * self.household.scale[name]
        arr = self.household.loads.get(name)
        if arr is not None and len(arr):
            rated = max(rated, float(arr.max()))
        return rated

    def potential_kw(self, t, step_h):
        """kW this home could shed at step t if asked."""
        kw = 0.0
        for name, arr in self.household.flex_loads("defer").items():
            if arr[t] > 0 and self.deferred_steps.get(name, 0) < self._max_steps(name, step_h):
                kw += arr[t]
        for arr in self.household.flex_loads("setpoint").values():
            kw += self.ac_reduction * arr[t]
        return kw

    def step(self, t, curtail, step_h, rng):
        """Advance one step. Returns (kW reduced versus schedule, kW of rebound added)."""
        reduction = 0.0
        rebound = 0.0
        if curtail:
            self.curtailed_steps += 1

        for name, arr in self.household.flex_loads("defer").items():
            sched = float(arr[t])
            self.scheduled_kwh += sched * step_h
            queue = self.queue_kwh.get(name, 0.0)
            can_defer = self.deferred_steps.get(name, 0) < self._max_steps(name, step_h)

            if curtail and sched > 0 and can_defer:
                self.queue_kwh[name] = queue + sched * step_h
                self.deferred_steps[name] = self.deferred_steps.get(name, 0) + 1
                self.deferred_kwh += sched * step_h
                self.rebound_start.pop(name, None)
                reduction += sched
                continue

            served = sched
            if queue > 1e-12:
                holding = curtail and can_defer
                if not holding and name not in self.rebound_start:
                    self.rebound_start[name] = t + int(rng.integers(0, self.rebound_stagger_steps + 1))
                if not holding and t >= self.rebound_start.get(name, t + 1):
                    extra = min(max(0.0, self._rated_kw(name) - sched), queue / step_h)
                    self.queue_kwh[name] = queue - extra * step_h
                    served += extra
                    rebound += extra
                    self.rebound_kwh += extra * step_h
                    if self.queue_kwh[name] <= 1e-9:
                        self.queue_kwh[name] = 0.0
                        self.deferred_steps[name] = 0
                        self.rebound_start.pop(name, None)
            elif not curtail:
                self.deferred_steps[name] = 0
            self.served_kwh += served * step_h

        for name, arr in self.household.flex_loads("setpoint").items():
            if curtail:
                cut = self.ac_reduction * float(arr[t])
                reduction += cut
                self.ac_avoided_kwh += cut * step_h
                self.ac_queue_kwh += cut * step_h * self.ac_rebound_share
            elif self.ac_queue_kwh > 1e-12:
                extra = min(self.ac_reduction * self._rated_kw(name), self.ac_queue_kwh / step_h)
                self.ac_queue_kwh -= extra * step_h
                rebound += extra
                self.ac_rebound_kwh += extra * step_h

        return reduction, rebound

    def pending_kwh(self):
        return sum(self.queue_kwh.values()) + self.ac_queue_kwh


class ApplianceFlexFleet:
    """Vectorised ApplianceFlex across all homes on a DT (same rules).

    ``mask`` marks homes with an actuator that have not opted out. ``rated_kw`` maps each
    deferrable appliance to per-home rated power; ``ac_rated_kw`` is per-home AC power.
    Queued energy carries over from one day to the next.
    """

    def __init__(self, cfg, mask, rated_kw, ac_rated_kw, step_h):
        self.mask = np.asarray(mask, dtype=bool)
        n = len(self.mask)
        self.names = list(rated_kw)
        self.rated = rated_kw
        self.ac_rated = ac_rated_kw
        self.step_h = step_h
        self.max_steps = {a: int(cfg["max_defer_min"].get(a, 60) // (step_h * 60)) for a in self.names}
        self.ac_reduction = cfg["ac_setpoint_reduction"]
        self.ac_rebound_share = cfg["ac_rebound_share"]
        self.stagger = cfg["rebound_stagger_steps"]
        self.queue = {a: np.zeros(n) for a in self.names}
        self.deferred_steps = {a: np.zeros(n, dtype=int) for a in self.names}
        self.rebound_start = {a: np.full(n, -1) for a in self.names}
        self.ac_queue = np.zeros(n)
        self.scheduled_kwh = np.zeros(n)
        self.served_kwh = np.zeros(n)
        self.deferred_kwh = np.zeros(n)
        self.rebound_kwh = np.zeros(n)
        self.ac_avoided_kwh = np.zeros(n)
        self.ac_rebound_kwh = np.zeros(n)
        self.curtailed_steps = np.zeros(n, dtype=int)

    def potential_kw(self, loads, t):
        kw = np.zeros(len(self.mask))
        for a in self.names:
            sched = loads.defer.get(a)
            if sched is None:
                continue
            ok = (sched[:, t] > 0) & (self.deferred_steps[a] < self.max_steps[a])
            kw += np.where(ok, sched[:, t], 0.0)
        kw += self.ac_reduction * loads.setpoint[:, t]
        return np.where(self.mask, kw, 0.0)

    def pending_rebound_kw(self, loads, t):
        """Rebound that would be drawn this step if nothing were held (upper bound)."""
        holdable, forced = self.rebound_split(loads, t)
        return holdable + forced

    def rebound_split(self, loads, t):
        """(holdable kW, forced kW): queued energy that may still wait, and energy whose
        appliance has reached its maximum deferral and must run now."""
        n = len(self.mask)
        holdable, forced = np.zeros(n), np.zeros(n)
        for a in self.names:
            sched = loads.defer[a][:, t] if a in loads.defer else 0.0
            kw = np.minimum(np.maximum(0.0, self.rated[a] - sched), self.queue[a] / self.step_h)
            can_wait = self.deferred_steps[a] < self.max_steps[a]
            holdable += np.where(can_wait, kw, 0.0)
            forced += np.where(can_wait, 0.0, kw)
        holdable += np.minimum(self.ac_reduction * self.ac_rated, self.ac_queue / self.step_h)
        return np.where(self.mask, holdable, 0.0), np.where(self.mask, forced, 0.0)

    def step(self, loads, t, curtail, hold, rng):
        """Advance one step for all homes.

        ``curtail``: homes asked to shed now. ``hold``: homes whose queued energy must keep
        waiting this step (the DT is short of supply). Returns (reduction kW, rebound kW).
        """
        n = len(self.mask)
        curtail = curtail & self.mask
        hold = hold & self.mask
        reduction = np.zeros(n)
        rebound = np.zeros(n)
        self.curtailed_steps += curtail
        for a in self.names:
            sched = loads.defer[a][:, t] if a in loads.defer else np.zeros(n)
            self.scheduled_kwh += sched * self.step_h
            can_defer = self.deferred_steps[a] < self.max_steps[a]
            defer_now = curtail & (sched > 0) & can_defer
            self.queue[a] += np.where(defer_now, sched * self.step_h, 0.0)
            self.deferred_steps[a] += defer_now
            self.deferred_kwh += np.where(defer_now, sched * self.step_h, 0.0)
            self.rebound_start[a][defer_now] = -1
            reduction += np.where(defer_now, sched, 0.0)

            served = np.where(defer_now, 0.0, sched)
            has_q = (~defer_now) & (self.queue[a] > 1e-12)
            holding = has_q & ((curtail & can_defer) | (hold & can_defer))
            # Count waiting steps while held, so nothing waits beyond max_defer_min.
            self.deferred_steps[a] += holding
            assign = has_q & ~holding & (self.rebound_start[a] < 0)
            self.rebound_start[a][assign] = t + rng.integers(0, self.stagger + 1, assign.sum())
            go = has_q & ~holding & (t >= self.rebound_start[a]) & (self.rebound_start[a] >= 0)
            extra = np.where(go, np.minimum(np.maximum(0.0, self.rated[a] - sched),
                                            self.queue[a] / self.step_h), 0.0)
            self.queue[a] -= extra * self.step_h
            served += extra
            rebound += extra
            self.rebound_kwh += extra * self.step_h
            done = go & (self.queue[a] <= 1e-9)
            self.queue[a][done] = 0.0
            self.deferred_steps[a][done] = 0
            self.rebound_start[a][done] = -1
            idle = ~curtail & ~has_q & (self.queue[a] <= 1e-12)
            self.deferred_steps[a][idle] = 0
            self.served_kwh += served * self.step_h

        cut = np.where(curtail, self.ac_reduction * loads.setpoint[:, t], 0.0)
        reduction += cut
        self.ac_avoided_kwh += cut * self.step_h
        self.ac_queue += cut * self.step_h * self.ac_rebound_share
        release = ~curtail & ~hold & (self.ac_queue > 1e-12)
        extra = np.where(release, np.minimum(self.ac_reduction * self.ac_rated, self.ac_queue / self.step_h), 0.0)
        self.ac_queue -= extra * self.step_h
        rebound += extra
        self.ac_rebound_kwh += extra * self.step_h
        return reduction, rebound

    def pending_kwh(self):
        return sum(q.sum() for q in self.queue.values()) + self.ac_queue.sum()
