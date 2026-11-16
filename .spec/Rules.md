# Operational & Engineering Rules — SAANJH

**Project:** SAANJH  
**Standard:** ASD-STE100 Simplified Technical English & Zero-Slop Principles  

---

## 1. Physical & Mathematical Ground Truths
1. **Thermodynamic Integrity:** Energy delivered cannot exceed the mathematical sum of battery output and deferred demand. Every reconciliation must satisfy:
   $$| (E_{\text{battery}} + E_{\text{deferred}}) - E_{\text{delivered}} | \le 2 \times 10^{-3}\text{ kWh}$$
2. **Hard Reserve Floor:** Under no operating condition may an inverter discharge below 70.0% SoC. This rule is enforced independently at both node and gateway tiers.
3. **Fail-Safe Relay Architecture:** Relays must be wired Normally Closed (NC). Any loss of power or signal must default to the grid connection.
4. **Rebound Conservation:** All deferred load (geysers, pumps, ACs) must rebound into future time blocks. Energy is delayed, not magically eliminated.

## 2. Evidence Standards
1. **Labeling Requirement:** Every data point must be explicitly stamped as `REAL DATA`, `CALIBRATED TO REAL DATA`, or `SIMULATED`.
2. **No Hardcoded Metrics:** All documentation, tables, and presentation artifacts must be generated dynamically from code outputs (`results.json`).
3. **No Imaginary Bench Evidence:** Distinguish between firmware code tested in native C++ simulators vs physical radio-frequency oscilloscope bench recordings.

## 3. Coding & Verification Directives
1. **Regression Gate:** The full test suite (`pytest -q` and `pio test -e native`) must pass with zero failures before any commit.
2. **Schema Compliance:** All result bundles must validate against Pydantic models in `simulation/contracts.py`.
