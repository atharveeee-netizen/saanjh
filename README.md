# SAANJH ⚡
## Neighbourhood Flexibility Network for Renewable-Deficit Reliability

![Challenge 3](https://img.shields.io/badge/Challenge-3-3DCD58.svg)
![Schneider Electric](https://img.shields.io/badge/Schneider-Electric-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)

### The Problem
India's grid faces a massive evening peak as solar generation drops and residential demand surges. This causes severe distribution transformer stress and voltage violations at the neighbourhood level.

### The Solution
SAANJH is a low-cost, LoRa-based edge network that turns existing household inverter batteries and deferrable loads into a coordinated **Virtual Community Battery**. It aggregates flexibility to relieve transformer stress locally, without requiring expensive new grid storage.

### Quick Start
To run the SAANJH feeder simulator and view the live grid control dashboard:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the 60-home feeder simulation
python simulation/feeder_sim.py

# 3. Launch the SAANJH Grid Control Dashboard
streamlit run dashboard/app.py
```

### Measured Impact (Simulated)
Based on a 60-home simulation on a 100 kVA transformer:

| Metric | Baseline | With SAANJH | Improvement |
|--------|----------|-------------|-------------|
| Peak Load | 91.2 kW | 76.8 kW | **15.8% Reduction** |
| Overload Duration | 85 min | 12 min | **86% Reduction** |
| Voltage Violations | 14 | 3 | **78% Reduction** |
| Dependability Ratio | - | 88.9% | **High Reliability** |

### Architecture
SAANJH bridges the last-mile gap, operating as a localized edge layer beneath the DISCOM's central ADMS/DERMS systems.

* **Sense:** Home nodes measure load and battery SOC.
* **Predict:** Gateway forecasts evening stress using local load models.
* **Optimise:** Dispatches minimal required flexibility.
* **Verify:** Transformer sentinel confirms constraint relief.

---
*Built for the Schneider Electric Yuva Yodha Tech Hackathon 2026.*
