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
