"""Committed result bundles must satisfy the versioned contracts and JSON Schema."""
import copy
import json
import os

import jsonschema
import pytest
from pydantic import ValidationError

from simulation import contracts

RESULTS = os.path.join(contracts.BASE_DIR, "simulation", "results")


def _load(name):
    with open(os.path.join(RESULTS, name), "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("name", sorted(contracts.CONTRACTS))
def test_result_bundle_validates(name):
    model = contracts.CONTRACTS[name]
    contracts.validate_file(os.path.join(RESULTS, name), model)


@pytest.mark.parametrize("name", sorted(contracts.CONTRACTS))
def test_result_bundle_matches_exported_schema(name):
    schema_name = {
        "results.json": "results_bundle_v1",
        "reliability.json": "reliability_v1",
        "energy_balance.json": "energy_balance_v1",
        "low_income.json": "low_income_v1",
        "overload.json": "overload_v1",
        "robustness.json": "robustness_v1",
        "calibration.json": "calibration_v1",
    }[name]
    schema_path = os.path.join(contracts.SCHEMA_DIR, f"{schema_name}.schema.json")
    assert os.path.exists(schema_path), f"missing schema {schema_path}"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.validate(_load(name), schema)


def test_energy_balance_reconciles():
    payload = _load("energy_balance.json")
    rec = payload["reconciliation"]
    assert rec["adds_up"] is True
    assert rec["battery_kwh"] + rec["deferred_kwh"] == pytest.approx(rec["delivered_kwh"], abs=2e-3)
    assert rec["delivered_kwh"] + rec["unmet_kwh"] == pytest.approx(rec["target_kwh"], abs=2e-3)


def test_missing_key_fails_loudly():
    payload = copy.deepcopy(_load("reliability.json"))
    del payload["label"]
    with pytest.raises(ValidationError):
        contracts.ReliabilityBundle.model_validate(payload)


def test_gateway_summary_contract():
    path = os.path.join(contracts.BASE_DIR, "gateway", "data", "replay_summary.json")
    contracts.validate_file(path, contracts.GatewaySummaryV1)
    with open(os.path.join(contracts.SCHEMA_DIR, "gateway_summary_v1.schema.json"), encoding="utf-8") as f:
        jsonschema.validate(json.load(open(path, encoding="utf-8")), json.load(f))
