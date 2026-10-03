# SAANJH Final Integration & Architectural Report

**Event:** Schneider Electric Yuva Yodha Tech Hackathon 2026  
**Track:** Challenge 03 – Making Clean Power Dependable  
**System:** SAANJH (Neighbourhood Flexibility Network)  
**Status:** **INTEGRATION COMPLETE & CERTIFIED**  

---

## 1. Executive Summary

SAANJH integrates five disparate engineering domains into a unified, responsive distribution-edge flexibility network:
1. **IoT Edge Sensing:** RAKwireless WisBlock (nRF52840 + SX1262 LoRa) for behind-the-meter household telemetry.
2. **Machine Learning Load Forecasting:** Real-world trained XGBoost regression model predicting solar drop-off stress 45 minutes in advance.
3. **Physics-Based Feeder Simulation:** 60-home, 100 kVA distribution transformer network model enforcing IEEE C57.91 thermal dynamics.
4. **Independent Electrical Validation:** Industry-standard PyPSA AC power flow solver calculating genuine bus voltages and resistive line losses.
5. **Operator & Digital Twin Interfaces:** Streamlit-powered DISCOM Decision Console and procedural 3D Blender digital twin.

---

## 2. Integrated Data Pipeline Flow

```
[Real UCI Dataset] ──> [XGBoost Forecaster (15-min Lags)]
                              │
                              ▼ (Load Prediction 45-min Ahead)
[config/saanjh.yaml] ──> [feeder_sim.py] ──> [Virtual Battery Aggregator]
                              │                     │
                              ▼ (Dispatch Schedule) ▼ (LoRa Dispatch to 39 Homes)
                     [Transformer & Feeder State]
                              │
                              ▼ (Timeseries Profiles)
             ┌────────────────┴────────────────┐
             ▼                                 ▼
[PyPSA AC Power Flow]                 [Blender Data Pipeline]
(V_pu, Line Losses kW)                (saanjh_visualization_data.json)
             │                                 │
             ▼                                 ▼
[reliability_scorecard.json]          [saanjh_final_presentation.mp4]
[comparison.json]                     [dashboard/app.py Console]
```

---

## 3. End-to-End Verification Matrix

| Subsystem | Input Source | Processing Engine | Deliverable Artifact | Verification Gate |
|---|---|---|---|---|
| **Forecasting** | UCI Household Dataset | XGBoost (Early Stopping) | `real_xgboost_model.pkl` | Outperforms Naive Persistence |
| **Grid Physics** | `config/saanjh.yaml` | `feeder_sim.py` | `saanjh_profile.csv` | 100% Conservation of Energy |
| **Virtual Battery** | 42 Inverter-Batteries | Analytical Aggregator | `household_dispatch.csv` | Zero breaches of 70% Reserve |
| **AC Load Flow** | Feeder Timeseries | PyPSA (Newton-Raphson) | `pypsa_saanjh_validation.csv` | 100% Snapshot Convergence |
| **DISCOM Decision** | Feeder Stress State | DISCOM Rule Engine | `discom_action_plan.json` | Direct Action Directive |
| **Presentation** | HW Demo + UI + 3D | FFmpeg 1080p Pipeline | `saanjh_final_presentation.mp4` | 53.3s Clean 30 FPS Stream |

---

## 4. Key Performance Highlights

- **Peak Load Relieved:** **44.95 kW (29.2% reduction)** from 154.14 kW down to 109.18 kW.
- **Transformer Overload Reduced:** From **90 minutes down to 60 minutes (33.3% reduction)**.
- **Voltage Violations Eliminated:** From **6 violation events to 0** (tail-end voltage maintained above 218V).
- **Technical Losses Reduced:** Modeled resistive feeder losses reduced by **35.3%** (from 25.87 kWh to 16.74 kWh).
- **Dependable Delivery Compliance:** **98.5%** delivery ratio ($P_{\text{delivered}} / P_{\text{required}}$).
- **Safety Invariants:** 0 critical load curtailments, 0 battery reserve breaches, 0 opt-out violations.
