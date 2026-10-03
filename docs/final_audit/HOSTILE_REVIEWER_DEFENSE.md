# SAANJH Hostile Technical Reviewer Defense Audit

**Evaluation:** Hostile Technical Panel Pre-Submission Defense  
**System:** SAANJH (Neighbourhood Flexibility Network)  
**Track:** Challenge 03 – Making Clean Power Dependable  

---

### 1. PROBLEM: Does this actually solve renewable intermittency?
**YES.** SAANJH specifically addresses the evening rooftop solar drop-off (the "Solar Cliff" where solar generation drops to 0 at sunset between 17:00 and 18:30) coinciding with returning residential demand. It bridges this gap by aggregating 33 kW / 16.6 kWh of existing distributed household inverter-batteries into an autonomous, dispatchable virtual battery bank that supplies local energy during the deficit.

### 2. RELIABILITY: Where is the measurable reliability improvement?
- **Transformer Thermal Overload:** Overload duration is cut from 90 minutes down to 60 minutes (**33.3% / 30-minute reduction**), preventing distribution transformer insulation breakdown.
- **Feeder Tail Voltage Violations:** Reduced from 6 events to 0 (**100% eliminated**), maintaining tail voltage above 218V (>0.90 p.u.).
- **Net Peak Load:** Slashed by **44.95 kW (29.2% reduction)** from 154.14 kW down to 109.18 kW.

### 3. BASELINE: What exactly is the baseline?
The baseline is the exact same 60-home neighborhood on the same 100 kVA transformer with the same solar profiles and appliance loads operating **unmanaged** (without SAANJH intervention). In the baseline, batteries do not discharge to support the grid, deferrable loads run unconstrained, and the transformer overloads for 90 continuous minutes.

### 4. FORECAST: Does the forecast actually affect dispatch?
**YES.** The XGBoost forecast engine predicts the 1-step-ahead (15–45 min) feeder load. If the predicted load exceeds the transformer's 95 kW safe rating, the deficit is computed as `required_flex_kw = predicted_load - 95 kW`, directly setting the setpoint for the virtual battery aggregator.

### 5. DISPATCH: Does dispatch respect battery constraints?
**YES.** Every battery is bounded by a hard physical reserve constraint of **≥70% SOC**. Once a battery drops to 70% SOC, `Battery.get_available_power()` returns 0.0 kW, and the battery physically stops discharging. In the simulation, across all 42 battery homes, min final SOC was 0.81, with exactly **zero reserve breaches**.

### 6. CRITICAL LOAD: Can SAANJH accidentally compromise essential loads?
**NO.** Essential loads (lighting, ceiling fans, television, refrigeration, and cooking) are hardcoded as non-deferrable base loads. They are never shed or curtailed. Only flexible loads (AC setpoint adjustment, EV charging delay, geyser shifting) and battery discharge participate. **Critical load violations = 0**.

### 7. VOLTAGE: Does the electrical model actually calculate voltage?
**YES.** Bus voltages are not decorative heuristic formulas. They are computed by running an independent non-linear AC Newton-Raphson load flow solver using **PyPSA** (`simulation/validators/pypsa_validator.py`) on a 415V/240V 3-phase 4-wire radial network with realistic conductor impedances. 100% of all 72 snapshots converged.

### 8. LOSSES: Are losses actually calculated?
**YES.** Modeled resistive feeder losses ($I^2R$) are calculated through the PyPSA line power flow ($P_{\text{send}} + P_{\text{receive}}$). Under SAANJH, modeled losses drop from 25.87 kWh to 16.74 kWh (**35.3% reduction**), accurately labeled as a *"modeled resistive-loss proxy"*.

### 9. DISCOM: What actionable information does the utility receive?
The operator receives a concrete directive via `discom_action_plan.json`:
`"DISPATCH 56.2 kW FOR 45 MINUTES VIA SAANJH EDGE"`, specifying expected overload avoidance (30 mins), voltage restoration (>218V), and technical loss savings (9.13 kWh).

### 10. LOCAL: What can continue operating if internet connectivity fails?
**Everything behind the feeder continues operating.** Home nodes communicate with the pole-mounted gateway via local 865 MHz LoRa RF. The edge gateway runs local XGBoost inference and dispatch scheduling locally on the Raspberry Pi CM4. If upstream fiber/cellular to the DISCOM central office goes down, the gateway operates autonomously.

### 11. AFFORDABILITY: Why can a low-income neighbourhood afford this?
Because households **do not buy batteries or solar panels for SAANJH**. 70% of urban Indian households already own inverter batteries for blackout protection. SAANJH only installs a low-cost LoRa CT monitor (₹2,999), achieving dependable capacity at **₹7,068 / kW**, over 6x cheaper than utility BESS (₹45,000–₹65,000 / kW).

### 12. OWNERSHIP: Who owns and maintains it?
- Batteries: Owned by households.
- Nodes & Gateway: Owned by DISCOM / Aggregator as distribution instrumentation.
- Maintenance: Handled by trained local electricians via a 5% annual O&M reserve fund.

### 13. ECONOMICS: Who pays whom?
The DISCOM compensates households ₹1.50/kWh for battery dispatch (delivered as an automated electricity bill credit), paid out of the DISCOM's savings from avoiding expensive evening peak spot power (₹10–₹12/kWh).

### 14. DATA: What is real and what is simulated?
- **REAL:** The UCI Household Power Consumption dataset was used to train and validate the XGBoost load forecasting model (`real_xgboost_model.pkl`).
- **SIMULATED:** The 60-home Indian distribution feeder, transformer thermal model, battery fleet state machine, and intervention impact are simulated via the digital-twin engine (`feeder_sim.py`).

### 15. HARDWARE: What was physically demonstrated?
A physical prototype of the RAKwireless WisBlock RAK4631 (nRF52840 + SX1262 LoRa) acquiring sensor telemetry and transmitting packets over LoRa RF to a receiving edge gateway, recorded in `artifacts/video/saanjh_final_presentation.mp4`.

### 16. VALIDATION: What was independently validated?
- AC power flow and voltage stability independently solved via PyPSA.
- Statistical robustness confirmed over a 50-run Monte Carlo simulation (0% failure rate).
- Causal data coupling verified via multi-parameter mutation testing (`scripts/mutation_test.py`).

### 17. REPRODUCIBILITY: Can another engineer run it?
**YES.** Any engineer can clone the repository, install `requirements.txt`, and execute `python simulation/feeder_sim.py` and `pytest` in under two minutes to reproduce all results.

### 18. IP: What external code was used?
- PyPSA (GPLv3) used strictly as an external validation harness.
- XGBoost (Apache 2.0) for ML forecasting.
- Virtual battery concepts adapted from NREL (BSD-3-Clause) with full attribution in `docs/THIRD_PARTY_COMPONENTS.md`.

### 19. LIMITATIONS: What does SAANJH NOT prove?
- It does not prove commercial-scale multi-feeder mesh distribution.
- It does not prove hardware-in-the-loop (HIL) dynamometer inverter testing (planned for Stage 2 pilot).
- Battery degradation models are linear proxies, not electrochemical cycle-life physics.
