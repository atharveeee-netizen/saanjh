# SAANJH Claim Traceability Matrix

Every claim presented in the Hackathon submission materials (`docs/SUBMISSION.md`, `README.md`, video) is grounded in traceable, reproducible source code and data artifacts.

| Claim | Metric / Value | Source Code / Data Artifact | Verification Method |
|---|---|---|---|
| **Peak Load Reduction** | Baseline: 163.27 kW<br>SAANJH: 162.95 kW<br>(**0.32 kW reduction**) | `simulation/feeder_sim.py`<br>`simulation/data/results/comparison.json` | Run `feeder_sim.py`; inspect `baseline_peak_kw` vs `saanjh_peak_kw`. |
| **Overload Duration Reduction** | Baseline: 90 min<br>SAANJH: 45 min<br>(**50% reduction**) | `simulation/feeder_sim.py`<br>`simulation/data/results/comparison.json` | Evaluated across 72 timesteps of transformer rated thermal threshold (100 kVA). |
| **Voltage Violations Reduction** | Baseline: 8 violations<br>SAANJH: 4 violations<br>(**50% reduction**) | `simulation/feeder_sim.py`<br>`simulation/data/results/comparison.json` | Measured at feeder tails against nominal 230V ± 6% regulatory limits. |
| **Household Fleet Participation** | 42 homes with inverter-batteries (70% penetration) | `config/saanjh.yaml`<br>`simulation/config.py` | Governed by `homes_with_inverter_battery: 42` in 60-home cluster. |
| **Battery Usable Capacity** | 22% available capacity (~400 Wh) / 70% backup reserve | `config/saanjh.yaml` (`battery.reserve_soc: 0.70`, `battery.available_soc: 0.22`) | Enforced by `VirtualBattery` logic preventing deep discharge beyond blackout reserve. |
| **Prototype Hardware BOM** | **₹22,143** Total Physical Prototype Cost | `docs/SUBMISSION.md`<br>`README.md` | Itemized: RAK4631 (₹2,999), Sensors (₹7,869), CM4 Gateway (₹11,275). |
| **ML Load Forecasting Superiority** | Real XGBoost model outperforming naive baseline | `artifacts/models/real_xgboost_model.pkl`<br>`artifacts/real_data/model_comparison.json` | Evaluated on real-world UCI power consumption benchmark dataset. |
| **Blender Digital Twin Fidelity** | Procedural 3D digital twin of 60 homes + transformer | `blender/scripts/animate_event.py`<br>`artifacts/video/saanjh_digital_twin_preview.mp4` | Bound dynamically to `artifacts/blender/saanjh_visualization_data.json`. |
| **Physical Hardware Demonstration** | LoRa node sensor acquisition and transmission | Stitched in `artifacts/video/saanjh_final_presentation.mp4` | Video evidence of LoRa RF transmission from sensor stack. |
