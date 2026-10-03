# Data Provenance

## Real Data (Used for Forecasting Model)
- **Dataset**: UCI Individual Household Electric Power Consumption
- **Source**: UCI Machine Learning Repository
- **URL**: https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip
- **License**: Open Data / Public Domain
- **Download date**: 2026-10-03
- **SHA-256**: 9f84b46ade8a2d8e1286ec4b2b6c2987a45a755c59f263be3b3b3d10dfbda3ff
- **Date range**: 2006-12-16 to 2007-11-26 (first ~500k rows used for demo)
- **Temporal resolution**: 15-minute (downsampled from 1-min raw)
- **Target**: `target_load_kw` (next 15-minute average)
- **Known limitations**: Geographic mismatch. Represents a French household, not an Indian neighbourhood. Used to prove methodology (XGBoost time-series learning), NOT absolute baseline loads.

## Synthetic Data (Used for Digital Twin Evaluation)
- **Dataset**: SAANJH 60-Home Neighbourhood Digital Twin
- **Source**: `simulation/feeder_sim.py` (Procedurally generated during execution)
- **Purpose**: Evaluates the dispatcher response and flexibility intervention against physical limits.
- **Strict Separation**: The synthetic data is purely an evaluation sandbox. The ML forecast engine was strictly trained on the REAL data above.
