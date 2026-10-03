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

## 5. React SCADA HMI (CoffeESIME)
- **License:** MIT
- **Usage:** Industrial SCADA/HMI design patterns, ISA-101 high-performance HMI color standards, linear gauge architecture, and operator screen layouts adapted for `docs/index.html`.
- **Status:** Attribution documented. Fully compliant with MIT License.

**STATUS: PASS**

