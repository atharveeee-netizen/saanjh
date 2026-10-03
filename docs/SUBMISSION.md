# SAANJH: Neighbourhood Flexibility Network
## Yuva Yodha Energy Tech Hackathon 2026 — Challenge 3

---

### Slide 1: The Intermittency Gap
*   **The Problem:** At 18:00, solar generation falls while neighbourhood demand rises.
*   **The Result:** Distribution transformers approach thermal limits, leading to voltage violations and grid instability.
*   **The Challenge 3 Mandate:** Make clean power dependable, neighbourhood by neighbourhood.

---

### Slide 2: The Invisible Resource
*   **60 Homes = 15 kW of Flexibility**
*   Indian households already own a massive fleet of inverter batteries and deferrable loads (ACs, pumps).
*   **The SAANJH Insight:** Instead of asking the community to buy an expensive shared battery, aggregate what already exists.

---

### Slide 3: How SAANJH Works
*   **Sense:** Low-cost IoT nodes monitor home loads and battery SOC.
*   **Predict:** Edge gateway forecasts evening stress using local load models.
*   **Optimise:** Calculates the exact flexibility needed to keep the transformer under 95% load.
*   **Dispatch:** Sends LoRa commands to stagger battery discharge and defer loads.
*   **Verify:** Transformer sentinel confirms constraint relief.

---

### Slide 4: Why SAANJH is Different
1.  **Storage-Light:** Uses batteries households already own.
2.  **Localised Communication:** LoRa-based edge network; does not require continuous broadband at every home.
3.  **Utility-Facing:** Provides feeder stress and flexibility visibility directly to the DISCOM.
4.  **Measurable Impact:** Every event validates a baseline vs. intervention improvement.

---

### Slide 5: Quantified Demonstration (Simulated)
*Based on a 60-home python simulation on a 100 kVA transformer.*
*   **Baseline Peak:** 91.2 kW
*   **SAANJH Peak:** 76.8 kW
*   **Peak Reduction:** 15.8% (14.4 kW)
*   **Overload Duration:** Reduced from 85 mins to 12 mins.
*   **Dependable Flexibility Ratio:** 88.9%

*(Insert Load Comparison Chart from `simulation/plots/load_comparison.png`)*

---

### Slide 6: Regulatory Tailwinds
*   **RERC 2026:** Mandates DISCOMs treat demand as a dispatchable resource (DFPO targets).
*   **MERC 2024:** Sets flexibility targets of 1.5% to 3.5%.
*   **Draft NEP 2026:** Prioritizes DER aggregation frameworks.
*   **Conclusion:** SAANJH provides the exact aggregator model that regulators are now mandating.

---

### Slide 7: Unit Economics & Ownership
*   **Ownership:** Local Operator (RWA/SHG) manages the system via a Flexibility Contract with the DISCOM.
*   **Value Exchange:** DISCOM gets dependable flexibility -> Operator gets paid -> Households get bill credits.
*   **Capital Efficiency:** SAANJH Edge (₹ 2,083/kW) vs Community Battery (₹ 25,000/kW).

*(Insert Money Flow Diagram)*

---

### Slide 8: Schneider Electric Ecosystem Fit
*   **The Missing Link:** Schneider's EcoStruxure ADMS & DERMS orchestrate the grid, but lack low-voltage, behind-the-meter visibility.
*   **Integration:** SAANJH acts as the "Last Mile" edge network, feeding aggregated flexibility data upward via MQTT/REST.

*(Insert Schneider Integration Diagram)*

---

### Slide 9: Measurement & Validation Plan
*   **Phase 1 (Baseline):** Measure transformer loading, voltage, and peak duration without intervention.
*   **Phase 2 (Event):** Trigger SAANJH dispatch and measure identical parameters.
*   **Phase 3 (Report):** Output quantified reliability improvement to validate the Dependable Flexibility Ratio.

---

### Slide 10: Prototype Roadmap
1.  **Now:** Conceptual design + Python Feeder Simulator + Architecture.
2.  **Round 2:** 3-5 physical LoRa nodes bench-tested.
3.  **Validation:** Live baseline vs. intervention measurements.
4.  **Final:** Neighbourhood-scale digital twin + hardware demonstrator + utility dashboard.
