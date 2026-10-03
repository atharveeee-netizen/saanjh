# Claim Traceability

This document traces every key metric claimed in the SAANJH Hackathon submission back to its programmatic source.

## Rule Enforcement
**"Nothing that appears as an experimental result may be hardcoded."**

1. **Dashboard KPI Table (163 kW -> 126 kW peak)**
   - *Source*: `comparison.json`
   - *Generator*: `simulation/feeder_sim.py`
   - *Method*: Baseline simulation run vs SAANJH intervention run. The real XGBoost model (`real_xgboost_model.pkl`) predicts the load, the SAANJH Dispatcher reacts to the forecast, modifying home states, which yields the new `.csv` curve. The `.md` templates are dynamically injected via `scripts/generate_docs.py`.

2. **Cost per Dependable kW (₹1,172)**
   - *Source*: Computed directly in `feeder_sim.py` at line 153.
   - *Formula*: `int(42695 / peak_reduction_kw)`. The ₹42,695 is the actual BOM of the Raspberry Pi CM4 and LoRa hardware used to build the gateway.

3. **Dependability Ratio**
   - *Source*: Computed in `feeder_sim.py`.
   - *Formula*: `homes_participating / NUM_HOMES`. 

4. **Forecasting Accuracy (MAE 0.309 kW)**
   - *Source*: `artifacts/real_data/model_comparison.json`
   - *Generator*: `ai_forecasting/train_real_model.py`
   - *Method*: XGBoost tested on an untouched 10% chronological split of the real UCI dataset. Evaluated without data leakage.
