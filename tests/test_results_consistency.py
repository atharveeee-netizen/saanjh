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
