# SAANJH: Neighbourhood Flexibility Network
## Schneider Electric Yuva Yodha Tech Hackathon 2026 — Challenge 03

---

### Slide 1: Executive Overview & Value Proposition
**SAANJH — Neighbourhood Flexibility Network for Renewable-Deficit Reliability**
*Transforming intermittent rooftop solar drop-off into dependable, dispatchable distribution grid capacity.*

![Cover](docs/diagrams/cover_slide.jpg)

**One-Line Proposition:** SAANJH aggregates existing household inverter batteries and deferrable residential loads into an edge-controlled virtual community battery, eliminating distribution transformer thermal overloads during the evening solar drop-off at 1/6th the cost of dedicated utility batteries.

---

### Slide 2: The Challenge — The Renewable Intermittency Gap
Every evening across Indian distribution networks:
* **The Solar Cliff:** Rooftop solar PV generation rapidly declines to zero between 17:00 and 18:30.
* **The Evening Surge:** Returning residents turn on heavy inductive and heating loads (ACs, geysers, EV charging, induction cooking), causing total demand to spike to **154.1 kW**.
* **The Distribution Bottleneck:** The local 100 kVA transformer experiences sustained thermal overloading (90 minutes exceeding 100% capacity) and severe voltage drop at the feeder tail.

![Problem](docs/diagrams/problem_slide.jpg)

---

### Slide 3: The Core Insight — The Invisible Battery Asset
* **India's Distributed Fleet:** Over 70% of urban Indian households already own 150Ah/12V domestic inverter battery systems for backup power.
* **The Opportunity:** A typical 60-home feeder possesses over **33 kW / 16.6 kWh** of flexible capacity.
* **The Move:** Instead of investing in multi-million rupee centralized community batteries, aggregate what already exists behind the meter while hardcoding a **70% emergency blackout reserve** for consumer protection.

---

### Slide 4: The Solution — Closed-Loop Flexibility Dispatch
1. **SENSE:** Non-invasive split-core CT sensors and WisBlock LoRa nodes capture real-time household power and battery SOC.
2. **PREDICT:** Raspberry Pi CM4 edge gateway uses an XGBoost forecaster trained on real data to detect the impending renewable deficit 45 minutes in advance.
3. **OPTIMISE:** Calculates the exact required flexibility (56.2 kW) to neutralize the solar drop-off.
4. **DISPATCH:** Staggers battery discharge across participating homes via local 865 MHz LoRa RF.
5. **VERIFY:** Digital transformer sentinel verifies constraint relief and restores feeder tail voltage.

![Solution](docs/diagrams/solution_slide.jpg)

---

### Slide 5: System Architecture — Edge-to-Utility Hierarchy
SAANJH is positioned as the **Neighbourhood Flexibility Edge Layer** directly beneath Schneider Electric's EcoStruxure ADMS & DERMS.

![Architecture](docs/diagrams/architecture_1791008183566.jpg)

* **Layer 1 (Household Edge):** RAKwireless WisBlock (nRF52840 + SX1262 LoRa) executing local CT sampling and hardcoded battery reserve locks (≥70% SOC).
* **Layer 2 (Feeder Gateway):** Pole-mounted Raspberry Pi CM4 + LoRa HAT running local XGBoost inference and autonomous fail-safe dispatch logic.
* **Layer 3 (Utility Supervisory):** Lightweight MQTT/REST interface providing aggregated feeder health and flexibility contracts to DISCOM ADMS.

---

### Slide 6: Operating Event — Renewable Deficit Timeline
```
16:00 ──> 17:30 ──> 18:15 ──> 18:30 ──> 19:45 ──> 20:30 ──> 22:00
Solar     Solar     XGBoost   SAANJH    Peak      Load       Event
Active    Declining Stress    Dispatch  Deficit   Recovers   Concluded
(15 kW)   (to 0)    Forecast  Active    Relieved  Batteries  (All Homes
                    (56 kW)   (56 kW)   (45 min)  >80% SOC   Reserve Safe)
```
* **Critical-Load Protection:** Non-deferrable loads (refrigeration, lights, fans) are never curtailed.
* **Opt-Out Compliance:** Opted-out households are bypassed with 100% adherence.

---

### Slide 7: Quantified Evidence — Baseline vs. SAANJH
*Based on 60 households on a 100 kVA distribution transformer (FDR-023), verified with PyPSA AC load flow solver:*

| Metric | Baseline (Unmanaged) | With SAANJH Intervention | Quantified Impact |
|---|---|---|---|
| **Peak Feeder Demand** | 154.1 kW | 109.2 kW | **-45.0 kW (-29.2%)** |
| **Overload Duration** | 90 min | 60 min | **-33% Reduction** |
| **Dependable Flexibility**| 0.0 kW | 56.2 kW | **56.2 kW Dispatched** |
| **Voltage Violations** | 6 | 0 | **100% Eliminated** |
| **Modeled Feeder Losses**| 25.9 kWh | 16.7 kWh | **-35.3% Loss Reduction** |
| **Enrolled Fleet** | — | 39 enrolled | **39 Active, 3 Opted-Out** |

![Load Comparison](simulation/plots/load_comparison.png)

---

### Slide 8: DISCOM Decision Layer — Actionable Operations
SAANJH translates predictive AI into direct distribution actions:
* **Feeder Identification:** Feeder FDR-023 / Transformer DT-100KVA-04.
* **Predictive Alert:** Impending thermal overload detected at 18:30 due to solar PV decline.
* **Direct Action:** Dispatched 56.2 kW for 45 minutes.
* **Physical Results:** Avoided 30 minutes of transformer overload, restored voltage to >218V, and saved 35.3% in technical losses.

---

### Slide 9: Unit Economics, Ownership & Deployment Model
* **Illustrative Economics:** Initial cluster deployment cost of **₹3,17,767 (₹7,068 / dependable kW)** vs ₹45,000–₹65,000 / kW for utility-scale BESS.
* **Cash Flow Model:** DISCOM funds low-cost LoRa node deployment; households receive monthly bill credits (₹1.50/kWh dispatched) to reward participation.
* **Phased Rollout:**
  1. *Stage 1 (Now):* 1 Feeder / 1 DT Pilot with bench-tested WisBlock LoRa nodes.
  2. *Stage 2 (Expansion):* 10 DT Feeder Cluster (600 homes) with diverse battery chemistries.
  3. *Stage 3 (Scale):* Substation integration with regional wholesale market bidding (IEX/RTM).

![Money Flow](docs/diagrams/money_flow_1791008227122.jpg)

---

### Slide 10: Prototype Demonstration, Validation & Next Steps
* **Physical Hardware:** Demonstration of physical sensor acquisition and LoRa RF transmission on RAKwireless WisBlock RAK4631 + Raspberry Pi CM4.
* **Rigorous Verification:** 100% data coupling proven via multi-vector mutation tests, 50-run Monte Carlo robustness, and PyPSA AC load flow solver.
* **Challenge 03 Ready:** Fully packaged, documented, and reproducible codebase.

![Roadmap](docs/diagrams/roadmap_slide.jpg)
