# Open Source Notices & Attribution

SAANJH's own source is released under the MIT License (see `LICENSE`). The
components below remain under their upstream licences; the MIT licence does not
override them. FUXA is vendored for reference but is **not** on the prototype's
critical path; the Streamlit dashboard is the primary evidence UI.

## FUXA SCADA/HMI Platform (vendored, optional)
- **Project:** FUXA — Web-based Process Visualization (SCADA/HMI/Dashboard)
- **Author / Organization:** frangoteam (https://github.com/frangoteam)
- **Repository:** https://github.com/frangoteam/FUXA
- **License:** MIT License
- **Upstream Revision:** `64eb012e0333e65bae83b96a7f116f1fccd3434f`
- **Usage in SAANJH:** retained as an optional process-visualisation reference. The Phase 1 prototype uses the Streamlit dashboard and does not require FUXA to run.

## MIT License Notice (FUXA)
```
MIT License

Copyright (c) 2019 frangoteam

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Additional Open-Source Components
- **NREL Virtual Battery Aggregator:** BSD-3-Clause (architecture reference)
- **PyPSA (Python for Power System Analysis):** MIT (validation harness; not GPL)
- **pvlib:** BSD-3-Clause (planned calibration module)
- **pandapower:** BSD-3-Clause (planned LV power-flow validation)
- **OpenEMS:** EPL-2.0 (architecture reference only; not vendored)
- **FlexMeasures:** Apache-2.0 (architecture reference only; not vendored)
- **OpenLEADR:** Apache-2.0 (future OpenADR integration only; not vendored)
- **RadioLib:** LGPL-2.1 (SX1262 driver, linked as a library)
- **Adafruit nRF52 Arduino core:** LGPL-2.1 (build framework)
- **RAK4631 WisBlock variant:** LGPL-2.1 (vendored in `firmware/rak4631_node/variants/`)
- **XGBoost:** Apache-2.0 (predictive load forecasting)
- **scikit-learn:** BSD-3-Clause (forecast baselines)
- **FastAPI:** MIT (backend API)
- **pydantic:** MIT (result contracts)
- **Streamlit:** Apache-2.0 (HIL/evidence dashboard)
- **Plotly.py:** MIT (dashboard charts)
- **Chart.js:** MIT License (optional trend visualization)

The prototype deliberately avoids GPL/AGPL code in distributed components.
PyPSA is MIT; it remains a validation-only dependency. RadioLib and the nRF52
core are LGPL-2.1 libraries used through their public APIs; their source is
available from the pinned versions in `firmware/rak4631_node/platformio.ini`.
