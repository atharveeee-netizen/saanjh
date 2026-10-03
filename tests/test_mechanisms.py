"""Tests for SAANJH's mechanisms and dispatcher on a full-year run (docs/PROJECT_BRIEF.md)."""
import numpy as np
import pytest

from simulation.config import load_config
from simulation.dispatcher import DeficitDispatcher
from simulation.engine import Scenario, run
from simulation.fleet import HomeFleet
from simulation.mechanisms.community_battery import CommunityBattery
from simulation.mechanisms.essential_band import EssentialBand
from simulation.mechanisms.inverter_relay import InverterFleet


@pytest.fixture(scope="module")
def runs():
    sc = Scenario("peri_urban_low_income", seed=0)
    return sc, run(sc, "baseline", record_days=[]), run(sc, "saanjh", record_days=[])


def test_band_never_exceeded_except_inrush():
    cfg = load_config()["essential_band"]
    # A fridge compressor start: 1 s at six times its 120 W running power, on top of 300 W.
    trace = np.full(120, 420.0)
    trace[10] = 300 + 6 * 120
    assert not EssentialBand.meter_trips(trace, 1.0, cfg["band_w"], cfg["grace_s"])
    # A sustained overload (a 2 kW geyser switched on) trips the meter after the grace.
    trace[30:100] = 2300
    assert EssentialBand.meter_trips(trace, 1.0, cfg["band_w"], cfg["grace_s"])


def test_band_respected_in_simulation(runs):
    _, _, s = runs
    assert s.ledger["band_excess_max_kw"] <= 1e-9


def test_battery_soc_bounds(runs):
    sc, _, s = runs
    cb = sc.cfg["community_battery"]
    lo, hi = s.ledger["community_battery_soc_range"]
    assert lo >= cb["soc_min"] - 1e-9 and hi <= cb["soc_max"] + 1e-9
    assert s.ledger["inverter"]["min_soc_on_relay"] >= sc.cfg["inverter_battery"]["reserve_soc"] - 1e-9


def test_no_shedding_while_earlier_steps_have_room(runs):
    _, _, s = runs
    assert s.ledger["shed_blocks_with_unused_steps"] == 0
    assert s.ledger["corrections"] == 0


def test_energy_balance_per_block(runs):
    _, b, s = runs
    assert b.ledger["max_energy_balance_error_kw"] < 1e-9
    assert s.ledger["max_energy_balance_error_kw"] < 1e-9


def test_identical_inputs_for_both_policies(runs):
    _, b, s = runs
    np.testing.assert_allclose(b.homes["demand_kwh"], s.homes["demand_kwh"])
    np.testing.assert_array_equal(b.homes["deficit_blocks"], s.homes["deficit_blocks"])


def test_saanjh_improves_essential_supply(runs):
    _, b, s = runs
    avail = lambda r: r.homes["ess_ok_blocks"].sum() / r.homes["deficit_blocks"].sum()
    assert avail(s) > avail(b)
    assert s.homes["shed_blocks"].sum() < b.homes["shed_blocks"].sum()


def test_fairness_is_reported(runs):
    from simulation.metrics import fairness
    _, _, s = runs
    f = fairness(s.homes["shed_blocks"].to_numpy())
    assert 0.0 <= f["gini"] <= 1.0


def _toy_dispatcher(gap_kw, band_capacity_kw):
    """A 10-home DT with no flexibility and no battery, so only the band can help."""
    cfg = load_config({"segments": {"middle": {"ownership": {"inverter": 0, "actuator": 0, "critical_load": 0}}}})
    fleet = HomeFleet(cfg, {"num_homes": 10, "segment_mix": {"middle": 1.0}}, np.random.default_rng(0))
    inv = InverterFleet(cfg["inverter_battery"], fleet.has_inverter)
    band = EssentialBand(cfg["essential_band"], fleet.critical)
    disp = DeficitDispatcher(cfg, fleet, inv, None, band, None, 0.25)

    class L:  # one-step loads: every home draws 0.5 kW + its share of band capacity
        pass
    loads = L()
    loads.total = np.full((10, 1), band.band_w / 1000 + band_capacity_kw / 10)
    loads.backed_up = np.zeros((10, 1))
    limit = loads.total.sum() - gap_kw
    return disp.plan(loads, 0, 19.0, limit, np.zeros(10), 30.0)


def test_band_closes_coverable_gap_without_shedding():
    dec = _toy_dispatcher(gap_kw=2.0, band_capacity_kw=3.0)
    assert dec.band_level_w is not None and not dec.shed.any()


def test_shedding_only_when_band_is_not_enough():
    dec = _toy_dispatcher(gap_kw=4.0, band_capacity_kw=3.0)
    assert dec.shed.any()


def test_community_battery_accounting():
    cfg = load_config()["community_battery"]
    cb = CommunityBattery(cfg)
    e0 = cb.stored_kwh()
    out = sum(cb.discharge(30, 0.25, 30) for _ in range(8)) * 0.25
    assert cb.soc >= cfg["soc_min"] - 1e-12
    assert out == pytest.approx(cb.cell_out_kwh * cb.eta)
    assert e0 - cb.stored_kwh() == pytest.approx(cb.cell_out_kwh)
    # Hot day: power is derated.
    assert cb.power_limit_kw(45) < cb.power_limit_kw(30)
