# SAANJH Claim Traceability Matrix

Every claim presented in the Hackathon submission materials (`docs/SUBMISSION.md`, `README.md`, video, dashboard) is grounded in traceable, reproducible source code and data artifacts.

| Claim | Metric / Value | Classification | Source Code / Data Artifact | Verification Method |
|---|---|---|---|---|
| **Peak Load Reduction** | Baseline: 154.14 kW<br>SAANJH: 109.18 kW<br>(**44.95 kW / 29.2% reduction**) | GENERATED RESULT | `simulation/feeder_sim.py`<br>`simulation/data/results/comparison.json` | Run `feeder_sim.py`; inspect `baseline_peak_kw` vs `saanjh_peak_kw`. |
| **Overload Duration Reduction** | Baseline: 90 min<br>SAANJH: 60 min<br>(**30 min / 33.3% reduction**) | GENERATED RESULT | `simulation/feeder_sim.py`<br>`simulation/data/results/reliability_scorecard.json` | Evaluated across 72 timesteps of transformer rated thermal threshold (95 kW). |
| **Voltage Violations Relief** | Baseline: 6 violations<br>SAANJH: 0 violations<br>(**100% eliminated**) | GENERATED RESULT | `simulation/validators/pypsa_validator.py`<br>`simulation/data/results/pypsa_saanjh_validation.csv` | Measured via Newton-Raphson AC load flow solver at feeder tail (<220V). |
| **Technical Loss Reduction** | Baseline: 25.87 kWh<br>SAANJH: 16.74 kWh<br>(**35.3% reduction**) | GENERATED RESULT (Modeled Proxy) | `simulation/validators/pypsa_validator.py`<br>`simulation/data/results/reliability_scorecard.json` | Modeled resistive-loss proxy ($I^2R$) across 250m aluminum conductor. |
| **Dependable Flexibility Delivered** | **56.25 kW peak** / 61.57 kWh delivered | GENERATED RESULT | `simulation/virtual_battery/aggregator.py`<br>`simulation/data/results/flexibility_response.json` | Aggregated battery discharge + deferrable load shedding. |
| **Delivery Compliance Ratio** | **0.985 (98.5%)** | GENERATED RESULT | `simulation/data/results/comparison.json` | Ratio of delivered flexibility to required flexibility during stress. |
| **Safety Invariants** | 0 critical load cuts<br>0 reserve breaches<br>0 opt-out dispatches | GENERATED RESULT | `simulation/models/household.py`<br>`simulation/models/battery.py` | Verified invariant counters across all 60 households. |
| **Household Fleet Participation** | 39 active, 3 opted out (out of 42 battery homes in 60-home cluster) | CONFIGURATION & RESULT | `config/saanjh.yaml`<br>`simulation/data/results/household_dispatch.csv` | Governed by `homes_with_inverter_battery: 42` and 5% opt-out policy. |
| **Battery Usable Capacity** | 22% available capacity (~400 Wh) / 70% emergency reserve | CONFIGURATION & MODEL | `config/saanjh.yaml`<br>`simulation/models/battery.py` | Enforced by `Battery.discharge()` preventing discharge below 70% SOC. |
| **Prototype Hardware BOM** | **₹22,143** Total Physical Prototype Cost | MEASURED BATCH | `README.md`<br>`simulation/economics_engine.py` | Itemized prototype purchases: RAK4631 (₹2,999), Sensors (₹7,869), CM4 (₹11,275). |
| **Cost per Dependable kW** | **₹7,068 / kW** | ILLUSTRATIVE ASSUMPTION | `simulation/data/results/economics_scenarios.json` | Initial deployment capex amortized over peak kW relief vs ₹45k/kW BESS. |
| **ML Load Forecasting Accuracy** | XGBoost outperforming Naive Persistence | GENERATED RESULT | `artifacts/models/real_xgboost_model.pkl`<br>`artifacts/real_data/model_comparison.json` | Evaluated on real-world UCI power consumption benchmark dataset. |
| **Blender Digital Twin Fidelity** | Procedural 3D digital twin with telemetry HUD | GENERATED VISUAL | `blender/scripts/animate_event.py`<br>`artifacts/video/saanjh_digital_twin_preview.mp4` | Bound dynamically to `artifacts/blender/saanjh_visualization_data.json`. |
| **Physical Hardware Demonstration** | LoRa sensor acquisition and packet transmission | PHYSICAL PROTOTYPE | Stitched in `artifacts/video/saanjh_final_presentation.mp4` | Video evidence of LoRa RF transmission from sensor stack. |
