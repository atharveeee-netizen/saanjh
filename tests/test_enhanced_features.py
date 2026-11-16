"""Tests for cryptographic authentication, conformal calibration, and 3-phase unbalance."""
import numpy as np
import pytest

from ai_forecasting.models import ConformalQuantileCalibrator
from gateway.protocol import AntiReplayFilter, compute_hmac, verify_hmac
from simulation.phase_unbalance import ThreePhaseUnbalanceAnalyzer


# --------------------------------------------------------------------------- security
def test_hmac_authentication_and_verification():
    secret_key = b"SAANJH_SCHNEIDER_SECRET_KEY_2026"
    data = b"NODE_101_DISCHARGE_CMD_2700S_350W"

    token = compute_hmac(data, secret_key)
    assert len(token) == 4
    assert verify_hmac(data, secret_key, token) is True

    # Tampered data must fail
    tampered_data = b"NODE_101_DISCHARGE_CMD_9999S_350W"
    assert verify_hmac(tampered_data, secret_key, token) is False

    # Tampered key must fail
    wrong_key = b"WRONG_KEY"
    assert verify_hmac(data, wrong_key, token) is False


def test_anti_replay_filter():
    rf = AntiReplayFilter(window_size=32)

    # First packet passes
    assert rf.check_and_update(1) is True

    # Same sequence (replay attack) must be rejected
    assert rf.check_and_update(1) is False

    # Monotonic progression passes
    assert rf.check_and_update(2) is True
    assert rf.check_and_update(3) is True

    # Late arrival within window passes once, then fails
    assert rf.check_and_update(5) is True
    assert rf.check_and_update(4) is True  # late arrival within window
    assert rf.check_and_update(4) is False # replayed late arrival


# --------------------------------------------------------------------------- conformal
def test_conformal_quantile_calibrator():
    calibrator = ConformalQuantileCalibrator(target_coverage=0.80)

    # Synthetic historical test: model was under-covering (q_low=10, q_high=20, true y between 5 and 25)
    np.random.seed(42)
    y_true = np.random.uniform(5.0, 25.0, size=100)
    q_hist = np.zeros((3, 100))
    q_hist[0] = 10.0  # P10
    q_hist[1] = 15.0  # P50
    q_hist[2] = 20.0  # P90

    # Before calibration, coverage is only (20 - 10) / (25 - 5) = 50%
    base_coverage = np.mean((y_true >= q_hist[0]) & (y_true <= q_hist[2]))
    assert base_coverage < 0.60

    # Compute adjustment score
    q_score = calibrator.compute_adjustment(y_true, q_hist)
    assert q_score > 0.0  # Must be positive to widen bounds

    # Adjust interval
    test_q = np.array([10.0, 15.0, 20.0])
    adj_q = calibrator.adjust(test_q, q_score)
    assert adj_q[0] < test_q[0]  # Lower bound decreased
    assert adj_q[2] > test_q[2]  # Upper bound increased
    assert adj_q[0] <= adj_q[1] <= adj_q[2]  # Monotonic ordering preserved


# --------------------------------------------------------------------------- 3-phase unbalance
def test_three_phase_unbalance_analysis():
    analyzer = ThreePhaseUnbalanceAnalyzer(dt_kva=100.0, pf=0.95)
    assert analyzer.phase_kw_rated == pytest.approx(31.6667, rel=1e-3)

    # 250 homes distributed across R, Y, B with severe Phase R overload:
    # Phase R: 95 homes, 38.0 kW (120% loading!)
    # Phase Y: 80 homes, 26.0 kW (82% loading)
    # Phase B: 75 homes, 25.0 kW (79% loading)
    phase_loads = {
        "R": (95, 38.0),
        "Y": (80, 26.0),
        "B": (75, 25.0),
    }
    agg_kw = 38.0 + 26.0 + 25.0  # 89.0 kW <= 95.0 kW overall rating!

    # 1. Baseline: trips the entire feeder because Phase R is overloaded
    res_base = analyzer.run_case(phase_loads, policy="baseline")
    assert res_base.tripped is True
    assert res_base.blackout_homes == 250
    assert res_base.unserved_kwh_1h == pytest.approx(89.0)

    # 2. SAANJH: phase-selective capping (caps only Phase R to 750W -> 95 * 0.75 = 71.25 kW, min(38, 71.25))
    # Let's test with a tighter cap on Phase R (e.g. 300W cap -> 95 * 0.3 = 28.5 kW)
    res_saanjh = analyzer.run_case(phase_loads, policy="saanjh", band_cap_w=300.0)
    assert res_saanjh.tripped is False
    assert res_saanjh.blackout_homes == 0  # 0 homes blacked out!
    assert res_saanjh.phase_states["R"].load_kw <= analyzer.phase_kw_rated  # Phase R relieved!
    assert res_saanjh.phase_states["Y"].load_kw == 26.0  # Phase Y untouched!
    assert res_saanjh.phase_states["B"].load_kw == 25.0  # Phase B untouched!
    assert res_saanjh.unserved_kwh_1h < 15.0  # Orders of magnitude less energy lost than 89 kWh!
