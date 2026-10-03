"""Physical-sanity tests for the evening peak case (docs/PROJECT_BRIEF.md, ground rule 3)."""
import math

import numpy as np
import pytest

from simulation.config import load_config
from simulation.feeder_sim import run_simulation
from simulation.mechanisms.inverter_relay import InverterBatteryFlex


@pytest.fixture(scope="module")
def saanjh_run():
    df, homes, ledger, cfg = run_simulation("saanjh", seed=7)
    return df, homes, ledger, cfg


def test_delivered_never_exceeds_inverter_limits(saanjh_run):
    df, homes, _, _ = saanjh_run
    inverter_sum = sum(h.inverter.inverter_kw for h in homes if h.inverter)
    assert (df["battery_delivered_kw"] <= inverter_sum + 1e-9).all()

    # Unit level: a relay can never serve more than the inverter rating or the home's
    # own backed-up load (an inverter cannot export).
    cfg = load_config()["inverter_battery"]
    inv = InverterBatteryFlex(cfg)
    inv.open_relay()
    served, _ = inv.step(0, backed_up_kw=5.0, step_h=0.25)
    assert served <= cfg["inverter_kw"] + 1e-12
    inv = InverterBatteryFlex(cfg)
    inv.open_relay()
    served, _ = inv.step(0, backed_up_kw=0.1, step_h=0.25)
    assert served == pytest.approx(0.1)


def test_battery_energy_conservation(saanjh_run):
    _, homes, _, cfg = saanjh_run
    eta = math.sqrt(cfg["inverter_battery"]["round_trip_efficiency"])
    cap = cfg["inverter_battery"]["capacity_kwh"]
    initial = cfg["inverter_battery"]["initial_soc"]
    used = [h.inverter for h in homes if h.inverter and h.inverter.cell_out_kwh > 0]
    assert used, "scenario should dispatch at least one battery"
    for inv in used:
        assert inv.ac_delivered_kwh == pytest.approx(inv.cell_out_kwh * eta, rel=1e-9)
        assert inv.cell_in_kwh == pytest.approx(inv.ac_recharge_kwh * eta, rel=1e-9)
        soc_drop_kwh = (initial - inv.soc) * cap
        assert inv.cell_out_kwh - inv.cell_in_kwh == pytest.approx(soc_drop_kwh, abs=1e-9)


def test_soc_never_below_reserve(saanjh_run):
    _, homes, _, cfg = saanjh_run
    reserve = cfg["inverter_battery"]["reserve_soc"]
    for h in homes:
        if h.inverter:
            assert h.inverter.min_soc_seen >= reserve - 1e-9


def test_recharge_appears_in_feeder_load(saanjh_run):
    df, homes, _, cfg = saanjh_run
    step_h = cfg["simulation"]["step_min"] / 60
    rebuilt = (df["uncontrolled_net_kw"] - df["battery_delivered_kw"]
               - df["appliance_reduction_kw"] + df["rebound_kw"] + df["recharge_kw"])
    np.testing.assert_allclose(df["net_load_kw"], rebuilt, atol=1e-9)
    assert df["recharge_kw"].sum() > 0
    ledger = sum(h.inverter.ac_recharge_kwh for h in homes if h.inverter)
    assert df["recharge_kw"].sum() * step_h == pytest.approx(ledger)


def test_no_flex_from_homes_without_actuators():
    overrides = {"segments": {"legacy": {"ownership": {"actuator": 0.0}}}}
    df, homes, _, _ = run_simulation("saanjh", seed=7, overrides=overrides)
    assert all(h.appliance_flex is None for h in homes)
    assert (df["appliance_reduction_kw"] == 0).all()
    assert (df["rebound_kw"] == 0).all()


def test_deferred_energy_rebounds(saanjh_run):
    _, homes, _, _ = saanjh_run
    flex = [h.appliance_flex for h in homes if h.appliance_flex]
    assert sum(a.deferred_kwh for a in flex) > 0, "scenario should defer some appliance energy"
    for a in flex:
        # Over the run, deferrable appliances use exactly the energy they wanted.
        assert a.served_kwh == pytest.approx(a.scheduled_kwh, abs=1e-9)
        assert sum(a.queue_kwh.values()) == pytest.approx(0.0, abs=1e-9)


def test_baseline_and_saanjh_see_identical_demand():
    base, *_ = run_simulation("baseline", seed=11)
    saanjh, *_ = run_simulation("saanjh", seed=11)
    np.testing.assert_allclose(base["demand_kw"], saanjh["demand_kw"])
    np.testing.assert_allclose(base["pv_kw"], saanjh["pv_kw"])


def test_battery_delivery_tracks_fleet_size():
    """Causal check (replaces the old config-file mutation script)."""
    few = {"segments": {"legacy": {"ownership": {"inverter": 0.05}}}}
    many = {"segments": {"legacy": {"ownership": {"inverter": 0.40}}}}
    df_few, *_ = run_simulation("saanjh", seed=3, overrides=few)
    df_many, *_ = run_simulation("saanjh", seed=3, overrides=many)
    assert df_many["battery_delivered_kw"].sum() > df_few["battery_delivered_kw"].sum()


def test_opted_out_homes_never_dispatched(saanjh_run):
    _, homes, ledger, _ = saanjh_run
    assert ledger["opt_out_dispatches"] == 0
    for h in homes:
        if h.opted_out:
            if h.inverter:
                assert h.inverter.dispatch_steps == 0
            if h.appliance_flex:
                assert h.appliance_flex.curtailed_steps == 0
