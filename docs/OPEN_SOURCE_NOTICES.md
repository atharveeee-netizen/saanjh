# Open Source Notices & Attribution

## FUXA SCADA/HMI Platform
- **Project:** FUXA — Web-based Process Visualization (SCADA/HMI/Dashboard)
- **Author / Organization:** frangoteam (https://github.com/frangoteam)
- **Repository:** https://github.com/frangoteam/FUXA
- **License:** MIT License
- **Upstream Revision:** `64eb012e0333e65bae83b96a7f116f1fccd3434f`
- **Usage in SAANJH:** SCADA/HMI visualization framework, process visualization components, and frontend telemetry infrastructure.
- **SAANJH Modifications & Application Layer:**
  - SAANJH Feeder FDR-023 single-line diagram and process view
  - SAANJH Data Adapter integrating canonical simulation results (CSV/JSON) into the SCADA tag namespace
  - 60-Household residential flexibility fleet matrix visualization
  - Transformer thermal loading and life-extension tracking view
  - Feeder tail voltage sag profile vs statutory limit view
  - DISCOM automated dispatch directive and economic sensitivity interface
  - Replay and edge simulation telemetry driver (operating without claiming false live utility grid connections)

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
- **NREL Virtual Battery Aggregator:** BSD-3-Clause
- **PyPSA (Python for Power System Analysis):** GPLv3 (Validation harness)
- **XGBoost:** Apache 2.0 (Predictive load forecasting)
- **Chart.js:** MIT License (Data trend visualization)
