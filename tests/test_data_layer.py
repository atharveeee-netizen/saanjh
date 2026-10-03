"""Tests for the real-data layer: weather, load calibration and the ESMI loader."""
import os

import pytest

from data.load_esmi import compute_stats
from scripts.calibrate_loads import calibrate
from simulation.config import load_config, repo_path
from simulation.weather import Weather


def test_weather_is_real_and_plausible():
    w = Weather("lucknow", 2023)
    assert w.is_real, "NASA POWER data should be present in data/processed/"
    assert len(w.dates) == 365
    annual_yield = w.q["pv_kw_per_kwp"].sum() / 4
    assert 1000 < annual_yield < 1600   # kWh per kWp, north India, horizontal
    assert set(w.days["day_type"]) <= {"clear", "cloudy", "monsoon", "heatwave"}


def test_load_calibration_hits_emarc_targets():
    summary, _ = calibrate(load_config(), n_homes=300, n_days=2)
    failed = {k: c for k, c in summary["checks"].items() if not c["ok"]}
    assert not failed, failed


def test_esmi_loader_on_format_fixture():
    stats = compute_stats([repo_path("data", "samples", "esmi_format_fixture.csv")])
    m = stats["mean"]
    assert m["outage_hours_per_day"] == pytest.approx(1.0)
    assert m["evening_outage_minutes_per_day"] == pytest.approx(40.0)
    assert m["outages_per_day"] == pytest.approx(2.0)
    assert m["low_voltage_hours_per_day"] == pytest.approx(0.5)


def test_inverter_ownership_is_realistic():
    cfg = load_config()
    own = {s: cfg["segments"][s]["ownership"]["inverter"] for s in ("low_income", "middle", "affluent")}
    assert own["low_income"] <= 0.05 and own["middle"] <= 0.25 and own["affluent"] <= 0.6
    for name in ("peri_urban_low_income", "mixed_urban"):
        mix = cfg["scenarios"][name]["segment_mix"]
        share = sum(mix[s] * own[s] for s in mix)
        assert share < 0.3, f"{name}: inverter share {share:.0%} is unrealistically high"
