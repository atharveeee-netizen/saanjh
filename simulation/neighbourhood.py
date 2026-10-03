"""Build the set of homes on a distribution transformer from a scenario."""
import numpy as np

from simulation.mechanisms.appliance_flex import ApplianceFlex
from simulation.mechanisms.inverter_relay import InverterBatteryFlex
from simulation.models.household import Household


def segment_counts(num_homes, mix):
    """Split ``num_homes`` across segments by largest remainder."""
    names = list(mix)
    raw = np.array([mix[n] * num_homes for n in names], dtype=float)
    counts = np.floor(raw).astype(int)
    for i in np.argsort(-(raw - counts))[: num_homes - counts.sum()]:
        counts[i] += 1
    return dict(zip(names, counts.tolist()))


def build_households(cfg, scenario, rng):
    """Create households with ownership drawn from each segment's probabilities."""
    homes = []
    counts = segment_counts(scenario["num_homes"], scenario["segment_mix"])
    overrides = scenario.get("ownership_overrides", {})
    for seg_name, count in counts.items():
        seg = cfg["segments"][seg_name]
        own = {**seg["ownership"], **overrides.get(seg_name, {})}
        for _ in range(count):
            hid = len(homes)
            homes.append(Household(
                hid, seg_name, seg, rng,
                has_inverter=rng.random() < own.get("inverter", 0.0),
                has_pv=rng.random() < own.get("rooftop_pv", 0.0),
                has_actuator=rng.random() < own.get("actuator", 0.0),
                critical_flag=rng.random() < own.get("critical_load", 0.0),
            ))

    n_opt_out = min(scenario.get("opted_out_homes", 0), len(homes))
    for i in rng.choice(len(homes), n_opt_out, replace=False):
        homes[int(i)].opted_out = True

    for h in homes:
        if h.has_inverter:
            h.inverter = InverterBatteryFlex(cfg["inverter_battery"])
        if h.has_actuator:
            h.appliance_flex = ApplianceFlex(h, cfg["appliance_flex"])
    return homes
