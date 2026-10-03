# SAANJH Final Submission Freeze Manifest

**Event:** Schneider Electric Yuva Yodha Tech Hackathon 2026  
**Track:** Challenge 03 – Making Clean Power Dependable  
**Timestamp:** 2026-10-03T15:05:00+05:30  
**Phase:** **FINAL FREEZE (PHASE 33)**  
**Status:** **PERMANENT FREEZE — ALL GATES PASSED**  

---

## 1. Runtime Environment & Dependencies
- **Operating System:** Windows 10/11
- **Python Version:** 3.10.11
- **Key Dependencies:**
  - `pypsa` == 0.35.4 (AC power flow validation)
  - `xgboost` == 3.2.0 (predictive load forecaster)
  - `streamlit` == 1.54.0 (operator decision dashboard)
  - `pandas` == 2.3.3, `numpy` == 2.2.6, `scipy` == 1.15.3
  - `joblib` == 1.5.3, `matplotlib` == 3.10.8, `plotly` == 6.6.0
  - `pytest` == 9.1.1 (testing framework)

---

## 2. Canonical Physical Configuration (`config/saanjh.yaml`)
- **Distribution Transformer:** 100 kVA (95 kW nominal rating, 65°C rated rise, 35°C ambient)
- **Feeder Architecture:** 415V / 240V 3-phase 4-wire radial network, 250m aluminum conductor ($R=0.08\,\Omega, X=0.02\,\Omega$)
- **Neighborhood Size:** 60 households (42 equipped with inverter-batteries, 15 with 1 kWp rooftop solar PV)
- **Inverter Battery Parameters:** 1,800 Wh capacity (150Ah/12V), 800W inverter rating, 70% emergency blackout reserve lock
- **Consumer Participation:** 39 active homes, 3 opted out (5% opt-out rate rigorously tested)

---

## 3. Authoritative Verification Artifact Hashes

| Artifact Path | SHA256 Signature (First 16 chars) | Role in Submission |
|---|---|---|
| `simulation/data/results/comparison.json` | `6c1ac2dce5dc8980` | Headline judging metrics |
| `simulation/data/results/reliability_scorecard.json` | `e07c11b34d4bf908` | Challenge 03 baseline vs SAANJH scorecard |
| `simulation/data/results/pypsa_saanjh_validation.csv` | `bcac26aadacd1792` | Independent AC load flow & loss validation |
| `simulation/data/results/household_dispatch.csv` | `f77d48fba8a94c25` | Household fairness, reserves & compensation |
| `simulation/data/results/flexibility_request.json` | `c88ed71c7b792fd6` | DISCOM machine-to-machine contract |
| `simulation/data/results/flexibility_response.json` | `d9cb6012c4d69010` | SAANJH edge response contract |
| `artifacts/blender/saanjh_visualization_data.json` | `eb32d76a854f8c00` | 3D procedural digital twin data contract |
| `artifacts/video/saanjh_final_presentation.mp4` | `86547af475c7862c` | Master 1080p 30 FPS stitched presentation video |

---

## 4. Final Validation Matrix

- **Challenge 03 Core Intermittency Gap:** **PASS** (Sunset drop-off explicitly mitigated via 56.25 kW dependable flexibility)
- **Transformer Thermal Overload:** **PASS** (Duration cut from 90 min to 60 min, 33.3% reduction)
- **Feeder Voltage Stability:** **PASS** (Tail voltage violations 100% eliminated via PyPSA AC power flow)
- **Modeled Resistive Feeder Losses:** **PASS** (35.3% reduction from 25.87 kWh down to 16.74 kWh)
- **Critical Load Invariant:** **PASS** (0 critical load cuts across all homes)
- **Battery Reserve Invariant:** **PASS** (0 reserve breaches; min SOC = 0.81 ≥ 0.70)
- **Fairness & Opt-Out Invariant:** **PASS** (3 opted-out homes received 0 dispatches)
- **50-Run Monte Carlo Robustness:** **PASS** (Mean peak reduction: 48.9 kW; 0% failure rate)
- **Multi-Vector Mutation Tests:** **PASS** (Causal coupling confirmed across fleet size, homes, and solar)
- **Automated Test Suite:** **PASS** (`pytest` 100% passing)

---

## 5. Non-Blocking Limitations
1. Field physical prototype validated sensing and LoRa transmission; multi-inverter power dynamometer testing is slated for Stage 2 pilot.
2. The network model represents a radial low-voltage distribution feeder; multi-feeder mesh distribution is planned for Stage 3.
3. Machine learning training used the public UCI benchmark dataset; localized Indian residential datasets will be gathered during the Stage 1 pilot.
