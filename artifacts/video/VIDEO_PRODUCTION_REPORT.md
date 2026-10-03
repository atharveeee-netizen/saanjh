# SAANJH Video Production & Technical Verification Report

**Project:** SAANJH (Neighbourhood Flexibility Network for Renewable-Deficit Reliability)  
**Track:** Schneider Electric Yuva Yodha Tech Hackathon 2026 — Challenge 03  
**Target Video Deliverable:** Final 5-Minute Technical Demonstration Video  
**Production Standard:** Industrial Digital Twin & Operations Center Standard (No promotional fluff, clean audio for live narrator overlay)  

---

## 1. Master Video Specifications

| Metric | Target Specification | Achieved Master Deliverable | Status |
| :--- | :---: | :---: | :---: |
| **Total Duration** | 4:50 – 5:20 (~5:00) | **5:09.11 (309.11s)** | **PASS** |
| **Resolution** | 1080p (1920 × 1080) | **1920 × 1080** | **PASS** |
| **Aspect Ratio** | 16:9 widescreen | **16:9 (1.78:1)** | **PASS** |
| **Frame Rate** | 30.00 FPS | **30.00 FPS constant** | **PASS** |
| **Video Codec** | H.264 (AVC) / High Profile | **libx264 (CRF 18, yuv420p)** | **PASS** |
| **Audio Specification** | Clean / No baked voiceover / No music | **Clean silent stream (-an)** | **PASS** |
| **Container Format** | MP4 | **MPEG-4 Part 14 (.mp4)** | **PASS** |

---

## 2. Segment Breakdown & Video Timeline

The master video (`artifacts/video/saanjh_final_5min_submission.mp4`) is constructed into 6 sequential, technically rigorous segments:

```
[0:00 - 0:20] Segment 1: Opening & Renewable Intermittency Problem Statement (20.0s)
[0:20 - 1:30] Segment 2: Website Walkthrough Part 1 — Overview, Architecture & Baseline (70.0s)
[1:30 - 2:02] Segment 3: Real Physical Hardware Telemetry Evidence (32.11s)
[2:02 - 4:24] Segment 4: Website Walkthrough Part 2 — Deficit, Forecast, Dispatch, Recovery & DISCOM (142.0s)
[4:24 - 4:54] Segment 5: Extended 3D Blender Digital Twin Operational Sequence (30.0s)
[4:54 - 5:09] Segment 6: Reliability Scorecard, Unit Economics & Challenge 03 Conclusion (15.0s)
TOTAL RUNTIME: 309.11 seconds (5 minutes 9.11 seconds)
```

---

### Detailed Timeline Progression

| Timestamp | Duration | Section Name | Source Asset | Visual Elements & Scientific Content |
| :--- | :---: | :--- | :--- | :--- |
| **0:00 – 0:20** | 20.0s | **Opening Problem Statement** | `cards/opening_card.png` | Schneider Electric Challenge 03 framing; solar cliff (sunset) coinciding with returning residential demand; 154.1 kW coincident peak on 100 kVA transformer (115% loading). |
| **0:20 – 1:30** | 70.0s | **System Overview & Baseline** | `saanjh_website_walkthrough_master.mp4` (0–70s) | Landing hero; 6 core KPI cards; baseline unmanaged load; 90-minute transformer thermal overload duration; tail-end voltage dipping below 220V. |
| **1:30 – 2:02** | 32.11s | **Real Hardware Evidence** | `hardware_demonstration.mp4` | **100% Physical Prototype:** RAKwireless WisBlock RAK4631 (nRF52840 + SX1262 LoRa 865 MHz) transmitting telemetry packets; lower-third banner. |
| **2:02 – 4:24** | 142.0s | **Core Workflow & Grid Recovery** | `saanjh_website_walkthrough_master.mp4` (70–212s) | **5 Operational Tabs:**<br>• *Tab 1:* Solar cliff drop-off vs. 80.75 kW safe limit line.<br>• *Tab 2:* PyPSA AC power flow voltage stabilization to 226V (0 violations).<br>• *Tab 3:* 56.25 kW flexibility dispatch across 39 homes, $\ge 70\%$ SOC reserve floor invariant.<br>• *Tab 4:* XGBoost forecaster, iteration 171 early stopping, benchmark table, 0 data leakage.<br>• *Tab 5:* DISCOM action plan directive (`"DISPATCH 56.2 kW FOR 45 MINS"`) & ₹7,068/kW unit capex. |
| **4:24 – 4:54** | 30.0s | **Extended 3D Digital Twin** | `saanjh_blender_digital_twin_30s.mp4` | **6 Cinematic Operational Shots:**<br>• *Shot 1 (0–6s):* Establishing wide shot.<br>• *Shot 2 (6–12s):* Camera sweep to transformer & feeder.<br>• *Shot 3 (12–18s):* Sunset transition & deficit alert.<br>• *Shot 4 (18–24s):* LoRa communication pulse.<br>• *Shot 5 (24–30s):* Household batteries glowing green, grid cooling.<br>• *Shot 6 (30–36s):* Stabilized wide grid view. |
| **4:54 – 5:09** | 15.0s | **Conclusion & Verification** | `cards/closing_card.png` | 4 metric impact boxes (↓44.95 kW peak, 30 min overload avoided, 0 violations, ₹7,068/kW); PyPSA 100% convergence certification; GitHub link. |

---

## 3. Data Provenance & Real vs. Simulated Boundaries

| Scene / Element | Nature | Data Source File | Scientific Boundary Notes |
| :--- | :---: | :--- | :--- |
| **Hardware Clip (1:30–2:02)** | **REAL PHYSICAL** | `artifacts/video/hardware_demonstration.mp4` | Physical WisBlock RAK4631 LoRa node capturing and transmitting live RF packets over 865 MHz. Demonstrates edge sensing & telemetry. |
| **AI Forecaster (Tab 4)** | **REAL DATA TRAINED** | `artifacts/models/real_xgboost_model.pkl` | Trained on 2,075,259 raw readings from UCI benchmark downsampled to 15-minute intervals. Audited chronological split; 0 data leakage; early stopping @ iteration 171. |
| **Feeder Load Curves** | **SIMULATION** | `simulation/data/results/saanjh_profile.csv` | 60-home residential feeder simulated under 100 kVA distribution transformer thermal constraints. |
| **AC Power Flow / Voltages** | **NUMERICAL SOLVER** | `simulation/data/results/pypsa_saanjh_validation.csv` | Independent AC Newton-Raphson load flow solver (PyPSA) on 415V/240V radial topology. 100% of 72 snapshots converged. |
| **Digital Twin Geometry & HUD** | **PROCEDURAL 3D** | `artifacts/blender/saanjh_visualization_data.json` | Blender 5.2 EEVEE procedural rendering directly driven by simulation frame-by-frame timestep outputs. Zero hardcoded HUD values. |

---

## 4. Anti-Hardcoding & Integrity Certification

1. **No Fabricated KPIs:** All numbers in the dashboard, Blender HUD, title cards, and video segments originate from `simulation/data/results/comparison.json`.
2. **Hard Reserve Floor Invariant:** Battery SOC floor ($\ge 70\%$) is strictly preserved in both simulation and visualization (min final SOC = 81%, 0 reserve breaches).
3. **No Decorative Fiction:** The virtual community battery is explicitly presented as a logical aggregation of existing residential inverter-batteries, not as an imaginary physical central container.
4. **Clean Presentation Audio:** The video is exported without music or AI voice, providing presenter-ready timing for live hackathon presentation and defense.
