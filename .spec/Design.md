# Design & Human Interface Guidelines — SAANJH

**Project:** SAANJH  
**Scope:** Streamlit Evidence Console, React Operator/Field Console, and Multilingual Messaging  

---

## 1. Visual Token Hierarchy & Palette
- **Primary / Grid Normal (Green):** `#3DCD58` (Healthy feeders, high availability, active supply).
- **Warning / Essential Band (Amber):** `#F2A900` (Load-capped households, evening deficit, reserve hold).
- **Critical / Shedding (Red):** `#D64545` (Full disconnection, battery fault, reserve violation).
- **Telemetry / Inverter (Blue):** `#3B82F6` (Active inverter discharge, smart meter signals).
- **Background / Neutral (Dark):** `#0D1117` / `#161B22` (High-contrast industrial SCADA dark theme).

## 2. Evidence Console Layout (Streamlit)
- **Persistent Header:** Headline availability KPI (98% vs 59%), SAIDI reduction (240h $\rightarrow$ 10.8h), Unserved energy, DT peak loading.
- **Tab 1 — Reliability Scorecard:** Baseline vs SAANJH comparative bars, Gini fairness coefficient.
- **Tab 2 — Energy Reconciliation:** Delivered vs unmet energy conservation checks ($P_{\text{battery}} + P_{\text{deferred}} = P_{\text{delivered}}$).
- **Tab 3 — Low-Income Economics:** Unit costs per preserved household-hour, payback period curves.
- **Tab 4 — Overload & Robustness:** Transformer thermal stress profiles and packet loss tolerance curves (0%, 5%, 20%).
- **Tab 5 — India Calibration:** eMARC load shape validation, ESMI outage distributions, NASA POWER solar insolation.
- **Tab 6 — HIL Gateway:** Live/replay node telemetry table, real-time SoC meters, packet loss and ACK metrics.
- **Tab 7 — DISCOM Dispatch Decisions:** Traceable audit trail explaining every 15-minute load-shedding or curtailment decision.

## 3. Household Accessibility
- **Communication Channels:** Automated WhatsApp template messages, SMS fallbacks, and IVR voice broadcasts.
- **Supported Languages:** English, Hindi (हिन्दी), Marathi (मराठी).
- **No-App Requirement:** Low-income households do not need a smartphone or app; critical status is pushed via standard SMS/IVR.
