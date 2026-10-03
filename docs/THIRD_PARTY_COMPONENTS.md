# Third-Party License & Attribution Audit

SAANJH leverages numerous open-source tools. All integrations have been verified to comply with their respective licenses.

## 1. NREL Virtual Battery Aggregator
- **License:** BSD-3-Clause (NREL standard)
- **Usage:** Concepts adapted for `VirtualBatteryAggregator` inside `simulation/virtual_battery/aggregator.py`.
- **Status:** Attribution maintained in documentation and module docstrings.

## 2. PyPSA (Python for Power System Analysis)
- **License:** GPLv3
- **Usage:** Independent validator in `simulation/validators/pypsa_validator.py`.
- **Status:** SAANJH uses PyPSA as an imported dependency (`import pypsa`), operating strictly as a validation harness (SaaS/Internal analysis model). The SAANJH core logic itself is independent and does not modify PyPSA source.

## 3. XGBoost
- **License:** Apache 2.0
- **Usage:** Predictive forecasting model.
- **Status:** Included in `requirements.txt`. Legal to use and distribute.

## 4. Plotly & Streamlit
- **License:** MIT / Apache 2.0
- **Usage:** Dashboard UI generation.
- **Status:** Unmodified dependencies. Fully compliant.

## 5. FUXA (frangoteam)
- **Source:** https://github.com/frangoteam/FUXA
- **Purpose:** SCADA/HMI/process-visualization frontend foundation
- **License:** MIT
- **Upstream commit:** `64eb012e0333e65bae83b96a7f116f1fccd3434f`
- **SAANJH-specific work:**
  - Feeder visualization (FDR-023 topology, 11 kV busbar, CB-23, DT-100KVA-04, 415V lateral spine)
  - SAANJH data integration (adapter mapping canonical CSV/JSON simulation results into FUXA tags)
  - Household flexibility visualization (60-node matrix with battery SOC and reserve floors)
  - Transformer loading visualization (thermal stress duration and limit indicators)
  - Feeder tail voltage visualization (Node 60 RMS profile against statutory limits)
  - Dispatch and renewable cliff event presentation (18:30 PV drop-off, 56.25 kW dispatch)
  - DISCOM action interface (operator directive execution and economic sensitivity breakdown)
  - SAANJH branding, operational telemetry replay, and technical documentation

## 6. React SCADA HMI (CoffeESIME)
- **Source:** https://github.com/CoffeESIME/react-scada-hmi
- **License:** MIT
- **Usage:** Evaluated for ISA-101 high-performance HMI color patterns and linear gauge standards.

**STATUS: PASS**


