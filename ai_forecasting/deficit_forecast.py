"""From a net-demand forecast to a deficit forecast and an operating decision.

Deficit forecast. The shortfall a DT will face depends on (a) its demand and (b) whether
the grid operator orders a cut. For (b) we use the same statistical shortfall model that
drives the simulation (event rate rising with demand stress and cloudiness, durations
from ESMI, depth range). The forecaster knows those rates but not the random draws, much
as an SLDC's day-ahead adequacy assessment knows the risk but not the outcome. Demand
uncertainty comes from the net-demand quantile forecast: we sample demand paths between
P10, P50 and P90 and shortfall events, and report quantiles of the deficit per block and
of the evening deficit energy.

Decision. The community battery can either sit fully charged for deficits (safest, earns
nothing on normal days) or shave the DT's evening peak (18:00-22:00), which is the
dearest Time-of-Day block, keeping back a reserve for deficits. The reserve is:
  * fixed:          a fixed share of usable energy (no forecast)
  * forecast-based: a quantile of the forecast evening deficit energy
"""
import numpy as np

from simulation.deficit import ShortfallModel, day_seed

STEPS = 96


def deficit_quantiles(model: ShortfallModel, demand_q, solar_idx, cloudiness, n_samples=400,
                      seed=0, day=0, window=(68, 96)):
    """Quantiles of the deficit (kW per block) and of deficit energy in ``window``.

    demand_q: (3, 96) P10/P50/P90 of unmanaged net demand.
    Returns dict with 'block_q' (3, 96) and 'window_kwh_q' {0.1, 0.5, 0.9}.
    """
    rng = np.random.default_rng(day_seed(seed, day, "forecast"))
    p10, p50, p90 = demand_q
    gaps = np.zeros((n_samples, STEPS))
    for k in range(n_samples):
        u = rng.random()
        path = np.where(u < 0.5, p10 + (p50 - p10) * (u / 0.5), p50 + (p90 - p50) * ((u - 0.5) / 0.5))
        stress, residual = model.stress(path, solar_idx, cloudiness)
        n = rng.poisson(model.rate * stress)
        if n == 0:
            continue
        w = np.clip(residual / max(residual.max(), 1e-9), 0, None) ** model.p
        w = w / w.sum() if w.sum() > 0 else np.full(STEPS, 1 / STEPS)
        mix = model.duration_mix
        events = []
        for _ in range(n):
            start = int(rng.choice(STEPS, p=w))
            x = rng.random()
            minutes = rng.uniform(15, 60) if x < mix["under_1h"] else (
                rng.uniform(60, 180) if x < mix["under_1h"] + mix["one_to_3h"] else rng.uniform(180, 300))
            events.append((start, max(1, int(round(minutes / model.step_min))), float(rng.uniform(*model.depth))))
        depth = model.depth_profile(events, STEPS)
        gaps[k] = depth * np.maximum(path, 0)
    w0, w1 = window
    energy = gaps[:, w0:w1].sum(axis=1) * 0.25
    return {
        "block_q": np.quantile(gaps, [0.1, 0.5, 0.9], axis=0),
        "window_kwh_q": {q: float(np.quantile(energy, q)) for q in (0.1, 0.5, 0.9, 0.97, 0.995)},
        "p_any_deficit": float((gaps.sum(axis=1) > 0).mean()),
    }


class BatteryPlanner:
    """Per-day community-battery plan for the engine (``plan_day``)."""

    def __init__(self, mode, forecasts=None, quantile=0.9, fixed_share=0.5, arbitrage=True):
        self.mode = mode                  # 'full_reserve' | 'fixed' | 'forecast'
        self.forecasts = forecasts or {}  # day -> deficit_quantiles output
        self.quantile = quantile
        self.fixed_share = fixed_share
        self.arbitrage = arbitrage

    def plan_day(self, scenario, day, date):
        cb = scenario.cfg["community_battery"]
        usable = (cb["soc_max"] - cb["soc_min"]) * cb["capacity_kwh"]
        if self.mode == "full_reserve" or not self.arbitrage:
            reserve = usable
        elif self.mode == "fixed":
            reserve = self.fixed_share * usable
        else:
            f = self.forecasts.get(day)
            reserve = usable if f is None else min(usable, f["window_kwh_q"][self.quantile])
        return {"event_energy_kwh": None, "charge_target_soc": None, "reserve_kwh": reserve,
                "arbitrage_window_h": (18, 22) if self.arbitrage else None}
