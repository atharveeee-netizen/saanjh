"""Economics must be computed, consistent with results.json, and fair to every household."""
import json
import os

import pytest

from simulation.config import load_config
from simulation.economics_engine import (RESULTS, household_compensation, load_inputs,
                                         ownership_models, recommended_model, scenario_economics)


@pytest.fixture(scope="module")
def res():
    with open(RESULTS, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("case", ["low", "base", "high"])
def test_compensation_covers_wear_and_charging_losses(case):
    e, _ = load_inputs(case)
    c = household_compensation(e, load_config())
    assert c["rate_per_kwh"] >= c["wear_per_kwh"] + c["charging_loss_per_kwh"]


def test_stored_economics_match_engine(res):
    cfg = load_config()
    e, _ = load_inputs()
    for name, stored in res["economics"]["scenarios"].items():
        for mode in ("reliability_only", "with_peak_shaving"):
            fresh = scenario_economics(res, cfg, name, mode, e)
            assert stored[mode]["discom_npv"] == pytest.approx(fresh["discom_npv"])
            assert stored[mode]["net_cost_per_home_per_month"] == pytest.approx(fresh["net_cost_per_home_per_month"])


def test_payback_is_computed_not_hardcoded(res):
    for s in res["economics"]["scenarios"].values():
        m = s["reliability_only"]
        net = m["annual"]["benefits_total"] - m["annual"]["opex_total"]
        if net <= 0:
            assert m["simple_payback_years"] is None
        else:
            assert m["simple_payback_years"] == pytest.approx(m["capex"]["total"] / net)


def test_no_household_loses_money(res):
    for s in res["economics"]["scenarios"].values():
        h = s["reliability_only"]["household"]
        assert h["low_income_upfront"] == 0 and h["low_income_monthly_charge"] == 0
        assert h["inverter_home_annual_net"] >= 0


def test_recommendation_in_docs_matches_numbers(res):
    e, _ = load_inputs()
    for s in res["economics"]["scenarios"].values():
        models = ownership_models(s["reliability_only"], e)
        assert recommended_model(models) == "A_discom" == s["recommended_ownership"]
