"""Versioned contracts for SAANJH result bundles and gateway evidence.

The simulation writes several JSON files. Dashboards, docs and tests read them.
This module is the single contract layer: it validates the files we commit and
exports JSON Schema so a renamed or missing key is caught before it reaches the
write-up.

Usage::

    python -m simulation.contracts                 # validate all committed bundles
    python -m simulation.contracts --write-schemas # regenerate schemas/
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "simulation", "results")
SCHEMA_DIR = os.path.join(BASE_DIR, "schemas")


class ContractModel(BaseModel):
    """Allow extra fields so a result bundle can grow without breaking old readers."""

    model_config = ConfigDict(extra="allow")


# --------------------------------------------------------------------------- radio
class TelemetryV1(ContractModel):
    node_id: int = Field(ge=1, le=65535)
    seq: int = Field(ge=0, le=65535)
    battery_mv: int = Field(ge=0)
    load_w: int = Field(ge=0)
    soc_pct: int = Field(ge=0, le=100)
    flags: int = Field(default=0, ge=0, le=255)
    temp_c: int = Field(default=25, ge=-128, le=127)
    reserved: int = Field(default=0, ge=0, le=65535)


class CommandV1(ContractModel):
    node_id: int = Field(ge=1, le=65535)
    seq: int = Field(ge=0, le=65535)
    command_id: int = Field(ge=0, le=65535)
    duration_s: int = Field(ge=0, le=65535)
    power_limit_w: int = Field(ge=0, le=65535)
    flags: int = Field(default=1, ge=0, le=255)


class AckV1(ContractModel):
    node_id: int = Field(ge=1, le=65535)
    seq: int = Field(ge=0, le=65535)
    command_id: int = Field(ge=0, le=65535)
    status: int = Field(ge=0, le=4)
    soc_pct: int = Field(ge=0, le=100)


class DispatchDecisionV1(ContractModel):
    grid_load_kw: float = Field(ge=0)
    limit_kw: float = Field(ge=0)
    gap_kw: float = Field(ge=0)
    already_kw: float = Field(default=0, ge=0)
    commanded_kw: float = Field(ge=0)
    expected_relief_kw: float = Field(ge=0)
    residual_kw: float = Field(ge=0)
    action: str
    reason: str = ""
    commands: list[dict[str, Any]] = Field(default_factory=list)


# --------------------------------------------------------------------------- analyses
class ReliabilityBundle(ContractModel):
    label: str
    seeds: int = Field(ge=1)
    window: str
    scenarios: dict[str, Any]


class EnergyReconciliation(ContractModel):
    target_kwh: float = Field(ge=0)
    battery_kwh: float = Field(ge=0)
    deferred_kwh: float = Field(ge=0)
    delivered_kwh: float = Field(ge=0)
    unmet_kwh: float = Field(ge=0)
    delivered_pct_of_claim: float = Field(ge=0)
    battery_share_pct: float = Field(ge=0)
    deferred_share_pct: float = Field(ge=0)
    unmet_share_pct: float = Field(ge=0)
    identity: str
    adds_up: bool

    @model_validator(mode="after")
    def _identity_holds(self):
        # Rounding to 3 decimal places can produce up to a 0.0015 discrepancy
        if abs((self.battery_kwh + self.deferred_kwh) - self.delivered_kwh) > 2e-3:
            raise ValueError("battery_kwh + deferred_kwh must equal delivered_kwh")
        if abs((self.delivered_kwh + self.unmet_kwh) - self.target_kwh) > 2e-3:
            raise ValueError("delivered_kwh + unmet_kwh must equal target_kwh")
        if not self.adds_up:
            raise ValueError("energy balance is marked as not adding up")
        return self


class EnergyBalanceBundle(ContractModel):
    label: str
    scenario: str
    seed: int = Field(ge=0)
    legacy_claim: dict[str, Any]
    simulated_event: dict[str, Any]
    best_45_min: dict[str, Any]
    reconciliation: EnergyReconciliation
    fleet_requirement: dict[str, Any]
    notes: list[str] = Field(default_factory=list)


class LowIncomeBundle(ContractModel):
    label: str
    scenario: str
    seeds: int = Field(ge=1)
    adoption_levels: list[float]
    groups: dict[str, Any]
    inputs: dict[str, Any]
    notes: list[str] = Field(default_factory=list)
    best_case: Optional[dict[str, Any]] = None


class OverloadBundle(ContractModel):
    label: str
    scenario: str
    seeds: int = Field(ge=1)
    stress_transformer_kva: float = Field(gt=0)
    stress_transformer_rating_kw: float = Field(gt=0)
    dispatch_target_pct: float = Field(gt=0, le=100)
    legacy_audit: dict[str, Any]
    baseline: dict[str, Any]
    adoption_sweep: list[dict[str, Any]]
    storage_sweep_at_60pct_adoption: list[dict[str, Any]]
    minimum: dict[str, Any]
    service_ladder: list[dict[str, Any]]
    limits: list[str] = Field(default_factory=list)


class RobustnessBundle(ContractModel):
    label: str
    scenario: str
    seeds: int = Field(ge=1)
    baseline: dict[str, Any]
    cases: list[dict[str, Any]]
    limits: list[str] = Field(default_factory=list)


class CalibrationBundle(ContractModel):
    label: str
    site: dict[str, Any]
    weather_label: str
    annual: dict[str, Any]
    calibration_targets: dict[str, Any]
    evening_profile_clear_summer: dict[str, Any]
    cases: dict[str, Any]
    forecast: dict[str, Any]
    honest_read: list[str] = Field(default_factory=list)


class AnnualSection(ContractModel):
    label: str
    seeds: int = Field(ge=1)
    days: int = Field(ge=1)
    site: dict[str, Any]
    scenarios: dict[str, Any]


class ResultsBundle(ContractModel):
    """The canonical annual bundle. Sections are validated by their own modules."""

    evening_peak_case: dict[str, Any]
    load_calibration: dict[str, Any]
    annual: AnnualSection
    sensitivity: dict[str, Any]
    figures: dict[str, Any]
    forecast: dict[str, Any]
    economics: dict[str, Any]


# --------------------------------------------------------------------------- gateway
class GatewaySummaryV1(ContractModel):
    mode: Optional[Literal["replay", "live"]] = None
    label: Optional[str] = None
    telemetry_sent: Optional[int] = Field(default=None, ge=0)
    telemetry_received: Optional[int] = Field(default=None, ge=0)
    telemetry_lost: Optional[int] = Field(default=None, ge=0)
    packet_success_pct: Optional[float] = Field(default=None, ge=0, le=100)
    commands_sent: Optional[int] = Field(default=None, ge=0)
    commands_delivered: Optional[int] = Field(default=None, ge=0)
    command_losses: Optional[int] = Field(default=None, ge=0)
    command_success_pct: Optional[float] = Field(default=None, ge=0, le=100)
    commands_accepted: Optional[int] = Field(default=None, ge=0)
    commands_refused: Optional[int] = Field(default=None, ge=0)
    commands_completed: Optional[int] = Field(default=None, ge=0)
    acks_received: Optional[int] = Field(default=None, ge=0)
    command_ack_pct: Optional[float] = Field(default=None, ge=0, le=100)
    mean_command_latency_ms: Optional[float] = Field(default=None, ge=0)
    p95_command_latency_ms: Optional[float] = Field(default=None, ge=0)
    soc_min_pct: Optional[float] = Field(default=None, ge=0, le=100)
    reserve_breaches: Optional[int] = Field(default=None, ge=0)
    battery_energy_delivered_kwh: Optional[float] = Field(default=None, ge=0)
    dispatch_target_kw: Optional[float] = Field(default=None, ge=0)
    transformer_rating_kw: Optional[float] = Field(default=None, ge=0)
    grid_peak_before_kw: Optional[float] = Field(default=None, ge=0)
    grid_peak_after_kw: Optional[float] = Field(default=None, ge=0)
    overload_minutes_before: Optional[int] = Field(default=None, ge=0)
    overload_minutes_after: Optional[int] = Field(default=None, ge=0)
    dispatch_events: Optional[int] = Field(default=None, ge=0)
    commanded_kwh: Optional[float] = Field(default=None, ge=0)
    accepted_kwh: Optional[float] = Field(default=None, ge=0)
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)
    notes: Optional[str] = None
    note: Optional[str] = None


CONTRACTS: dict[str, type[ContractModel]] = {
    "results.json": ResultsBundle,
    "reliability.json": ReliabilityBundle,
    "energy_balance.json": EnergyBalanceBundle,
    "low_income.json": LowIncomeBundle,
    "overload.json": OverloadBundle,
    "robustness.json": RobustnessBundle,
    "calibration.json": CalibrationBundle,
}

GATEWAY_CONTRACTS: dict[str, type[ContractModel]] = {
    "replay_summary.json": GatewaySummaryV1,
    "live_summary.json": GatewaySummaryV1,
}

SCHEMA_MODELS: dict[str, type[ContractModel]] = {
    "telemetry_v1": TelemetryV1,
    "command_v1": CommandV1,
    "ack_v1": AckV1,
    "dispatch_decision_v1": DispatchDecisionV1,
    "results_bundle_v1": ResultsBundle,
    "reliability_v1": ReliabilityBundle,
    "energy_balance_v1": EnergyBalanceBundle,
    "low_income_v1": LowIncomeBundle,
    "overload_v1": OverloadBundle,
    "robustness_v1": RobustnessBundle,
    "calibration_v1": CalibrationBundle,
    "gateway_summary_v1": GatewaySummaryV1,
}


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_payload(model: type[ContractModel], payload: Any):
    return model.model_validate(payload)


def validate_file(path: str, model: type[ContractModel]):
    return validate_payload(model, load_json(path))


def validate_all(results_dir: str = RESULTS_DIR, gateway_dir: Optional[str] = None) -> list[str]:
    errors: list[str] = []
    for name, model in CONTRACTS.items():
        path = os.path.join(results_dir, name)
        if not os.path.exists(path):
            errors.append(f"{name}: missing")
            continue
        try:
            validate_file(path, model)
        except (ValidationError, ValueError) as exc:
            errors.append(f"{name}: {exc}")
    gateway_dir = gateway_dir or os.path.join(BASE_DIR, "gateway", "data")
    for name, model in GATEWAY_CONTRACTS.items():
        path = os.path.join(gateway_dir, name)
        if os.path.exists(path):
            try:
                validate_file(path, model)
            except (ValidationError, ValueError) as exc:
                errors.append(f"gateway/{name}: {exc}")
    return errors


def write_schemas(schema_dir: str = SCHEMA_DIR) -> list[str]:
    os.makedirs(schema_dir, exist_ok=True)
    written = []
    for name, model in SCHEMA_MODELS.items():
        path = os.path.join(schema_dir, f"{name}.schema.json")
        schema = model.model_json_schema(mode="validation")
        schema.setdefault("$schema", "https://json-schema.org/draft/2020-12/schema")
        schema.setdefault("title", name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, sort_keys=True)
            f.write("\n")
        written.append(path)
    return written


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Validate SAANJH result contracts")
    ap.add_argument("--write-schemas", action="store_true", help="regenerate schemas/")
    ap.add_argument("--results-dir", default=RESULTS_DIR)
    ap.add_argument("--gateway-dir", default=os.path.join(BASE_DIR, "gateway", "data"))
    args = ap.parse_args(argv)

    if args.write_schemas:
        for path in write_schemas():
            print(f"wrote {os.path.relpath(path, BASE_DIR)}")

    errors = validate_all(args.results_dir, args.gateway_dir)
    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1
    print(f"validated {len(CONTRACTS)} result bundles and gateway summaries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
