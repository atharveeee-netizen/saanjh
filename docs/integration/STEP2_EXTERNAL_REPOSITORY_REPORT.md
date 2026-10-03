# Step 2: External Repository Report
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
