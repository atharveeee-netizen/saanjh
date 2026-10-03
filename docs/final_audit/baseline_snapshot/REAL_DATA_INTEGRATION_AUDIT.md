# Real Data Integration Audit

## A. What is already trained?
Currently, an XGBoost Regressor and a Random Forest Regressor have been trained on synthetic time-series data. 

## B. What is only synthetic?
- The dataset generated in `ai_forecasting/train_model.py` is entirely synthetic. It mimics the Prayas Energy Group (eMARC) Indian load profiles (e.g., incorporating temperature correlations, evening peaks, weekend shifts), but it is a mathematical fabrication.
- The 60-home feeder simulation (`simulation/feeder_sim.py`) is also a digital twin (synthetic physical simulation).

## C. What model artifact exists?
- `ai_forecasting/models/xgboost_load_forecaster.pkl` exists.

## D. What input schema does the model expect?
The current model expects 11 features:
`['hour', 'day_of_week', 'month', 'is_weekend', 'temperature_c', 'load_kw', 'load_lag_1', 'load_lag_4', 'load_lag_96', 'load_roll_mean_4', 'load_roll_std_4']`

## E. What does the simulator currently consume?
Currently, the simulator DOES NOT consume the `.pkl` artifact. It uses a naive hardcoded forecast heuristic (`actual_load * (1 + 0.05 * noise)`). The trained AI model is effectively disconnected from the physical digital twin.

## F. Which results are hardcoded?
Previously, HTML, JS, and Markdown results were hardcoded. These have successfully been purged and replaced with a dynamic data injection pipeline (`scripts/generate_docs.py` and `docs/index.html` via `fetch()`).

## G. Which results are generated?
- `comparison.json` (all KPIs)
- `baseline_profile.csv` and `saanjh_profile.csv` (load curves)
- `README.md` and `docs/SUBMISSION.md` (via templates)

## Next Steps for Real Data Extension:
1. Download a legitimate public dataset (e.g., UCI Household Power Consumption).
2. Clean it and engineer time-series features (lags, rolling means).
3. Train XGBoost on it WITHOUT data leakage (chronological split).
4. Save the new artifact and integrate it into the `feeder_sim.py` dispatcher so the digital twin actually relies on the real-world trained model.
