"""Data access for the SAANJH operator console.

The dashboard reads two sources and nothing else:

* ``simulation/results/`` - committed result bundles from the annual,
  reliability, energy-balance, low-income, overload, robustness and
  calibration analyses;
* ``gateway/data/`` - hardware-in-the-loop evidence written by
  ``python -m gateway.service`` (CSV, SQLite and the run summary).

Every loader degrades gracefully, so a fresh clone renders before any
simulation or hardware run has happened. Nothing here invents grid data.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(ROOT, "simulation", "results")
GATEWAY_DIR = os.path.join(ROOT, "gateway", "data")
ANNUAL_DIR = os.path.join(RESULTS_DIR, "annual")

SCENARIO_LABELS = {
    "peri_urban_low_income": "Peri-urban low-income DT",
    "mixed_urban": "Mixed urban DT",
}

GROUP_LABELS = {
    "inverter_batteries": "Household inverter batteries",
    "shared_battery": "Shared community battery",
    "combined": "Combined fleet",
}

BUNDLE_FILES = {
    "results": "results.json",
    "reliability": "reliability.json",
    "energy_balance": "energy_balance.json",
    "low_income": "low_income.json",
    "overload": "overload.json",
    "robustness": "robustness.json",
    "calibration": "calibration.json",
}

CSV_FILES = {
    "telemetry": ("gateway", "telemetry.csv"),
    "commands": ("gateway", "commands.csv"),
    "acks": ("gateway", "acks.csv"),
    "dispatch": ("gateway", "dispatch.csv"),
    "grid": ("gateway", "grid.csv"),
    "montecarlo": ("results", "montecarlo.csv"),
    "load_profiles": ("results", "load_profiles.csv"),
    "forecast_decision": ("results", "forecast_decision_value.csv"),
}


def _path(kind: str, name: str) -> str:
    if kind == "gateway":
        return os.path.join(GATEWAY_DIR, name)
    return os.path.join(RESULTS_DIR, name)


def read_json(path: str) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def read_csv(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except (OSError, ValueError):
        return pd.DataFrame()


@dataclass
class DashboardData:
    results: dict[str, Any] = field(default_factory=dict)
    reliability: dict[str, Any] = field(default_factory=dict)
    energy_balance: dict[str, Any] = field(default_factory=dict)
    low_income: dict[str, Any] = field(default_factory=dict)
    overload: dict[str, Any] = field(default_factory=dict)
    robustness: dict[str, Any] = field(default_factory=dict)
    calibration: dict[str, Any] = field(default_factory=dict)
    replay_summary: dict[str, Any] = field(default_factory=dict)
    live_summary: dict[str, Any] = field(default_factory=dict)
    telemetry: pd.DataFrame = field(default_factory=pd.DataFrame)
    commands: pd.DataFrame = field(default_factory=pd.DataFrame)
    acks: pd.DataFrame = field(default_factory=pd.DataFrame)
    dispatch: pd.DataFrame = field(default_factory=pd.DataFrame)
    grid: pd.DataFrame = field(default_factory=pd.DataFrame)
    montecarlo: pd.DataFrame = field(default_factory=pd.DataFrame)
    load_profiles: pd.DataFrame = field(default_factory=pd.DataFrame)
    forecast_decision: pd.DataFrame = field(default_factory=pd.DataFrame)
    missing: list[str] = field(default_factory=list)

    @property
    def mode(self) -> str:
        if self.live_summary:
            return "live"
        if self.replay_summary:
            return "replay"
        return "no gateway run"

    def scenario(self, key: str) -> dict[str, Any]:
        return self.results.get("annual", {}).get("scenarios", {}).get(key, {})


def load_all(results_dir: str = RESULTS_DIR,
             gateway_dir: str = GATEWAY_DIR) -> DashboardData:
    """Load every bundle and log. Missing files are recorded, not raised."""
    global RESULTS_DIR, GATEWAY_DIR, ANNUAL_DIR
    RESULTS_DIR, GATEWAY_DIR = results_dir, gateway_dir
    ANNUAL_DIR = os.path.join(results_dir, "annual")

    data = DashboardData()
    missing: list[str] = []

    for attr, filename in BUNDLE_FILES.items():
        path = os.path.join(results_dir, filename)
        if not os.path.exists(path):
            missing.append(f"simulation/results/{filename}")
        setattr(data, attr, read_json(path))

    for attr, (kind, filename) in CSV_FILES.items():
        path = _path(kind, filename)
        if not os.path.exists(path):
            label = os.path.relpath(path, ROOT).replace("\\", "/")
            missing.append(label)
        setattr(data, attr, read_csv(path))

    for attr, filename in (("replay_summary", "replay_summary.json"),
                           ("live_summary", "live_summary.json")):
        path = os.path.join(gateway_dir, filename)
        if not os.path.exists(path):
            missing.append(f"gateway/data/{filename}")
        setattr(data, attr, read_json(path))

    if not data.dispatch.empty:
        data.dispatch["ts"] = pd.to_datetime(data.dispatch["ts"], errors="coerce")
    if not data.grid.empty:
        data.grid["ts"] = pd.to_datetime(data.grid["ts"], errors="coerce")
    if not data.telemetry.empty:
        data.telemetry["ts"] = pd.to_datetime(data.telemetry["ts"], errors="coerce")
    if not data.commands.empty:
        data.commands["ts"] = pd.to_datetime(data.commands["ts"], errors="coerce")

    data.missing = missing
    return data


def _mean(value: Any) -> Any:
    """Annual metrics are stored as {mean, p10, p90} blocks."""
    if isinstance(value, dict):
        return value.get("mean")
    return value


def annual_rows(data: DashboardData, scenario: str) -> pd.DataFrame:
    """Baseline vs SAANJH headline metrics for one scenario."""
    block = data.scenario(scenario)
    baseline = block.get("baseline", {})
    saanjh = block.get("saanjh", {})
    rows = [
        # Stored as a fraction (0.986), displayed as a percentage.
        ("Essential supply availability", "essential_supply_availability", "%", 100.0),
        ("Outage hours per home", "outage_hours_per_home", "h", 1.0),
        ("Outage hours inside deficit", "outage_hours_in_deficit_per_home", "h", 1.0),
        ("Banded (partial-service) hours", "banded_hours_per_home", "h", 1.0),
        ("Energy not served", "energy_not_served_kwh", "kWh", 1.0),
        ("DT overload", "dt_overload_hours", "h", 1.0),
        ("DT peak loading", "dt_peak_loading_pct", "%", 1.0),
    ]
    out = []
    for label, key, unit, scale in rows:
        before = _mean(baseline.get(key))
        after = _mean(saanjh.get(key))
        if before is None and after is None:
            continue
        out.append({
            "metric": label,
            "unit": unit,
            "baseline": None if before is None else before * scale,
            "saanjh": None if after is None else after * scale,
            "delta": None if before is None or after is None else (after - before) * scale,
        })
    return pd.DataFrame(out)


def scorecard_rows(data: DashboardData, scenario: str) -> pd.DataFrame:
    block = data.reliability.get("scenarios", {}).get(scenario, {})
    rows = []
    for item in block.get("scorecard", []):
        rows.append({
            "metric": item.get("label", item.get("key")),
            "unit": item.get("unit", ""),
            "baseline": item.get("baseline", {}).get("mean"),
            "saanjh": item.get("saanjh", {}).get("mean"),
            "p10": item.get("saanjh", {}).get("p10"),
            "p90": item.get("saanjh", {}).get("p90"),
        })
    return pd.DataFrame(rows)


def low_income_points(data: DashboardData, group: str) -> pd.DataFrame:
    points = data.low_income.get("groups", {}).get(group, {}).get("points", [])
    return pd.DataFrame(points)


def robustness_cases(data: DashboardData) -> pd.DataFrame:
    return pd.DataFrame(data.robustness.get("cases", []))


def calibration_checks(data: DashboardData) -> pd.DataFrame:
    checks = data.calibration.get("calibration_targets", {}).get("checks", {})
    rows = []
    for key, item in checks.items():
        target = item.get("target", [None, None])
        rows.append({
            "check": key,
            "value": item.get("value"),
            "target_low": target[0] if len(target) > 0 else None,
            "target_high": target[1] if len(target) > 1 else None,
            "ok": item.get("ok"),
        })
    return pd.DataFrame(rows)


def forecast_rows(data: DashboardData) -> pd.DataFrame:
    models = data.calibration.get("forecast", {}).get("models", [])
    return pd.DataFrame(models)


def replay_kpis(summary: dict[str, Any]) -> dict[str, Any]:
    """Normalise the names used by gateway Recorder.summary()."""
    return {
        "telemetry_sent": summary.get("telemetry_sent"),
        "telemetry_received": summary.get("telemetry_received"),
        "packet_success_pct": summary.get("packet_success_pct"),
        "commands_sent": summary.get("commands_sent"),
        "commands_delivered": summary.get("commands_delivered"),
        "command_success_pct": summary.get("command_success_pct"),
        "command_ack_pct": summary.get("command_ack_pct"),
        "mean_latency_ms": summary.get("mean_command_latency_ms"),
        "p95_latency_ms": summary.get("p95_command_latency_ms"),
        "soc_min_pct": summary.get("soc_min_pct"),
        "reserve_breaches": summary.get("reserve_breaches"),
        "overload_before_min": summary.get("overload_minutes_before"),
        "overload_after_min": summary.get("overload_minutes_after"),
        "commanded_kwh": summary.get("commanded_kwh"),
        "delivered_kwh": summary.get("battery_energy_delivered_kwh"),
        "profile_peak_kw": summary.get("profile_peak_kw"),
        "hours": summary.get("hours"),
        "nodes": len(summary.get("nodes", [])),
    }
