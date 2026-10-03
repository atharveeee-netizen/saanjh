"""Year-long DT simulation for a scenario under the BASELINE or SAANJH policy.

Both policies see identical inputs for a given seed: the same homes, the same appliance
use (generated per day from seeded streams), the same weather and the same supply
allocation. Per-block physics:

    home grid draw = appliance demand - rooftop PV - battery-served load
                     - deferred appliance load + rebound + inverter recharge
    (shed homes draw nothing; their PV trips off; inverters carry backed-up circuits)
    DT net load    = sum of home draws - community battery discharge + its charging

Energy balance per home and block (tested):
    desired = served from grid/PV + served from own battery + deferred
              + curtailed by the band + unserved while disconnected
"""
import json
import os
import zlib
from dataclasses import dataclass

import numpy as np
import pandas as pd

from simulation.config import load_config, repo_path
from simulation.deficit import (ShortfallModel, calibrate_shortfall, day_seed,
                                rotational_shedding)
from simulation.dispatcher import DeficitDispatcher
from simulation.fleet import HomeFleet
from simulation.mechanisms.appliance_flex import ApplianceFlexFleet
from simulation.mechanisms.community_battery import CommunityBattery
from simulation.mechanisms.essential_band import EssentialBand
from simulation.mechanisms.inverter_relay import InverterFleet
from simulation.weather import Weather

COOLING = ("fans", "cooler", "ac", "ac_day")
CALIBRATION_CACHE = repo_path("simulation", "results", "allocation_calibration.json")


def _clock(hour):
    return f"{int(hour):02d}:{int(round((hour % 1) * 60)):02d}"


@dataclass
class RunResult:
    scenario: str
    policy: str
    seed: int
    timeseries: pd.DataFrame
    homes: pd.DataFrame
    log: list
    ledger: dict
    calibration: dict


class Scenario:
    """Everything that is identical across policies for one scenario and seed."""

    def __init__(self, name, seed=0, cfg=None, overrides=None, n_days=None, weather=None):
        self.cfg = cfg or load_config(overrides)
        self.name = name
        self.sc = self.cfg["scenarios"][name]
        self.seed = seed
        self.step_h = self.cfg["simulation"]["step_min"] / 60
        self.steps = int(round(24 / self.step_h))
        site = self.cfg["site"]
        self.weather = weather or Weather(site["name"], site["year"], self.steps)
        self.dates = self.weather.dates[: n_days or len(self.weather.dates)]
        self.pv_max = float(self.weather.q["pv_kw_per_kwp"].max())
        rng = np.random.default_rng(zlib.crc32(f"{name}/{seed}/fleet".encode()))
        self.fleet = HomeFleet(self.cfg, self.sc, rng, self.cfg["grid"]["lt_feeders"])
        self.rating_kw = self.sc.get("transformer_kva", self.cfg["transformer"]["rating_kva"]) \
            * self.cfg["electrical"]["power_factor"]
        self.dt_limit_kw = self.rating_kw * self.cfg["transformer"]["dispatch_target_pct"] / 100
        self.calibration = self._allocation()

    # ------------------------------------------------------------ inputs per day
    def day_inputs(self, day_index):
        date = self.dates[day_index]
        info = self.weather.days.loc[date]
        mult = {}
        if info["day_type"] == "heatwave":
            m = self.cfg["dispatch"]["heatwave_cooling_multiplier"]
            mult = {a: m for a in COOLING}
        rng = np.random.default_rng(day_seed(self.seed, day_index, "load"))
        loads = self.fleet.generate_day(rng, self.steps, self.step_h, info["season"], mult)
        pvk, temp = self.weather.day(date)
        return date, info, loads, pvk, temp

    def _unmanaged_feeder_matrix(self):
        k = self.fleet.n_lt_feeders
        cols = []
        for d in range(len(self.dates)):
            _, _, loads, pvk, _ = self.day_inputs(d)
            net = loads.total - self.fleet.pv_kwp[:, None] * pvk[None, :]
            cols.append(np.vstack([net[self.fleet.feeder == f].sum(axis=0) for f in range(k)]))
        return np.hstack(cols)

    def _make_model(self, res):
        oc = self.cfg["outage_calibration"]
        depth = tuple(self.sc.get("shortfall_depth", self.cfg["dispatch"].get("shortfall_depth", [0.15, 0.45])))
        return ShortfallModel(res["rate"], res["concentration"], res["d_ref_kw"], oc["duration_mix"],
                              self.cfg["simulation"]["step_min"], depth)

    def _allocation(self):
        cache = {}
        if os.path.exists(CALIBRATION_CACHE):
            with open(CALIBRATION_CACHE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        oc = self.cfg["outage_calibration"]
        cat = oc["categories"][self.sc["esmi_category"]]
        share = oc["deficit_share"]
        sig = json.dumps([cat, share, oc["duration_mix"], self.sc, self.cfg["segments"], self.cfg["grid"],
                          self.cfg["site"], self.cfg["dispatch"].get("shortfall_depth"), len(self.dates)],
                         sort_keys=True, default=str)
        sig = zlib.crc32(sig.encode())
        key = f"{self.name}:{sig}"
        if key in cache and cache[key].get("signature") == sig:
            self.alloc = self._make_model(cache[key])
            return cache[key]
        # Calibrate on seed 0 so every Monte Carlo seed shares one supply model.
        if self.seed != 0:
            ref = Scenario(self.name, 0, self.cfg, n_days=len(self.dates), weather=self.weather)
            self.alloc = self._make_model(ref.calibration)
            return ref.calibration
        fm = self._unmanaged_feeder_matrix()
        d_ref = float(np.percentile(fm.sum(axis=0), 99))
        solar_days = [self.weather.day(d)[0] / self.pv_max for d in self.dates]
        cloud_days = [float(self.weather.days.loc[d, "cloudiness"]) for d in self.dates]
        hours = np.tile(np.arange(self.steps) * self.step_h, len(self.dates))
        homes_per_feeder = np.bincount(self.fleet.feeder, minlength=self.fleet.n_lt_feeders)
        res = calibrate_shortfall(fm, homes_per_feeder, solar_days, cloud_days, hours,
                                  self.cfg["simulation"]["step_min"],
                                  share * cat["daily_outage_min"], share * cat["evening_outage_min"],
                                  d_ref, oc["duration_mix"], steps_per_day=self.steps, seed=0)
        res.update({"signature": sig, "esmi_category": self.sc["esmi_category"], "deficit_share": share,
                    "label": "CALIBRATED TO REAL DATA (ESMI Uttar Pradesh published outage minutes)"})
        cache[key] = res
        os.makedirs(os.path.dirname(CALIBRATION_CACHE), exist_ok=True)
        with open(CALIBRATION_CACHE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
        self.alloc = self._make_model(res)
        return res

    def shortfall_day(self, day_index, loads, pvk):
        """Shortfall events, cut depth and allocation for one day (identical for all policies)."""
        total = (loads.total - self.fleet.pv_kwp[:, None] * pvk[None, :]).sum(axis=0)
        cloud = float(self.weather.days.loc[self.dates[day_index], "cloudiness"])
        events = self.alloc.events(self.seed, day_index, total, pvk / self.pv_max, cloud)
        depth = self.alloc.depth_profile(events, self.steps)
        return events, depth, self.alloc.allocation(depth, total)


def run(scenario, policy="saanjh", forecaster=None, cb_override=None, record_days=None):
    """Simulate every day of ``scenario`` under ``policy`` ('baseline' or 'saanjh').

    ``forecaster`` (optional) supplies per-day event-energy estimates and battery charge
    targets (Prompt 6). ``record_days`` limits the per-block timeseries kept in memory.
    """
    cfg, fleet, step_h, T = scenario.cfg, scenario.fleet, scenario.step_h, scenario.steps
    n = fleet.n
    saanjh = policy == "saanjh"
    rng = np.random.default_rng(zlib.crc32(f"{scenario.name}/{scenario.seed}/{policy}/ops".encode()))

    inv = InverterFleet(cfg["inverter_battery"], fleet.has_inverter)
    flex = band = cb = disp = None
    if saanjh:
        mask = fleet.has_actuator & ~fleet.opted_out
        rated = {a: fleet.rated_kw(a) for a in fleet.flex_names("defer")}
        ac_rated = sum((fleet.rated_kw(a) for a in fleet.flex_names("setpoint")), np.zeros(n))
        flex = ApplianceFlexFleet(cfg["appliance_flex"], mask, rated, ac_rated, step_h)
        band = EssentialBand(cfg["essential_band"], fleet.critical)
        cb_cfg = {**cfg["community_battery"], **scenario.sc.get("community_battery", {}), **(cb_override or {})}
        cb = CommunityBattery(cb_cfg) if cb_cfg.get("capacity_kwh", 0) > 0 else None
        disp = DeficitDispatcher(cfg, fleet, inv, flex, band, cb, step_h)

    feeder_cum = np.zeros(fleet.n_lt_feeders)
    acc = {k: np.zeros(n) for k in ("deficit_blocks", "ess_ok_blocks", "shed_blocks", "shed_deficit_blocks",
                                    "banded_blocks", "unserved_kwh", "band_curtailed_kwh", "demand_kwh")}
    rows, log = [], []
    event = None
    max_balance_err = 0.0
    band_excess_max = 0.0
    shed_with_slack = 0
    cb_soc_min, cb_soc_max = np.inf, -np.inf
    overload_blocks, peak_loading = 0, 0.0
    arbitrage_kwh = 0.0
    peak_shaved = []
    record = set(range(len(scenario.dates))) if record_days is None else set(record_days)

    for di in range(len(scenario.dates)):
        date, info, loads, pvk, temp = scenario.day_inputs(di)
        events, depth, alloc = scenario.shortfall_day(di, loads, pvk)
        plan = forecaster.plan_day(scenario, di, date) if (forecaster and saanjh) else None
        for t in range(T):
            hour = t * step_h
            d = loads.total[:, t]
            bu = loads.backed_up[:, t]
            pv = fleet.pv_kwp * pvk[t]
            unmanaged_gap = float((d - pv).sum() - alloc[t])
            in_deficit = unmanaged_gap > 0

            inv.process_releases(t)
            if saanjh:
                limit = min(alloc[t], scenario.dt_limit_kw)
                ev_need = plan["event_energy_kwh"][t] if plan and plan.get("event_energy_kwh") is not None else None
                target = plan.get("charge_target_soc") if plan else None
                dec = disp.plan(loads, t, hour, limit, pv, temp[t], ev_need, target, plan)
                if dec.gap_kw > 0:
                    inv.cancel_release()
                    inv.open(np.where(dec.open_relays)[0])
                else:
                    inv.schedule_release(t, rng)
                shed = dec.shed
                hold, curtail = dec.hold, dec.curtail
                banded = dec.banded
                limits = band.limits_kw(dec.band_level_w) if dec.band_level_w else None
            else:
                limit = alloc[t]
                draw0 = d - pv + inv.expected_recharge_kw(step_h)
                feeder_kw = np.bincount(fleet.feeder, weights=draw0, minlength=fleet.n_lt_feeders)
                shed_f = rotational_shedding(feeder_kw, alloc[t], feeder_cum)
                shed = shed_f[fleet.feeder]
                banded = np.zeros(n, bool)
                limits = None
                dec = None

            grid_on = ~shed
            served_batt = inv.discharge(t, bu, step_h, grid_on)
            if flex is not None:
                red, reb = flex.step(loads, t, curtail & grid_on, hold | shed, rng)
            else:
                red = reb = np.zeros(n)
            pv_on = np.where(grid_on, pv, 0.0)
            draw_pre = np.where(grid_on, d - served_batt - red + reb - pv_on, 0.0)
            if limits is not None:
                capped = np.where(banded, np.minimum(draw_pre, limits), draw_pre)
            else:
                capped = draw_pre
            band_cut = draw_pre - capped
            cap_room = np.where(banded, (limits if limits is not None else 0) - capped, np.inf)
            rech = inv.recharge(step_h, grid_on, cap_room)
            draw = capped + rech

            cb_kw = 0.0
            if cb is not None:
                if dec.cb_kw > 0:
                    cb_kw = cb.discharge(dec.cb_kw, step_h, temp[t])
                elif dec.cb_kw < 0:
                    cb_kw = -cb.charge(-dec.cb_kw, step_h, temp[t], plan.get("charge_target_soc") if plan else None)
                if cb_kw > 0 and dec.gap_kw <= 0:
                    arbitrage_kwh += cb_kw * step_h
                    if dec.peak_before_kw is not None:
                        peak_shaved.append(dec.peak_before_kw)
            net = float(draw.sum() - cb_kw)

            # Correction: if the realised load still exceeds the limit (rebound stagger or
            # rounding), disconnect more homes in the fair order and log it.
            if saanjh and net > limit + 1e-6:
                excess = net - limit
                cand = np.where(grid_on & (draw > 0))[0]
                order = cand[np.lexsort((-draw[cand], disp.cum_shed[cand], fleet.critical[cand]))]
                k = int(np.searchsorted(np.cumsum(draw[order]), excess - 1e-9)) + 1
                extra = order[:k]
                # Their load is now unserved; their batteries were not used this block.
                shed = shed.copy()
                shed[extra] = True
                grid_on = ~shed
                net -= draw[extra].sum()
                draw[extra] = 0.0
                log.append({"date": str(date), "time": _clock(hour), "kind": "correction", "excess_kw": excess,
                            "gap_est": dec.gap_kw, "band": dec.band_level_w, "n_shed": int(dec.shed.sum()),
                            "text": f"Realised load exceeded the limit by {excess:.1f} kW; disconnected "
                                    f"{len(extra)} more homes."})

            loading = abs(net) / scenario.rating_kw * 100
            overload_blocks += loading > 100
            peak_loading = max(peak_loading, loading)
            if saanjh:
                disp.cum_shed += shed
                if limits is not None and (banded & grid_on).any():
                    band_excess_max = max(band_excess_max, float((draw - limits)[banded & grid_on].max()))
                if dec.shed.any():
                    lowest = dec.band_level_w == band.ladder_w[-1]
                    cb_full = cb is None or dec.cb_kw >= dec.covered.get("battery_max_kw", 0.0) - 1e-6
                    shed_with_slack += int(not (lowest and cb_full))
                if cb is not None:
                    cb_soc_min, cb_soc_max = min(cb_soc_min, cb.soc), max(cb_soc_max, cb.soc)

            # Per-home ledgers.
            unserved = np.where(shed, np.maximum(0.0, d - served_batt), 0.0)
            acc["demand_kwh"] += d * step_h
            acc["unserved_kwh"] += unserved * step_h
            acc["band_curtailed_kwh"] += band_cut * step_h
            acc["shed_blocks"] += shed
            acc["banded_blocks"] += banded & grid_on
            if in_deficit:
                acc["deficit_blocks"] += 1
                ess_ok = grid_on | (fleet.has_inverter & (served_batt >= 0.99 * bu))
                acc["ess_ok_blocks"] += ess_ok
                acc["shed_deficit_blocks"] += shed

            # Energy balance per home (module docstring). Connected homes: appliance demand
            # plus rebound = grid/PV supply + own battery + deferred + band curtailment.
            # Disconnected homes: demand = own battery backup + unserved.
            lhs = d + np.where(grid_on, reb, 0.0)
            rhs = np.where(grid_on, (capped - np.where(grid_on, 0.0, 0.0)) + pv_on + served_batt + red + band_cut,
                           served_batt + unserved)
            rhs = np.where(shed & (draw == 0) & grid_on, lhs, rhs)
            max_balance_err = max(max_balance_err, float(np.abs(lhs - rhs).max()))
            assert (band_cut >= -1e-9).all() and (unserved >= -1e-9).all()
            assert (served_batt <= bu + 1e-9).all()

            # Event log (SAANJH): one entry when an event starts, when the action set
            # changes materially, and when it ends.
            if saanjh:
                active = dec.gap_kw > 0
                sig = (dec.band_level_w, bool(shed.any()), dec.battery_mode) if active else None
                if active and event is None:
                    event = {"id": f"EV-{scenario.name[:3].upper()}-{date:%m%d}-{t:02d}", "date": str(date),
                             "start": _clock(hour), "entries": [], "peak_gap_kw": 0.0, "blocks": 0,
                             "homes_banded_max": 0, "homes_shed_max": 0, "battery_kwh": 0.0,
                             "relay_kwh": 0.0, "appliance_kwh": 0.0, "lowest_band_w": None, "sig": None}
                if active:
                    event["blocks"] += 1
                    event["peak_gap_kw"] = max(event["peak_gap_kw"], dec.gap_kw)
                    event["homes_banded_max"] = max(event["homes_banded_max"], int(banded.sum()))
                    event["homes_shed_max"] = max(event["homes_shed_max"], int(shed.sum()))
                    event["battery_kwh"] += max(cb_kw, 0) * step_h
                    event["relay_kwh"] += float(served_batt[grid_on].sum()) * step_h
                    event["appliance_kwh"] += float(red.sum()) * step_h
                    if dec.band_level_w and (event["lowest_band_w"] is None or dec.band_level_w < event["lowest_band_w"]):
                        event["lowest_band_w"] = dec.band_level_w
                    if sig != event["sig"]:
                        event["entries"].append({"time": _clock(hour), "text": dec.reason})
                        event["sig"] = sig
                elif event is not None:
                    event["end"] = _clock(hour)
                    event.pop("sig")
                    log.append({"kind": "event", **event})
                    event = None

            if di in record:
                rows.append({
                    "day": di, "date": str(date), "step": t, "hour": hour,
                    "day_type": info["day_type"], "season": info["season"],
                    "demand_kw": float(d.sum()), "pv_kw": float(pv.sum()), "allocation_kw": float(alloc[t]),
                    "limit_kw": float(min(limit, 1e6)), "unmanaged_gap_kw": max(unmanaged_gap, -1e6),
                    "cut_fraction": float(depth[t]),
                    "net_kw": net, "battery_kw": cb_kw, "battery_soc": cb.soc if cb else np.nan,
                    "relay_kw": float(served_batt[grid_on].sum()), "outage_backup_kw": float(served_batt[shed].sum()),
                    "appliance_reduction_kw": float(red.sum()), "rebound_kw": float(reb.sum()),
                    "recharge_kw": float(rech.sum()), "band_level_w": dec.band_level_w if dec else np.nan,
                    "homes_banded": int((banded & grid_on).sum()), "homes_shed": int(shed.sum()),
                    "band_curtailed_kw": float(band_cut.sum()), "unserved_kw": float(unserved.sum()),
                    "loading_pct": abs(net) / scenario.rating_kw * 100,
                })
        if cb is not None:
            cb.apply_fade()
        if event is not None and di == len(scenario.dates) - 1:
            event["end"] = "24:00"
            event.pop("sig")
            log.append({"kind": "event", **event})
            event = None

    homes = pd.DataFrame({
        "home_id": [f"HH-{i + 1:04d}" for i in range(n)],
        "segment": fleet.segment, "lt_feeder": fleet.feeder + 1,
        "has_inverter": fleet.has_inverter, "has_pv": fleet.has_pv, "has_actuator": fleet.has_actuator,
        "critical": fleet.critical, "opted_out": fleet.opted_out,
        **acc,
        "relay_kwh": inv.relay_kwh, "outage_backup_kwh": inv.outage_kwh,
        "battery_cycles": inv.cell_out_kwh / inv.capacity_kwh,
        "relay_cycles": inv.relay_kwh / inv.eta / inv.capacity_kwh,
        "appliance_deferred_kwh": flex.deferred_kwh if flex else 0.0,
        "ac_avoided_kwh": flex.ac_avoided_kwh if flex else 0.0,
    })
    ledger = {
        "max_energy_balance_error_kw": max_balance_err,
        "band_excess_max_kw": band_excess_max,
        "shed_blocks_with_unused_steps": shed_with_slack,
        "community_battery_soc_range": [cb_soc_min, cb_soc_max] if cb is not None else None,
        "corrections": sum(1 for e in log if e.get("kind") == "correction"),
        "overload_blocks": int(overload_blocks),
        "peak_loading_pct": float(peak_loading),
        "inverter": {
            "relay_kwh": float(inv.relay_kwh.sum()), "outage_backup_kwh": float(inv.outage_kwh.sum()),
            "recharge_kwh": float(inv.ac_recharge_kwh.sum()),
            "losses_kwh": float((inv.cell_out_kwh - inv.ac_delivered_kwh + inv.ac_recharge_kwh - inv.cell_in_kwh).sum()),
            "min_soc_on_relay": float(inv.min_soc_relay[fleet.has_inverter].min()) if fleet.has_inverter.any() else None,
            "sum_inverter_kw": float(fleet.has_inverter.sum() * inv.inverter_kw),
        },
    }
    if flex is not None:
        ledger["appliance"] = {
            "deferred_kwh": float(flex.deferred_kwh.sum()), "rebound_kwh": float(flex.rebound_kwh.sum()),
            "ac_avoided_kwh": float(flex.ac_avoided_kwh.sum()), "ac_rebound_kwh": float(flex.ac_rebound_kwh.sum()),
            "pending_kwh_at_end": float(flex.pending_kwh()),
        }
    if cb is not None:
        ledger["community_battery"] = {
            "peak_shaving_kwh": arbitrage_kwh,
            "discharged_kwh": cb.discharged_kwh, "charged_kwh": cb.charged_kwh,
            "equivalent_full_cycles": cb.efc, "capacity_kwh_end": cb.capacity_kwh,
            "nameplate_kwh": cb.nameplate_kwh, "soc_end": cb.soc, "fade_loss_kwh": cb.fade_loss_kwh,
            "losses_kwh": (cb.cell_out_kwh - cb.discharged_kwh) + (cb.charged_kwh - cb.cell_in_kwh),
        }
    return RunResult(scenario.name, policy, scenario.seed, pd.DataFrame(rows), homes, log, ledger,
                     scenario.calibration)
