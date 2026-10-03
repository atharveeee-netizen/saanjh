# SAANJH: State of the Art & Novelty Analysis

## 1. Literature Review: Distribution Transformer & Flexibility Management

Our research into existing approaches for load forecasting and residential flexibility (specifically focusing on developing nations like India) revealed three major paradigms:

### Approach A: The Centralized VPP (Virtual Power Plant)
*   **Examples:** FlexMeasures (Open Source), Tesla Autobidder, GridSignal.
*   **How it works:** Cloud-based servers ingest smart meter data over the internet (4G/Wi-Fi), run complex optimization (MILP or RL), and send dispatch commands back to residential assets.
*   **The Flaw in India:** Internet reliability. During extreme evening peak loads, grid voltage drops often cause home broadband routers to reboot or lose sync. Relying on cloud APIs during the exact moment of grid stress is a critical single point of failure. 

### Approach B: High-Voltage Feeder Upgrades
*   **Examples:** Traditional DISCOM CAPEX (e.g., adding 500 kVA transformers to replace 100 kVA ones).
*   **How it works:** Brute force. When a neighbourhood's demand exceeds transformer capacity, the utility simply lays thicker cables and installs a larger transformer.
*   **The Flaw in India:** Extremely high cost (₹8,000 to ₹15,000 per kW of upgrade) and physical space constraints in dense urban/peri-urban neighbourhoods.

### Approach C: "Smart" Metering (AMI) for Time-of-Use (ToU) Pricing
*   **Examples:** EESL Smart Meter National Programme (India).
*   **How it works:** Smart meters send 15-minute load profiles to the utility. The utility charges higher tariffs during peak hours to *encourage* manual load shifting.
*   **The Flaw in India:** Behavioral fatigue. Residents will not manually turn off their ACs every evening just to save a few rupees. Automation is required.

---

## 2. Competitive Comparison: SAANJH vs. The Status Quo

| Feature | Centralized VPPs | Smart Meters (ToU) | **SAANJH (Our Approach)** |
| :--- | :--- | :--- | :--- |
| **Control Plane** | Cloud / API | Human Behavioral | **Local Edge (LoRaWAN)** |
| **Communication** | 4G / Wi-Fi | Cellular (GPRS/LTE) | **LoRa (868 MHz ISM band)** |
| **Asset Visibility** | Inverter APIs (Requires API access) | Aggregate House Load | **Direct CT Clamp at Inverter/Main** |
| **Response Time** | Minutes (Cloud round-trip) | Hours/Days | **< 3 seconds (Edge loop)** |
| **Cost** | High (Cloud compute) | ₹6,000+ per meter | **₹3,000 for Gateway, ₹350 per Node** |

---

## 3. Our Core Novelty

Based on the literature review, SAANJH introduces three specific novelties designed for the Indian grid context:

### Novelty 1: The "Cloudless" Edge Dispatch (LoRaWAN Class A/C)
Unlike Western VPPs that rely on Wi-Fi and Cloud APIs, SAANJH's critical loop operates entirely locally.
We utilize the **RAKwireless WisBlock (nRF52840 + SX1262)** at the home, communicating directly with a **Raspberry Pi CM4 Edge Gateway** located at the distribution transformer via LoRa 868MHz. 
**Why this matters:** If the internet goes down during a thunderstorm or voltage sag, SAANJH still balances the transformer because the intelligence is running on the CM4 at the edge, not in AWS.

### Novelty 2: Hardware-Native Load Disaggregation
Research papers relying on the eMARC dataset often struggle with Non-Intrusive Load Monitoring (NILM) to separate battery charging from AC usage.
**Our Novelty:** We bypass complex software NILM entirely by using a dual-CT clamp approach on our custom **Qashu PCB**. By physically clamping the inverter output and the mains, we get perfect, deterministic flexibility estimation without heavy AI inference at the node.

### Novelty 3: Fairness-Constrained Greedy Optimization
Existing models either dispatch all batteries at once (causing a massive rebound peak when they finish) or use computationally heavy Linear Programming.
SAANJH uses a lightweight **Staggered Greedy Heuristic** that can run on a Raspberry Pi CM4. It divides homes into dynamically assigned cohorts, discharging them sequentially to flatten the curve rather than creating a secondary rebound peak.

---

## 4. Future Work & Adaptations

From academic literature, we plan to adapt the following for SAANJH Phase 2:
*   **Federated Learning:** Instead of the CM4 doing all load forecasting, we can train lightweight models on the RAK4631 nodes (using Edge Impulse) to predict individual home behavior, only transmitting the model weights to the CM4.
*   **Battery Degradation Penalty:** Incorporating the cost of battery cycle degradation into the dispatch optimizer, ensuring we don't unfairly degrade a specific resident's lead-acid or Li-ion battery.
