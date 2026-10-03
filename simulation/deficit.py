"""Supply-shortfall model and the baseline load-shedding policy.

When regional supply cannot meet demand (typically as solar ramps down into the evening
peak, on hot high-demand days and on cloudy days), the grid operator orders DISCOMs to
cut load. We model these as shortfall EVENTS. During an event the DT must cut a fraction
s of the load it would otherwise draw:

    allocation A_t = (1 - s_t) x unmanaged DT demand_t        (no cap outside events)

Event generation per day (seeded, identical for every policy):
* count ~ Poisson(rate x stress_day), with
  stress_day = (day's peak residual demand / D_ref)^2 x (1 + cloudiness_day)
  so hot, high-demand days and cloudy days see more shortfalls  [ASSUMPTION: form]
* start time weighted by (residual demand_t / its daily max)^p, where
  residual = demand - SOLAR_SHARE x D_ref x solar availability (NASA POWER, REAL DATA)
* duration drawn from the ESMI outage-duration mix (REAL DATA, published): 30% under 1 h,
  33% 1-3 h, 37% over 3 h (capped at 5 h  [ASSUMPTION])
* depth s ~ Uniform(DEPTH_MIN, DEPTH_MAX)  [ASSUMPTION, varied in sensitivity runs]

``rate`` and ``p`` are calibrated so the BASELINE policy reproduces deficit_share x the
published ESMI evening (17:00-23:00) outage minutes exactly and comes as close as
possible to the all-day figure. Labelled CALIBRATED TO REAL DATA.

BASELINE policy (what DISCOMs do today): during a shortfall, whole LT feeders of the DT
are disconnected in rotation (least cumulative shedding first) until the remaining
demand fits the allocation. Every home on a shed feeder loses all supply; homes with
inverters fall back on their own batteries. Shedding by LT feeder is finer than the
common practice of shedding whole 11 kV feeders, so the baseline is not a strawman.
"""
import zlib

import numpy as np

SOLAR_SHARE = 0.3        # [ASSUMPTION] solar share of regional supply at full sun
DEPTH_MIN, DEPTH_MAX = 0.15, 0.45   # [ASSUMPTION] fraction of load to cut during an event
MAX_EVENT_MIN = 300      # [ASSUMPTION]
NO_LIMIT = 1e9


def day_seed(seed, day_index, stream):
    return zlib.crc32(f"{seed}/{day_index}/{stream}".encode())


class ShortfallModel:
    def __init__(self, rate, concentration, d_ref_kw, duration_mix, step_min=15,
                 depth=(DEPTH_MIN, DEPTH_MAX)):
        self.rate = rate
        self.p = concentration
        self.d_ref_kw = d_ref_kw
        self.duration_mix = duration_mix
        self.step_min = step_min
        self.depth = depth

    def stress(self, demand_kw, solar_idx, cloudiness):
        residual = demand_kw - SOLAR_SHARE * self.d_ref_kw * solar_idx
        return (max(residual.max(), 0) / self.d_ref_kw) ** 2 * (1 + cloudiness), residual

    def events(self, seed, day_index, demand_kw, solar_idx, cloudiness):
        """Return a list of (start_step, n_steps, depth) for one day."""
        rng = np.random.default_rng(day_seed(seed, day_index, "shortfall"))
        stress, residual = self.stress(demand_kw, solar_idx, cloudiness)
        n = rng.poisson(self.rate * stress)
        if n == 0:
            return []
        w = np.clip(residual / max(residual.max(), 1e-9), 0, None) ** self.p
        w = w / w.sum() if w.sum() > 0 else np.full(len(w), 1 / len(w))
        mix = self.duration_mix
        out = []
        for _ in range(n):
            start = int(rng.choice(len(w), p=w))
            u = rng.random()
            if u < mix["under_1h"]:
                minutes = rng.uniform(15, 60)
            elif u < mix["under_1h"] + mix["one_to_3h"]:
                minutes = rng.uniform(60, 180)
            else:
                minutes = rng.uniform(180, MAX_EVENT_MIN)
            steps = max(1, int(round(minutes / self.step_min)))
            out.append((start, steps, float(rng.uniform(*self.depth))))
        return out

    def depth_profile(self, events, steps):
        """Cut fraction per block; overlapping events take the deeper cut. Events that
        run past midnight are truncated (the next day's events are drawn separately)."""
        s = np.zeros(steps)
        for start, n, depth in events:
            s[start:start + n] = np.maximum(s[start:start + n], depth)
        return s

    def allocation(self, depth, demand_kw):
        return np.where(depth > 0, (1 - depth) * demand_kw, NO_LIMIT)


def rotational_shedding(feeder_kw, allocation_kw, cum_shed):
    """Baseline decision for one block.

    feeder_kw: demand per LT feeder; cum_shed: cumulative shed blocks per feeder
    (updated in place). Returns a boolean mask of shed feeders.
    """
    shed = np.zeros(len(feeder_kw), dtype=bool)
    remaining = feeder_kw.sum()
    if remaining <= allocation_kw:
        return shed
    for f in np.lexsort((-feeder_kw, cum_shed)):
        if remaining <= allocation_kw:
            break
        shed[f] = True
        remaining -= feeder_kw[f]
    cum_shed += shed
    return shed


def baseline_outage_minutes(feeder_matrix, homes_per_feeder, depth, hours, step_min,
                            evening=(17, 23)):
    """Mean outage minutes per home per day (all day, evening window)."""
    k, T = feeder_matrix.shape
    cum = np.zeros(k)
    total = feeder_matrix.sum(axis=0)
    shed_homes = np.zeros(T)
    for t in np.where(depth > 0)[0]:
        mask = rotational_shedding(feeder_matrix[:, t], (1 - depth[t]) * total[t], cum)
        shed_homes[t] = homes_per_feeder[mask].sum()
    n = homes_per_feeder.sum()
    days = T * step_min / 1440
    per_home = shed_homes / n * step_min
    ev = (hours >= evening[0]) & (hours < evening[1])
    return per_home.sum() / days, per_home[ev].sum() / days


def calibrate_shortfall(feeder_matrix, homes_per_feeder, solar_idx_days, cloudiness_days,
                        hours, step_min, target_daily, target_evening, d_ref_kw,
                        duration_mix, steps_per_day=96, seed=0):
    """Find (rate, p): bisect ``rate`` to hit the evening target for each p on a grid,
    keep the p whose all-day minutes are closest to the daily target."""
    days = feeder_matrix.shape[1] // steps_per_day
    total = feeder_matrix.sum(axis=0)

    def depth_series(rate, p):
        m = ShortfallModel(rate, p, d_ref_kw, duration_mix, step_min)
        out = []
        for d in range(days):
            sl = slice(d * steps_per_day, (d + 1) * steps_per_day)
            ev = m.events(seed, d, total[sl], solar_idx_days[d], cloudiness_days[d])
            out.append(m.depth_profile(ev, steps_per_day))
        return np.concatenate(out)

    best = None
    for p in (0.0, 1.0, 2.0, 4.0, 6.0, 8.0, 12.0):
        lo, hi = 0.0, 8.0
        for _ in range(22):
            mid = (lo + hi) / 2
            _, evening = baseline_outage_minutes(feeder_matrix, homes_per_feeder,
                                                 depth_series(mid, p), hours, step_min)
            if evening > target_evening:
                hi = mid
            else:
                lo = mid
        rate = (lo + hi) / 2
        daily, evening = baseline_outage_minutes(feeder_matrix, homes_per_feeder,
                                                 depth_series(rate, p), hours, step_min)
        err = abs(daily - target_daily)
        if best is None or err < best["daily_error"]:
            best = {"rate": float(rate), "concentration": float(p),
                    "daily_minutes": float(daily), "evening_minutes": float(evening),
                    "daily_error": float(err)}
    best.update({"target_daily_minutes": float(target_daily),
                 "target_evening_minutes": float(target_evening), "d_ref_kw": float(d_ref_kw)})
    return best
