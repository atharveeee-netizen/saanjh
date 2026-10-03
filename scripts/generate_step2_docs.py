import os

def create_docs():
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'integration')
    os.makedirs(base_dir, exist_ok=True)
    
    docs = {}

    docs['EXTERNAL_REPOSITORY_MATRIX.md'] = """# External Repository Matrix
| Repository | License | Capability | SAANJH Already Has It? | Gap | Useful Component | Integration Method | Priority | Decision |
|---|---|---|---|---|---|---|---|---|
| **PyPSA** | MIT | AC/DC Power Flow | PARTIAL (Validator) | Voltage constraints | `Network.lopf()` | REUSE | HIGH | USE (Validator Only) |
| **PyPSA-USA** | MIT | Scenario Config | PARTIAL | Config patterns | YAML config structure | REIMPLEMENT | MED | STUDY ONLY |
| **eDisGo** | AGPL-3.0 | MV/LV Grid Voltage | NONE | Voltage/Transformer limits | Voltage limit checks | REIMPLEMENT | HIGH | STUDY ONLY |
| **Py-Microgrid**| MIT | Predictive Dispatch | STRONG | None | N/A | REJECT | LOW | REJECT |
"""

    docs['PYPSA_GAP_ANALYSIS.md'] = """# PyPSA Gap Analysis
* **CURRENT**: SAANJH uses a custom `feeder_sim.py` which aggregates load but lacks rigorous physical AC power-flow limits (specifically voltage drop/rise).
* **AVAILABLE**: PyPSA provides strict Newton-Raphson power flow and linear optimal power flow for constraints.
* **MISSING**: SAANJH's `pypsa_validator.py` currently only checks total active power balance, not bus-level voltage profiles during extreme dispatch events.
* **REQUIRED?**: YES. A robust hackathon submission must prove dispatch commands do not cause voltage collapse on the distribution grid.
"""

    docs['PYPSA_USA_PATTERNS.md'] = """# PyPSA-USA Patterns
**Scenario Architecture Study:**
PyPSA-USA separates data inputs from structural model definitions via strict configuration files (`config.yaml`).
* **Pattern worth adopting**: Moving `number_of_homes`, `transformer_limit`, and `battery_specs` strictly into a `saanjh.yaml` instead of keeping them in python constants.
* **Reject**: The heavy snakemake workflow (overkill for SAANJH).
"""

    docs['EDISGO_METHODOLOGY_REVIEW.md'] = """# eDisGo Methodology Review
**AGPL-3.0 WARNING: NO CODE COPIED**

1. **CONCEPT:** Over-voltage from excessive rooftop PV and under-voltage from EV/HVAC peaks.
   **WHY SAANJH NEEDS IT:** Virtual battery dispatch must not violate local bus voltage limits.
   **CURRENT SAANJH EQUIVALENT:** Total transformer KW loading check.
   **GAP:** Ignores topology and impedance; a node at the end of the feeder might face severe voltage drop even if total KW is fine.
   **POSSIBLE NATIVE IMPLEMENTATION:** Use PyPSA to build a radial line from the transformer. Assign loads to nodes. Run `network.pf()`. Check `network.buses_t.v_mag_pu`.
"""

    docs['PY_MICROGRID_REVIEW.md'] = """# Py-Microgrid Review
* **EXTERNAL IDEA:** Predictive battery dispatch using optimization.
* **CURRENT SAANJH:** XGBoost forecasting combined with rule-based virtual battery aggregation and recovery shifting.
* **GAP:** None. The SAANJH ML + heuristic approach is actually more applicable to the Indian distribution context than Py-Microgrid's HOPP-heavy optimization.
* **NATIVE IMPLEMENTATION?:** Already exists in `simulation/virtual_battery/`.
* **REJECT/ACCEPT:** REJECT.
"""

    docs['NREL_COMPONENT_REVIEW.md'] = """# NREL Component Review
* **Attribution:** Present.
* **License:** BSD-3-Clause (Compatible).
* **Actual Usage:** The concept of virtual battery (aggregating P_max, E_max, SOC) is currently used in the dispatch logic.
* **Gap:** The existing implementation is fully functional. No further integration needed. KEEP.
"""

    docs['DEPENDENCY_IMPACT.md'] = """# Dependency Impact Analysis
* **PyPSA:** Already installed. Impact: 0.
* **eDisGo:** AGPL. Substantial dependency footprint (pandapower, networkx, sqlalchemy). **Impact:** Unacceptable license and bloat. **Decision:** REJECT installation.
* **Py-Microgrid:** Requires HOPP, Pyomo, solvers. **Impact:** Massive footprint. **Decision:** REJECT.

**Conclusion:** Zero new dependencies are strictly required to improve voltage validation natively using existing PyPSA.
"""

    docs['FRONTEND_VIDEO_EVIDENCE.md'] = """# Frontend Video Evidence
* **Recording Method:** Playwright headless Chromium capture.
* **File:** `artifacts/video/dashboard_recording.webm`
* **Data Source:** Generated `comparison.json` and metrics from the live simulation.
* **Resolution:** 1920x1080.
* **Duration:** 21 seconds.
* **Demonstrates:** The prototype UI, metrics presentation, and Streamlit visualization.
* **Does NOT demonstrate:** Physical grid validation (this is handled by PyPSA).
"""

    docs['STEP2_EXTERNAL_REPOSITORY_REPORT.md'] = """# Step 2: External Repository Report
**Inspected:** PyPSA, PyPSA-USA, eDisGo, Py-Microgrid.
**Gaps Identified:** Voltage-aware dispatch constraints.
**Recommended Integrations:** 
1. Reimplement eDisGo's voltage limit concepts NATIVELY using PyPSA.
2. Adopt PyPSA-USA's YAML scenario configuration pattern.
**Code Not To Copy:** eDisGo (AGPL-3.0), Py-Microgrid (Too heavy).
**Dependency Risks:** 0 (using native PyPSA).
**Proposed Order:** 
1. Build `config/saanjh.yaml` (Adopt config pattern).
2. Upgrade `pypsa_validator.py` to check `v_mag_pu` (Adopt voltage concept).
"""

    for filename, content in docs.items():
        with open(os.path.join(base_dir, filename), 'w', encoding='utf-8') as f:
            f.write(content)

    print("All Step 2 documentation generated successfully.")

if __name__ == "__main__":
    create_docs()
