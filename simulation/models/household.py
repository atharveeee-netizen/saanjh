"""Household load model.

Each home owns a set of appliances drawn from its segment's ownership probabilities.
A day's load for every appliance is generated up front as an array of kW per step, so a
baseline run and a SAANJH run on the same seed see exactly the same demand.
"""
import numpy as np


class Household:
    def __init__(self, hid, segment, seg_cfg, rng, has_inverter, has_pv, has_actuator,
                 opted_out=False, critical_flag=False):
        self.hid = hid
        self.segment = segment
        self.seg_cfg = seg_cfg
        self.has_inverter = has_inverter
        self.has_pv = has_pv
        self.pv_kwp = seg_cfg.get("pv_kwp", 1.0) if has_pv else 0.0
        self.has_actuator = has_actuator
        self.opted_out = opted_out
        self.critical_flag = critical_flag

        self.owned = {
            name: (rng.random() < spec.get("own", 1.0))
            for name, spec in seg_cfg["appliances"].items()
        }
        # Per-home scale factors so homes differ even with identical schedules.
        self.scale = {name: rng.uniform(0.8, 1.2) for name in seg_cfg["appliances"]}
        self.shift_h = {name: rng.uniform(-0.25, 0.25) for name in seg_cfg["appliances"]}
        # Home-level usage intensity (mean 1) for continuous loads; sessions keep their
        # rated power since an appliance draws its rating when on.
        sigma = seg_cfg.get("home_intensity_sigma", 0.0)
        self.intensity = float(rng.lognormal(-sigma ** 2 / 2, sigma)) if sigma > 0 else 1.0

        self.loads = {}       # name -> np.ndarray of kW per step for the current day
        self.inverter = None  # set by the engine when the home has an inverter
        self.appliance_flex = None

    @property
    def label(self):
        return f"H-{self.hid + 1:03d}"

    # ------------------------------------------------------------------ load generation
    def generate_day(self, rng, steps_per_day, step_h, multipliers=None, start_hour=0.0,
                     season=None):
        """Generate kW arrays for every owned appliance for one day.

        ``multipliers`` scales appliances by name for the day (e.g. a heatwave).
        ``season`` applies each appliance's per-season factor: kW for profiles, daily
        probability for sessions.
        ``start_hour`` lets a run start at a clock time other than midnight (the evening
        case runs noon to noon so that rebound and recharge finish inside the run).
        Sessions that run past the end of the day wrap to its start; for a run of similar
        days this is equivalent to spilling into the next day.
        """
        multipliers = multipliers or {}
        hours = (start_hour + np.arange(steps_per_day) * step_h) % 24
        self.loads = {}
        for name, spec in self.seg_cfg["appliances"].items():
            if not self.owned[name]:
                continue
            seasonal = spec.get("season", {}).get(season, 1.0) if season else 1.0
            mult = multipliers.get(name, 1.0) * self.scale[name] * self.intensity
            if mult <= 0 or seasonal <= 0:
                continue
            arr = np.zeros(steps_per_day)
            if "profile" in spec:
                for start, end, kw in spec["profile"]:
                    s = start + self.shift_h[name] if 0 < start < 24 else start
                    e = end + self.shift_h[name] if 0 < end < 24 else end
                    arr[(hours >= s) & (hours < e)] += kw * mult * seasonal
                # Small step-to-step variation around the profile.
                arr *= rng.uniform(0.9, 1.1, steps_per_day)
            if "session" in spec:
                sess = spec["session"]
                p = min(1.0, sess.get("probability", 1.0) * seasonal)
                for _ in range(sess.get("per_day", 1)):
                    if rng.random() > p:
                        continue
                    start_h = rng.normal(sess["start_mean"], sess.get("start_sd", 0.0))
                    start = int(round(((start_h - start_hour) % 24) / step_h)) % steps_per_day
                    n = max(1, int(round(sess["duration_min"] / (step_h * 60))))
                    idx = np.arange(start, start + n) % steps_per_day
                    arr[idx] += sess["kw"] * multipliers.get(name, 1.0) * self.scale[name]
            self.loads[name] = arr
        return self.loads

    # ------------------------------------------------------------------ load queries
    def _sum(self, t, predicate):
        return float(sum(arr[t] for name, arr in self.loads.items()
                         if predicate(self.seg_cfg["appliances"][name])))

    def demand_kw(self, t):
        """Unmanaged appliance demand at step t (before PV, flexibility or limits)."""
        return float(sum(arr[t] for arr in self.loads.values()))

    def critical_kw(self, t):
        return self._sum(t, lambda s: s.get("critical", False))

    def backed_up_kw(self, t):
        """Load on the circuits wired through the home inverter."""
        return self._sum(t, lambda s: s.get("backed_up", False))

    def flex_loads(self, kind):
        return {name: arr for name, arr in self.loads.items()
                if self.seg_cfg["appliances"][name].get("flex") == kind}
