"""Numbers shown in docs must come from results.json, and results.json from the code."""
import json
import os

import pytest

from scripts import render_results
from simulation.feeder_sim import RESULTS_DIR, run_simulation, summarise

RESULTS = os.path.join(RESULTS_DIR, "results.json")


@pytest.fixture(scope="module")
def results():
    with open(RESULTS, "r", encoding="utf-8") as f:
        return json.load(f)


def test_results_file_matches_simulation(results):
    stored = results["evening_peak_case"]
    base, _, _, cfg = run_simulation("baseline", stored["scenario"], stored["seed"])
    saanjh, homes, ledger, _ = run_simulation("saanjh", stored["scenario"], stored["seed"], cfg=cfg)
    fresh = summarise(base, saanjh, homes, ledger, cfg, stored["scenario"])
    for block in ("baseline", "saanjh", "flexibility"):
        for key, value in fresh[block].items():
            if isinstance(value, float):
                assert stored[block][key] == pytest.approx(value, rel=1e-6, abs=1e-9), (block, key)
            else:
                assert stored[block][key] == value, (block, key)


def test_docs_are_rendered_from_results():
    assert render_results.main(["--check"]) == 0, "run: python scripts/render_results.py"


def test_annual_summary_matches_montecarlo_rows(results):
    import pandas as pd
    mc = pd.read_csv(os.path.join(RESULTS_DIR, "montecarlo.csv"))
    for name, s in results["annual"]["scenarios"].items():
        for policy in ("baseline", "saanjh"):
            rows = mc[(mc.scenario == name) & (mc.policy == policy)]
            assert len(rows) == results["annual"]["seeds"]
            for key in ("essential_supply_availability", "outage_hours_per_home", "energy_not_served_kwh"):
                assert s[policy][key]["mean"] == pytest.approx(rows[key].mean(), rel=1e-9)


def test_seed0_run_reproduces_saved_homes_table():
    import pandas as pd
    from simulation.engine import Scenario, run
    name = "mixed_urban"
    saved = pd.read_csv(os.path.join(RESULTS_DIR, "annual", f"{name}_saanjh_homes.csv"))
    fresh = run(Scenario(name, 0), "saanjh", record_days=[]).homes
    for col in ("shed_blocks", "ess_ok_blocks", "deficit_blocks", "unserved_kwh"):
        assert fresh[col].to_numpy() == pytest.approx(saved[col].to_numpy(), rel=1e-9, abs=1e-9), col
