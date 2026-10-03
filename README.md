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

## Year-long results: baseline vs SAANJH

Baseline is what DISCOMs do today during a supply shortfall: rotational shedding of whole
LT feeders. SAANJH applies, in order, flexibility (inverter relays, appliance deferral,
the community battery), then the essential band, and only then single-home
disconnection. Both policies see identical demand, weather and shortfalls.

<!-- results:annual:start -->
*SIMULATED on inputs CALIBRATED TO REAL DATA (see docs/DATA_SOURCES.md). Mean over 30 Monte Carlo seeds, 365 days at 15-minute resolution, weather for Lucknow 2023; P10–P90 across seeds in brackets.*

**Peri-urban low-income DT**: 250 homes on a 100 kVA DT (segment mix Low-income 70%, Middle 25%, Affluent 5%). Baseline calibrated to ESMI 'other municipal' locations: 27 shortfall outage minutes per evening (target 26.5), 39 per day (target 45.0).

| Metric | Baseline | SAANJH |
|---|---:|---:|
| Essential-supply availability in deficit windows | 59% (58%–60%) | 98% (97%–99%) |
| Outage hours per home per year (full disconnection) | 240.3 (213.5–269.7) | 10.8 (6.8–15.0) |
| Hours on essential band per home per year | 0.0 (0.0–0.0) | 1.2 (0.7–1.7) |
| Energy not served (kWh/year) | 11,457 (10,146–12,996) | 527 (327–763) |
| Energy curtailed above the band (kWh/year) | 0 (0–0) | 37 (22–52) |
| DT peak loading | 87% | 93% |
| Fairness of outage hours across homes (Gini, 0 = equal) | 0.00 | 0.02 |

| Essential-supply availability by segment | Baseline | SAANJH |
|---|---:|---:|
| Low-income | 56% | 98% |
| Middle | 65% | 98% |
| Affluent | 78% | 99% |

Household-hours of essential supply preserved per year: 52,164. Flexibility delivered per year: 1.2 MWh of demand flexibility (inverter relays 1.2 MWh, essential band 0.04 MWh, appliances 0.02 MWh) plus 7.0 MWh from the community battery (76 equivalent full cycles). Extra cycles on household inverter batteries (average over homes with an inverter): 31.8 per year.

**Mixed urban DT**: 200 homes on a 100 kVA DT (segment mix Low-income 40%, Middle 45%, Affluent 15%). Baseline calibrated to ESMI 'megacity' locations: 6 shortfall outage minutes per evening (target 6.0), 11 per day (target 10.5).

| Metric | Baseline | SAANJH |
|---|---:|---:|
| Essential-supply availability in deficit windows | 62% (60%–63%) | 100% (99%–100%) |
| Outage hours per home per year (full disconnection) | 78.0 (62.7–89.9) | 0.7 (0.1–1.4) |
| Hours on essential band per home per year | 0.0 (0.0–0.0) | 0.2 (0.0–0.5) |
| Energy not served (kWh/year) | 3,019 (2,498–3,487) | 36 (8–70) |
| Energy curtailed above the band (kWh/year) | 0 (0–0) | 7 (1–14) |
| DT peak loading | 83% | 92% |
| Fairness of outage hours across homes (Gini, 0 = equal) | 0.00 | 0.17 |

| Essential-supply availability by segment | Baseline | SAANJH |
|---|---:|---:|
| Low-income | 55% | 100% |
| Middle | 63% | 100% |
| Affluent | 77% | 100% |

Household-hours of essential supply preserved per year: 12,814. Flexibility delivered per year: 0.6 MWh of demand flexibility (inverter relays 0.5 MWh, essential band 0.01 MWh, appliances 0.03 MWh) plus 1.7 MWh from the community battery (19 equivalent full cycles). Extra cycles on household inverter batteries (average over homes with an inverter): 9.7 per year.
<!-- results:annual:end -->

![Essential-supply availability by segment](docs/figures/availability_by_segment.svg)

![A shortfall evening on the peri-urban DT](docs/figures/event_day_peri_urban_low_income.svg)

### Sensitivity

<!-- results:sensitivity:start -->
*SIMULATED. Each row changes one input; mean of 10 seeds. Availability = essential-supply availability in deficit windows.*

| Input | Value | Peri-urban low-income DT: baseline / SAANJH availability, SAANJH outage h | Mixed urban DT: baseline / SAANJH availability, SAANJH outage h |
|---|---|---:|---:|
| Essential band floor (W) | 300 | 59% / 99%, 8.3 h | 62% / 100%, 0.4 h |
| Essential band floor (W) | 500 | 59% / 98%, 10.6 h | 62% / 100%, 0.6 h |
| Essential band floor (W) | 1000 | 59% / 98%, 11.4 h | 62% / 100%, 0.7 h |
| Community battery (kWh) | 0 | 59% / 76%, 138.8 h | 62% / 82%, 33.2 h |
| Community battery (kWh) | 50 | 59% / 93%, 43.3 h | 62% / 97%, 5.6 h |
| Community battery (kWh) | 100 | 59% / 98%, 10.6 h | 62% / 100%, 0.6 h |
| Community battery (kWh) | 200 | 59% / 100%, 0.4 h | 62% / 100%, 0.0 h |
| Inverter owners enrolled | 0.0 | 59% / 97%, 14.5 h | 62% / 99%, 1.5 h |
| Inverter owners enrolled | 0.6 | 59% / 98%, 10.6 h | 62% / 100%, 0.6 h |
| Inverter owners enrolled | 1.0 | 59% / 98%, 8.8 h | 62% / 100%, 0.3 h |
| Segment mix | base | 59% / 98%, 10.6 h | 62% / 100%, 0.6 h |
| Segment mix | more affluent | 60% / 98%, 12.3 h | 64% / 99%, 1.1 h |
| Share of outages caused by shortfall | 0.3 | 60% / 99%, 3.7 h | 61% / 100%, 0.3 h |
| Share of outages caused by shortfall | 0.5 | 59% / 98%, 10.6 h | 62% / 100%, 0.6 h |
| Share of outages caused by shortfall | 0.7 | 59% / 97%, 25.6 h | 62% / 100%, 0.8 h |
| Shortfall depth | 15-45% | 59% / 98%, 10.6 h | 62% / 100%, 0.6 h |
| Shortfall depth | 25-60% | 46% / 94%, 37.0 h | 50% / 98%, 4.1 h |
<!-- results:sensitivity:end -->

![Sensitivity of essential-supply availability](docs/figures/sensitivity.svg)

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
python simulation/feeder_sim.py   # evening peak case
python simulation/run_year.py     # year-long Monte Carlo (about 20 min on 30 cores)
python scripts/make_figures.py
python scripts/render_results.py  # refreshes the tables above
pytest
```
