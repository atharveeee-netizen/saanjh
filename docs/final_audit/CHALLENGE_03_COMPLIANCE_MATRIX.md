# Challenge 03 Compliance Matrix: Making Clean Power Dependable

**Track:** Schneider Electric Yuva Yodha Tech Hackathon 2026 – Challenge 03  
**Target:** Bridging the gap when renewable sources are intermittent  
**System:** SAANJH (Neighbourhood Flexibility Network)  
**Audit Date:** 2026-10-03  

---

## Executive Assessment

The objective of Challenge 03 is to transform intermittent renewable energy into a dependable, resilient power supply at the distribution edge without requiring prohibitive grid-scale capital expenditure. This matrix audits SAANJH against all four primary challenge criteria.

---

## Requirement 1: Bridge Intermittency Gaps

> **Criterion:** The solution must bridge the gap between variable renewable generation and fixed consumer demand, providing dependable capacity during solar drop-off and evening peak surge.
> 
> **Chain of Causality:**
> $$\text{Renewable Supply (Rooftop Solar)} \longrightarrow \text{Solar Decline (18:00)} \longrightarrow \text{Renewable-Demand Deficit} \longrightarrow \text{XGBoost Load Forecast} \longrightarrow \text{Flexibility Requirement} \longrightarrow \text{Local Dispatch} \longrightarrow \text{Reliability Improvement}$$

### Compliance Evidence
1. **Explicit Deficit Event Modeling:** The simulation explicitly models 15 solar-equipped households (1 kWp each) whose generation declines to zero between 17:00 and 18:30 while evening residential demand (ACs, cooking, water heating) surges from 35 kW to >160 kW.
2. **Deficit Energy Calculation:** The renewable-deficit event creates an unmanaged transformer overload (exceeding the 100 kVA rating) for 90 minutes.
3. **Dependable Flexibility:** Rather than relying on simple peak shaving, SAANJH calculates the *dependable flexibility requirement* ($P_{\text{req}}$) to neutralize the solar drop-off and schedules staggered inverter-battery discharge and deferrable load shifts across 42 participating homes.
4. **Verified Relief:** Overload duration is cut by 50% (90 min $\to$ 45 min), and tail-end feeder voltage drop violations are halved (8 $\to$ 4).

| Audit Item | Current Status | Evidence Path |
|---|---|---|
| Solar Drop-Off Modeled | **COMPLIANT** | `simulation/feeder_sim.py` (`SOLAR_PROFILES`) |
| Renewable Deficit Quantified | **COMPLIANT** | `simulation/data/results/reliability_scorecard.json` |
| Forecast Drives Dispatch | **COMPLIANT** | `artifacts/models/real_xgboost_model.pkl` |
| Reliability Metric Improvement | **COMPLIANT** | `simulation/data/results/comparison.json` |

---

## Requirement 2: Stay Local and Manageable

> **Criterion:** The architecture must operate reliably at the neighborhood/feeder scale with minimal reliance on continuous cloud connectivity or heavy centralized intervention.

### Operational Boundaries
- **What runs locally (Behind the Feeder):**
  - High-frequency sensor acquisition (sub-second current, voltage, SOC).
  - LoRa peer-to-peer telemetry (868/865 MHz ISM band, zero cellular data cost).
  - Edge Gateway (Raspberry Pi CM4) executing local XGBoost inference and dispatch scheduling.
  - Fail-safe autonomous operation: If upstream Internet/DISCOM link fails, the gateway continues local transformer defense autonomously based on local CT measurements.
- **What is transmitted to DISCOM:**
  - Aggregated 5-minute telemetry: Feeder P/Q, aggregated available flexibility (kW), committed flexibility, transformer winding temperature, feeder health status.
- **What NEVER leaves the neighborhood:**
  - Raw per-second household power traces, appliance signatures, indoor occupancy, or individual household SOC states (preserving consumer privacy).

| Audit Item | Current Status | Evidence Path |
|---|---|---|
| Neighborhood-Scale Topology | **COMPLIANT** | 60 homes, single 100 kVA DT, 400V/230V radial feeder |
| Local LoRa RF Mesh/Star | **COMPLIANT** | RAK4631 WisBlock + SX1262 LoRa physical prototype |
| Local Edge Autonomous Fallback | **COMPLIANT** | Edge Gateway logic operates disconnected from cloud |
| Minimal Upstream Bandwidth | **COMPLIANT** | Lightweight MQTT telemetry (< 2 KB/minute) |

---

## Requirement 3: Genuinely Affordable

> **Criterion:** The solution must be economically accessible for Indian distribution environments, avoiding costly dedicated battery banks or complex infrastructure overhauls.

### Capital & Operational Breakdown (60-Home Cluster)

| Cost Component | Prototype Actual | Commercial Scaled (Per Cluster) | Cost Per Dependable kW | Notes |
|---|---|---|---|---|
| **Hardware CAPEX** | ₹22,143 | ₹1,25,000 (60 nodes + GW) | ₹7,812 / kW | Utilizing *existing* inverters; only adding LoRa CT monitor |
| **Installation & Commissioning** | DIY / Prototype | ₹15,000 (1 technician-day) | ₹937 / kW | Non-invasive CT clamp + inverter serial connection |
| **Annual O&M & Replacement** | ₹0 | ₹6,000 / year | ₹375 / kW-yr | 5% annual reserve for node battery/antenna replacement |
| **Communication OPEX** | ₹0 | ₹0 | ₹0 | Unlicensed 865 MHz LoRa (No SIM cards required) |
| **Household Compensation** | Modeled | ₹1.50 / kWh dispatched | Variable | Offsets battery cycle wear; credited via electricity bill |

**Affordability Verdict:** By aggregating existing behind-the-meter inverter batteries (70% urban penetration in India), SAANJH achieves dependable capacity at **< ₹10,000 per kW**, compared to **₹45,000–₹65,000 per kW** for utility-scale BESS.

---

## Requirement 4: Support the DISCOM

> **Criterion:** The system must provide actionable operational intelligence directly to utility distribution operators (ADMS/DMS/SCADA), not just academic predictions.

### DISCOM Operator Dashboard Outputs
1. **Feeder Stress Level:** Immediate status flag (`NORMAL`, `WARNING`, `CRITICAL`).
2. **Actionable Directive:** e.g., *"DISPATCH 16 kW FLEXIBILITY FOR 45 MINUTES TO PREVENT 100 kVA TRANSFORMER THERMAL OVERLOAD"*.
3. **Transformer Asset Health:** Winding temperature tracking and remaining thermal runway.
4. **Feeder Voltage Risk:** Predicted tail-end voltage under-voltage $(< 0.94\text{ p.u.})$.
5. **Technical Loss Reduction:** Modeled $I^2R$ resistive loss savings during peak hours.

| Audit Item | Current Status | Evidence Path |
|---|---|---|
| Actionable Decision Interface | **COMPLIANT** | `app.py` DISCOM Advisory Console |
| Machine-to-Machine Contract | **COMPLIANT** | `simulation/data/results/flexibility_request.json` |
| Thermal Health Modeling | **COMPLIANT** | IEEE C57.91-based top-oil/winding temperature simulation |
| Resistive Loss Assessment | **COMPLIANT** | Feeder branch $I^2R$ calculation |
