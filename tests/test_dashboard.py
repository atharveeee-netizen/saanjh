"""Dashboard data-layer and headless render tests."""
import os

import pandas as pd

from dashboard.data import (
    ROOT,
    annual_rows,
    calibration_checks,
    load_all,
    low_income_points,
    replay_kpis,
    robustness_cases,
    scorecard_rows,
)


def test_load_all_reads_committed_bundles():
    data = load_all()
    assert data.results["annual"]["scenarios"], "results.json missing annual scenarios"
    assert data.replay_summary, "gateway replay summary missing"
    assert data.mode == "replay"
    assert {"node_id", "soc_pct", "relay"}.issubset(data.telemetry.columns)
    assert {"command_id", "delivered", "status"}.issubset(data.commands.columns)


def test_annual_rows_have_both_policies():
    rows = annual_rows(load_all(), "peri_urban_low_income")
    assert not rows.empty
    assert rows["baseline"].notna().all()
    assert rows["saanjh"].notna().all()
    availability = rows[rows["metric"] == "Essential supply availability"].iloc[0]
    assert availability["baseline"] < availability["saanjh"]
    # The bundle stores a fraction; the dashboard must show a percentage.
    assert 90.0 <= availability["saanjh"] <= 100.0


def test_scorecard_and_robustness_are_populated():
    data = load_all()
    scorecard = scorecard_rows(data, "mixed_urban")
    assert not scorecard.empty
    assert {"metric", "baseline", "saanjh"}.issubset(scorecard.columns)
    cases = robustness_cases(data)
    assert not cases.empty
    delivery = cases["relay_command_delivery_pct"].dropna()
    assert not delivery.empty and delivery.between(0, 100).all()


def test_low_income_curves_are_monotonic_in_adoption():
    data = load_all()
    for group in ("inverter_batteries", "shared_battery", "combined"):
        frame = low_income_points(data, group)
        assert len(frame) >= 3
        assert frame["adoption"].is_monotonic_increasing
        assert frame["essential_supply_availability_pct"].is_monotonic_increasing


def test_calibration_checks_pass_and_forecast_has_models():
    data = load_all()
    checks = calibration_checks(data)
    assert not checks.empty
    assert checks["ok"].all()
    models = pd.DataFrame(data.calibration["forecast"]["models"])
    assert {"scenario", "model", "mase"}.issubset(models.columns)


def test_replay_kpis_use_recorder_names():
    kpi = replay_kpis(load_all().replay_summary)
    assert kpi["telemetry_sent"] > kpi["telemetry_received"] > 0
    assert kpi["packet_success_pct"] > 90
    assert kpi["commands_sent"] >= kpi["commands_delivered"] > 0
    assert kpi["soc_min_pct"] >= 70.0
    assert kpi["reserve_breaches"] == 0
    assert kpi["nodes"] == 3


def test_dashboard_renders_headlessly():
    from streamlit.testing.v1 import AppTest

    app = os.path.join(ROOT, "dashboard", "app.py")
    at = AppTest.from_file(app, default_timeout=120).run()
    assert not at.exception, at.exception
    assert len(at.title) == 1
    assert len(at.tabs) >= 7
