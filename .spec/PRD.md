# Product Requirements Document (PRD) — SAANJH

**Project:** SAANJH (Neighbourhood Flexibility Network for Renewable-Deficit Reliability)  
**Author:** Akshit Aggarwal & Team  
**Competition:** Schneider Electric Yuva Yodha 2026 (Track: Grid Reliability & Renewable Intermittency)  
**Phase:** Prototype Round (Deadline: 7 December 2026, 23:59 IST)  

---

## 1. Problem Statement & Opportunity
In Indian distribution networks, evening renewable intermittency (17:00–23:00) causes steep supply deficits. DISCOMs manage these deficits via blunt rotational feeder load-shedding, cutting 100% of power to all connected households regardless of willingness to shed non-essential loads. With only 4–5% of Indian homes owning private inverters (concentrated among the affluent), peri-urban and low-income households disproportionately bear the blackout burden.

SAANJH provides an equitable, edge-coordinated essential supply layer at the Distribution Transformer (DT) level (100 kVA, 200–250 households).

## 2. Core Value Propositions
1. **Guaranteed Essential Supply:** Preserve lights, fans, mobile charging, and refrigeration for all households during grid deficit events.
2. **Frugal & Retrofit-Friendly:** Uses existing RDSS smart meters for load limiting, second-life EV battery packs for community storage, and low-cost (<₹1,500) LoRa relays for private inverter borrowing.
3. **Regulatory & Financial Alignment:** Integrates with state Demand Flexibility Portfolio Obligations (DFPO in MH, KA, RJ) using open standards (OpenADR / IEEE 2030.5).
4. **Safety & Fail-Safe by Construction:** Normally-closed (NC) hardware relay connections, hardware-enforced 70% SoC reserve, and physical push-button opt-out.

## 3. User Personas & Stakeholders
- **Low-Income Household:** Receives unbroken essential power (no total blackout), alerts via SMS/WhatsApp/IVR in Hindi/Marathi.
- **Inverter-Owning Household:** Lends fractional battery power (>70% SoC preserved), earns monthly DISCOM bill credits, maintains physical override switch.
- **DT Substation Operator / SHG:** Local community operator managing enrolment, maintenance, and visual alarms.
- **DISCOM Grid Engineer:** Commands aggregate DT flex capacity, receives OpenADR telemetry, verifies DFPO compliance.

## 4. Key Performance Indicators (KPIs)
- **Essential Availability:** Increase from ~59% (baseline) to >95% during deficit windows.
- **Outage Hours:** Reduce from >200 h/year to <15 h/year per household.
- **Reserve Breaches:** Exactly 0 breaches below 70.0% SoC on household inverters.
- **Unit Economics:** Levelized cost of preserved essential supply <₹15/household-hour.
