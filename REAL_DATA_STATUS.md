# Real Data Status

DATASET: UCI Individual Household Electric Power Consumption (15-min downsampled)
SOURCE: UCI Machine Learning Repository
LICENSE: Open Data / Public Domain
DATE RANGE: 2006-12-16 to 2007-11-26
RESOLUTION: 15-minute
RECORD COUNT: 32981 processed observations

MODEL: XGBoost Regressor
TRAINING PERIOD: First 80% (chronological)
VALIDATION PERIOD: Next 10%
TEST PERIOD: Final 10%

BASELINE METRICS: MAE 0.3222 kW, RMSE 0.4485 kW, R2 0.812
XGBOOST METRICS: MAE 0.3091 kW, RMSE 0.4421 kW, Best Iteration: 171

MODEL SAVED: YES (artifacts/models/real_xgboost_model.pkl)
MODEL RELOADED: YES (Verified by tests/test_model_reload.py)
SIMULATION INTEGRATED: YES (RealWorldForecastEngine implemented in feeder_sim.py with 60-home explicit upscaling)
DASHBOARD UPDATED: YES (Metrics dynamically flow to frontend via scripts/generate_docs.py and comparison.json)
BLENDER UPDATED: N/A (Existing visual model unaffected by background forecast heuristic changes)

DATA LIMITATIONS: The dataset represents an individual French household, while our target is an Indian feeder. It is utilized strictly to train and validate the forecasting methodology, not to perfectly simulate Indian ambient temperatures or cultural loads.
MODEL LIMITATIONS: The XGBoost model is unaware of spontaneous real-time faults or network topology, only historical patterns.
SAANJH SIMULATION LIMITATIONS: The simulation interpolates 15-minute XGBoost forecasts into the 5-minute Dispatcher loop using explicit scalar translation.

REPRODUCTION COMMAND: `.venv\Scripts\python.exe ai_forecasting\train_real_model.py` followed by `.venv\Scripts\python.exe simulation\feeder_sim.py`

FILES CREATED:
- data/download_real_dataset.py
- data/preprocess_real_dataset.py
- ai_forecasting/train_real_model.py
- tests/test_model_reload.py
- docs/REAL_DATA_INTEGRATION_AUDIT.md
- artifacts/real_data/xgboost_training_history.csv
- artifacts/models/real_xgboost_model.pkl
- REAL_DATA_STATUS.md
