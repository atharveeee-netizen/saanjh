# SAANJH

An essential-supply layer for a distribution transformer. During renewable-deficit
windows, SAANJH aims to keep every home's essential loads running instead of
load-shedding the whole feeder. Built for the Schneider Electric Yuva Yodha 2026
hackathon, track "Grid Reliability & Renewable Intermittency".

> Work in progress. The project is being rebuilt step by step from
> `docs/PROJECT_BRIEF.md`. Every number on this page is generated from
> `simulation/results/results.json` by `scripts/render_results.py`. `archive/` holds the
> earlier Blender renders, demo videos and video scripts, which are not part of the core
> submission.

## Evening peak case (accounting-corrected)

This is the original prototype's 60-home evening case, re-run after fixing how
flexibility is counted. It now counts only what batteries and appliances physically
deliver, and it adds battery recharge and appliance rebound back onto the feeder.

<!-- results:evening_peak:start -->
*SIMULATED. Scenario `evening_peak_legacy`: 60 homes on a 100 kVA DT, one day, seed 42. Forecast: one-step-ahead XGBoost trained on UCI (non-Indian) household data.*

| Metric | Baseline | SAANJH | Change |
|---|---:|---:|---:|
| Peak DT load (kW) | 151.5 | 141.2 | −10.3 |
| Peak DT loading | 160% | 149% | −11 pts |
| Time above DT rating (min) | 90 | 90 | ±0.0 |
| Energy above DT rating (kWh) | 45.0 | 36.4 | −8.6 |
| Minimum tail-end voltage (V) | 209.1 | 210.6 | +1.6 |
| Time below 216.2 V (min) | 75 | 75 | ±0.0 |

| Flexibility ledger | Value |
|---|---:|
| Flexibility requested (kWh) | 70.8 |
| Flexibility delivered (kWh) | 19.7 |
| … from inverter batteries (kWh) | 8.6 |
| … from deferred appliances (kWh) | 8.9 |
| … from AC setpoint raise (kWh) | 2.2 |
| Rebound added back later (kWh) | 10.0 |
| Battery recharge added back (kWh) | 10.7 |
| Battery conversion losses (kWh) | 2.1 |
| Peak battery output / sum of inverter ratings (kW) | 6.1 / 9.1 |
| Homes with inverter / with actuator / opted out | 13 / 11 / 1 |
<!-- results:evening_peak:end -->

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows; use `source .venv/bin/activate` elsewhere
pip install -r requirements.txt
python simulation/feeder_sim.py   # writes simulation/results/results.json
python scripts/render_results.py  # refreshes the tables above
pytest
```
