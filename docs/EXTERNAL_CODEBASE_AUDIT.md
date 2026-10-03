# External Codebase Audit

## SAANJH Existing Architecture
- **Forecasting:** `ai_forecasting/` uses an XGBoost model trained on real-world UCI data, outputting `.csv` forecasts.
- **Simulation/Digital Twin:** `simulation/feeder_sim.py` runs a basic 60-home digital twin. Dispatch logic is located in `simulation/models/dispatcher.py`. Households, solar, and transformers are modelled individually.
- **Economics:** `simulation/economics_engine.py` dynamically computes CAPEX based on participation volume.
- **Frontend Dashboard:** A basic HTML/JS frontend located at `docs/index.html` fetching from `artifacts/real_data/` and `simulation/data/results/`.
- **Visualization:** `blender/scripts/animate_event.py` runs a dynamic 3D rendering of the event.

## Current Strengths
- Strongly decoupled data flows (JSON/CSV).
- Proven robustness via Monte Carlo (`simulation/run_monte_carlo.py`) and Adversarial Testing (`simulation/run_adversarial_tests.py`).
- Genuine ML (XGBoost) model trained on actual real-world data with no data leakage.
- Completely dynamic Blender animation.

## Current Weaknesses
- **Virtual Battery Aggregation:** Missing a formal, standard-compliant mathematical aggregation layer.
- **Feeder Physics Validation:** Missing independent electrical validation (e.g. PyPSA or OpenDSS).
- **Frontend:** HTML/JS frontend is basic; it needs a robust, premium web framework.

## External Components Required
1. **Virtual Battery Aggregator (NREL):** To formalize the aggregation of flexible loads.
2. **PyPSA / OpenDSS Wrapper:** To independently validate feeder physics.
3. **Advanced Frontend Component:** A high-quality React or similar framework for the dashboard.

## External Components Optional
1. Deep Learning / Forecasting extensions (e.g., Temporal Fusion Transformers) - only if they outperform XGBoost.

## Components that should NOT be replaced
- The core data pipelines (JSON/CSV result structures).
- The XGBoost engine (unless a strictly better model is benchmarked).
- The Blender animation scripts.
- Adversarial and Monte Carlo robustness scripts.

## Integration Risks
- Complex mathematical differences between the existing simplistic SAANJH models and formal PyPSA/OpenDSS physics.
- Heavy computational overhead from external electrical grid solvers.

## License Risks
- MUST check all external repos. NREL is BSD-3 (compatible). PyPSA is MIT (compatible). Frontend must be MIT/Apache-2.0.

## Dependency Risks
- PyPSA/OpenDSS may introduce massive dependency trees. Must ensure it works in a clean environment.

## Final Recommended Architecture
1. **SAANJH Core Simulator** runs the time-series.
2. **NREL Aggregator Layer** handles the dispatch logic of virtual batteries.
3. **PyPSA Validator Layer** strictly validates the physical plausibility of the simulation independently.
4. **React/Next.js Dashboard** fetches the unified outputs.
