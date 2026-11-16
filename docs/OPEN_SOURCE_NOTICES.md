# Open Source Notices & Attribution

SAANJH's own source is released under the MIT License (see `LICENSE`). The
components below remain under their upstream licences; the MIT licence does not
override them. The Streamlit dashboard is the primary evidence UI; the React
console in `ui/` is a secondary design artefact.

## Additional Open-Source Components
- **NREL Virtual Battery Aggregator:** BSD-3-Clause (architecture reference)
- **PyPSA (Python for Power System Analysis):** MIT (validation harness; not GPL)
- **pvlib:** BSD-3-Clause (planned calibration module)
- **pandapower:** BSD-3-Clause (planned LV power-flow validation)
- **OpenEMS:** EPL-2.0 (architecture reference only; not vendored)
- **FlexMeasures:** Apache-2.0 (architecture reference only; not vendored)
- **OpenLEADR:** Apache-2.0 (future OpenADR integration only; not vendored)
- **RadioLib:** MIT (SX1262 driver, linked as a library)
- **Adafruit nRF52 Arduino core:** LGPL-2.1 (build framework)
- **RAK4631 WisBlock variant:** LGPL-2.1 (vendored in `firmware/rak4631_node/variants/`)
- **XGBoost:** Apache-2.0 (predictive load forecasting)
- **scikit-learn:** BSD-3-Clause (forecast baselines)
- **FastAPI:** MIT (backend API)
- **pydantic:** MIT (result contracts)
- **Streamlit:** Apache-2.0 (HIL/evidence dashboard)
- **Plotly.py:** MIT (dashboard charts)

The prototype deliberately avoids GPL/AGPL code in distributed components.
PyPSA is MIT; it remains a validation-only dependency. RadioLib is MIT. The
Adafruit nRF52 core is LGPL-2.1 and is used through its public APIs; its source
is available from the pinned versions in `firmware/rak4631_node/platformio.ini`.
