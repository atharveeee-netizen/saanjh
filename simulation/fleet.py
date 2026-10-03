"""Vectorised household fleet for year-long runs.

The same load model as ``simulation/models/household.py`` (profiles, sessions, seasons,
per-home scale, shift and intensity), but every quantity is an array over homes so a
year of 15-minute blocks for a few hundred homes runs in seconds.
"""
from dataclasses import dataclass, field

import numpy as np

from simulation.neighbourhood import segment_counts


@dataclass
class DayLoads:
    """Load matrices (homes x steps, kW) for one day."""
    total: np.ndarray
    critical: np.ndarray
    backed_up: np.ndarray
    defer: dict = field(default_factory=dict)      # appliance -> matrix
    setpoint: np.ndarray = None                    # AC load that a setpoint raise can trim
    by_appliance: dict = field(default_factory=dict)


class HomeFleet:
    def __init__(self, cfg, scenario, rng, n_lt_feeders=4):
        self.cfg = cfg
        counts = segment_counts(scenario["num_homes"], scenario["segment_mix"])
        segs = [s for s, c in counts.items() for _ in range(c)]
        self.n = n = len(segs)
        self.segment = np.array(segs)
        self.segment_names = [s for s in counts if counts[s] > 0]
        overrides = scenario.get("ownership_overrides", {})

        def draw(key):
            p = np.array([{**cfg["segments"][s]["ownership"], **overrides.get(s, {})}.get(key, 0.0)
                          for s in segs])
            return rng.random(n) < p

        self.has_inverter = draw("inverter")
        self.has_pv = draw("rooftop_pv")
        self.has_actuator = draw("actuator")
        self.critical = draw("critical_load")
        self.pv_kwp = np.where(self.has_pv,
                               [cfg["segments"][s].get("pv_kwp", 0.0) for s in segs], 0.0)
        sig = np.array([cfg["segments"][s].get("home_intensity_sigma", 0.0) for s in segs])
        self.intensity = np.where(sig > 0, rng.lognormal(-sig ** 2 / 2, np.maximum(sig, 1e-9)), 1.0)

        self.appliances = sorted({a for s in self.segment_names for a in cfg["segments"][s]["appliances"]})
        self.owned, self.scale, self.shift = {}, {}, {}
        for a in self.appliances:
            own_p = np.array([cfg["segments"][s]["appliances"].get(a, {}).get("own", 0.0) for s in segs])
            self.owned[a] = rng.random(n) < own_p
            self.scale[a] = rng.uniform(0.8, 1.2, n)
            self.shift[a] = rng.uniform(-0.25, 0.25, n)

        self.opted_out = np.zeros(n, dtype=bool)
        k = min(scenario.get("opted_out_homes", 0), n)
        self.opted_out[rng.choice(n, k, replace=False)] = True
        self.n_lt_feeders = n_lt_feeders
        self.feeder = rng.permutation(n) % n_lt_feeders

    # ------------------------------------------------------------------
    def _spec(self, segment, appliance):
        return self.cfg["segments"][segment]["appliances"].get(appliance)

    def rated_kw(self, appliance):
        """Per-home rated power of a session appliance (0 where not owned)."""
        kw = np.zeros(self.n)
        for s in self.segment_names:
            spec = self._spec(s, appliance)
            if spec and "session" in spec:
                rows = self.segment == s
                kw[rows] = spec["session"]["kw"] * self.scale[appliance][rows]
        return np.where(self.owned[appliance], kw, 0.0)

    def flex_names(self, kind):
        return [a for a in self.appliances
                if any((self._spec(s, a) or {}).get("flex") == kind for s in self.segment_names)]

    def generate_day(self, rng, steps, step_h, season=None, multipliers=None, start_hour=0.0):
        multipliers = multipliers or {}
        hours = (start_hour + np.arange(steps) * step_h) % 24
        T = steps
        by_app = {}
        total = np.zeros((self.n, T))
        critical = np.zeros((self.n, T))
        backed = np.zeros((self.n, T))
        defer, setpoint = {}, np.zeros((self.n, T))

        for a in self.appliances:
            arr_a = np.zeros((self.n, T))
            for s in self.segment_names:
                spec = self._spec(s, a)
                if not spec:
                    continue
                rows = np.where((self.segment == s) & self.owned[a])[0]
                if not len(rows):
                    continue
                seasonal = spec.get("season", {}).get(season, 1.0) if season else 1.0
                m_app = multipliers.get(a, 1.0)
                if seasonal <= 0 or m_app <= 0:
                    continue
                if "profile" in spec:
                    mult = (m_app * self.scale[a][rows] * self.intensity[rows] * seasonal)[:, None]
                    sub = np.zeros((len(rows), T))
                    for start, end, kw in spec["profile"]:
                        sh = self.shift[a][rows][:, None]
                        st = start + sh if 0 < start < 24 else np.full_like(sh, start)
                        en = end + sh if 0 < end < 24 else np.full_like(sh, end)
                        sub += kw * ((hours[None, :] >= st) & (hours[None, :] < en))
                    sub *= mult * rng.uniform(0.9, 1.1, (len(rows), T))
                    arr_a[rows] += sub
                if "session" in spec:
                    sess = spec["session"]
                    p = min(1.0, sess.get("probability", 1.0) * seasonal)
                    for _ in range(sess.get("per_day", 1)):
                        on = rng.random(len(rows)) < p
                        start_h = rng.normal(sess["start_mean"], sess.get("start_sd", 0.0), len(rows))
                        start = np.rint(((start_h - start_hour) % 24) / step_h).astype(int) % T
                        n_steps = max(1, int(round(sess["duration_min"] / (step_h * 60))))
                        idx = (start[:, None] + np.arange(n_steps)[None, :]) % T
                        kw = (sess["kw"] * m_app * self.scale[a][rows] * on)[:, None]
                        np.add.at(arr_a, (rows[:, None].repeat(n_steps, 1), idx),
                                  np.broadcast_to(kw, idx.shape))
                flags_rows = rows
                if spec.get("critical"):
                    critical[flags_rows] += arr_a[flags_rows]
                if spec.get("backed_up"):
                    backed[flags_rows] += arr_a[flags_rows]
                if spec.get("flex") == "defer":
                    defer.setdefault(a, np.zeros((self.n, T)))[flags_rows] += arr_a[flags_rows]
                if spec.get("flex") == "setpoint":
                    setpoint[flags_rows] += arr_a[flags_rows]
            total += arr_a
            by_app[a] = arr_a
        return DayLoads(total=total, critical=critical, backed_up=backed, defer=defer,
                        setpoint=setpoint, by_appliance=by_app)
