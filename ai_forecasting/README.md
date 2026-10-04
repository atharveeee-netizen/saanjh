# Forecasting

## What is forecast

For each 15-minute block of the next day (96 blocks, issued at midnight), the gateway
forecasts the DT's **unmanaged net demand** (household demand minus rooftop PV) as
quantiles P10, P50 and P90. It then turns that into a **deficit forecast**: how much of
that demand is likely to be cut by a supply shortfall. The shortfall part uses the
statistical shortfall model (event rate rising with demand stress and cloudiness,
ESMI-based durations). The forecaster knows those rates but not the random draws, as a
day-ahead adequacy assessment would.

The forecast drives one operating decision: **how much community-battery energy to keep
in reserve for deficits** while the battery shaves the DT's evening peak (18:00–22:00)
on normal days.

## Models

| Model | Type |
|---|---|
| Seasonal naive | Yesterday's profile; P10/P90 from the last seven days at the same block |
| Weekly naive | Same weekday last week (point forecast) |
| XGBoost quantile | Gradient-boosted quantile regression on calendar, weather and lag features; retrained every 30 days on all earlier days, so test days are never in its training data |
| Chronos-2 | Amazon's time-series foundation model, zero-shot, with temperature and solar availability as covariates |

Everything runs on CPU. The UCI single-household XGBoost model in
`artifacts/models/` (trained by `train_real_model.py` on French data) is kept only as
the one-step forecaster of the legacy evening case and as a methodology benchmark.

## Accuracy (rolling origin)

<!-- results:forecast_accuracy:start -->
*Forecasts of SIMULATED DT demand on REAL weather (see ai_forecasting/README.md). Day-ahead, 96 blocks, issued at midnight; test days 28–364 of seed 0. MASE below 1 beats yesterday's profile. Chronos: amazon/chronos-2 (zero-shot).*

**Peri-urban low-income DT**

| Model | MASE | MAE (kW) | Pinball loss (kW) | P10–P90 coverage |
|---|---:|---:|---:|---:|
| Seasonal naive | 1.02 | 1.2 | 0.48 | 53% |
| Weekly naive | 1.91 | 2.2 | 1.11 | – |
| XGBoost quantile | 1.55 | 1.8 | 0.65 | 69% |
| Chronos-2 (zero-shot) | 0.99 | 1.2 | 0.42 | 68% |

| Evening deficit-energy forecast from | P10–P90 coverage | Days above P90 | Mean P90 (kWh) | Mean realised (kWh) |
|---|---:|---:|---:|---:|
| Seasonal naive | 88% | 12% | 60.0 | 22.9 |
| XGBoost quantile | 84% | 16% | 53.8 | 22.9 |
| Chronos-2 (zero-shot) | 87% | 13% | 57.8 | 22.9 |

**Mixed urban DT**

| Model | MASE | MAE (kW) | Pinball loss (kW) | P10–P90 coverage |
|---|---:|---:|---:|---:|
| Seasonal naive | 1.01 | 1.6 | 0.60 | 53% |
| Weekly naive | 1.60 | 2.5 | 1.26 | – |
| XGBoost quantile | 1.38 | 2.2 | 0.74 | 69% |
| Chronos-2 (zero-shot) | 0.83 | 1.3 | 0.45 | 69% |

| Evening deficit-energy forecast from | P10–P90 coverage | Days above P90 | Mean P90 (kWh) | Mean realised (kWh) |
|---|---:|---:|---:|---:|
| Seasonal naive | 91% | 9% | 12.6 | 4.7 |
| XGBoost quantile | 90% | 10% | 9.5 | 4.7 |
| Chronos-2 (zero-shot) | 91% | 9% | 10.9 | 4.7 |
<!-- results:forecast_accuracy:end -->

## Decision value

<!-- results:forecast_decision:start -->
*SIMULATED. Year-long SAANJH runs, mean of 3 seeds. The community battery shaves the 18:00–22:00 peak but keeps a deficit reserve set by each policy.*

| Reserve policy | Peri-urban low-income DT: availability / outage h / peak shaved (MWh) | Mixed urban DT: availability / outage h / peak shaved (MWh) |
|---|---:|---:|
| full reserve (no peak shaving) | 98.6% / 8.3 h / 0.0 | 99.7% / 0.7 h / 0.0 |
| fixed 25% reserve (no forecast) | 94.3% / 33.5 h / 15.8 | 97.2% / 5.5 h / 18.2 |
| fixed 50% reserve (no forecast) | 96.9% / 18.4 h / 9.6 | 98.8% / 2.3 h / 11.3 |
| fixed 75% reserve (no forecast) | 98.1% / 11.2 h / 3.7 | 99.4% / 1.1 h / 4.5 |
| Seasonal naive P90 reserve | 98.4% / 9.6 h / 3.9 | 96.0% / 7.7 h / 19.3 |
| Seasonal naive P97 reserve | 98.6% / 8.4 h / 1.1 | 99.1% / 1.7 h / 9.1 |
| Seasonal naive P99.5 reserve | 98.6% / 8.3 h / 0.2 | 99.6% / 0.7 h / 2.2 |
| XGBoost quantile P90 reserve | 98.1% / 11.1 h / 5.2 | 95.4% / 9.0 h / 20.4 |
| XGBoost quantile P97 reserve | 98.5% / 8.6 h / 1.7 | 98.8% / 2.3 h / 10.6 |
| XGBoost quantile P99.5 reserve | 98.6% / 8.4 h / 0.4 | 99.6% / 0.7 h / 3.0 |
| Chronos-2 (zero-shot) P90 reserve | 98.3% / 9.8 h / 4.4 | 95.6% / 8.4 h / 19.8 |
| Chronos-2 (zero-shot) P97 reserve | 98.6% / 8.4 h / 1.3 | 99.1% / 1.7 h / 9.7 |
| Chronos-2 (zero-shot) P99.5 reserve | 98.6% / 8.3 h / 0.3 | 99.6% / 0.8 h / 2.5 |
<!-- results:forecast_decision:end -->

## Limitations

- The demand series is simulated from the calibrated household model, not metered DT
  data. Real DT meter data would be noisier.
- Observed weather (NASA POWER) stands in for a day-ahead weather forecast, which
  flatters every model that uses weather covariates equally.
- The shortfall model is the same one that generates shortfalls in the simulation, so
  the deficit forecast is well specified by construction. A real SLDC adequacy forecast
  would be less well matched.

Run: `python ai_forecasting/evaluate.py` (about 25 minutes on CPU with Chronos-2).
