# SAANJH Digital Twin — Voiceover Script

**Target Duration**: 2 minutes
**Target Video**: `saanjh_digital_twin_voiceover_ready.mp4`

---

## 00:00–00:10
**VISUAL**: 
Shot 1 — Establishing. Wide view of the 60-home neighbourhood digital twin. The central transformer is connected via the LV feeder to the homes. The HUD displays "SAANJH DIGITAL TWIN — SIMULATED EVENT".

**VOICEOVER**: 
"Welcome to SAANJH. This is a digital twin of an Indian neighbourhood, simulating sixty homes, connected to a single distribution transformer. As urban loads grow, these transformers face critical thermal stress."

---

## 00:10–00:25
**VISUAL**: 
Shot 3 & 4 — Normal Operation to Evening Stress. The sun visibly sets. Solar generation drops to zero. Energy flow from the grid to the homes accelerates. The Transformer HUD shows load climbing past 85% safety margins. The transformer material begins to glow red.

**VOICEOVER**: 
"During the evening peak, solar generation vanishes just as residential demand surges. Here, we see the baseline simulation: without intervention, the transformer quickly exceeds its physical limits, triggering voltage violations and reducing asset lifespan."

---

## 00:25–00:40
**VISUAL**: 
Shot 5 — Forecast. The camera focuses on a floating technical HUD. The `RealWorldForecastEngine` (trained on real UCI data) projects the next 60 minutes. A clear trendline crosses the red safety threshold.

**VOICEOVER**: 
"But SAANJH anticipates the stress. Our edge AI, utilizing an XGBoost model trained on real-world consumption patterns, forecasts the impending overload up to an hour in advance. This gives the local gateway time to act."

---

## 00:40–01:00
**VISUAL**: 
Shot 6 — Dispatch. SAANJH activates. Participating homes (with batteries and flexible loads) highlight in bright green. The energy flow reverses locally: batteries discharge to offset household demand.

**VOICEOVER**: 
"Before the overload occurs, SAANJH calculates the exact flexibility required and dispatches a localized signal. Participating inverters seamlessly deploy stored energy. Instead of drawing from the strained grid, these homes become self-sufficient, providing instant relief."

---

## 01:00–01:15
**VISUAL**: 
Shot 7 & 8 — Transformer Response (Baseline vs SAANJH). Split screen or sequential comparison. The SAANJH transformer cools down (red to grey) as the load drops from 163 kW to 126 kW.

**VOICEOVER**: 
"The physical results are immediate. In this simulated event, SAANJH shaved peak demand by over twenty-two percent, completely eliminating transformer overloads without requiring expensive infrastructure upgrades."

---

## 01:15–01:30
**VISUAL**: 
Shot 9 — Economics & Physical Hardware. The HUD shifts to display the actual ₹42,695 BOM cost. A small picture-in-picture window shows the physical Raspberry Pi prototype reading telemetry.

**VOICEOVER**: 
"This flexibility is highly affordable. Our physical edge gateway, built on a Raspberry Pi CM4 with LoRa communication, achieves this level of protection for a one-time capital expense of roughly twelve-hundred rupees per dependable kilowatt."

---

## 01:30–01:50
**VISUAL**: 
Shot 10 — Final System View. The camera pulls back to the wide establishing shot. The neighbourhood is stable. 
TEXT: SAANJH — Neighbourhood-Scale Flexibility.

**VOICEOVER**: 
"SAANJH bridges the gap between massive ADMS systems and the edge. By unlocking the latent flexibility of everyday appliances, we deliver a resilient, clean, and locally coordinated grid. Thank you."
