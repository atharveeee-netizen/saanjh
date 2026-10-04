# Review findings (hostile-reviewer pass)

Read as a senior distribution engineer judging the submission and looking for flaws.
Nothing here has been fixed yet; each finding has a suggested fix. Ranked critical,
major, minor.

## Critical

**C1. The headline rests on the community battery, not the essential band.**
The sensitivity table shows that without the battery SAANJH reaches 76% (peri-urban) and
82% (mixed urban) essential-supply availability, not 98–100%. On a low-income DT most
homes already draw less than 500 W in the evening, so the band has little to cut. A
reviewer will say the "essential band" story is under-evidenced and the result is really
"a 100 kWh battery on a DT".
*Fix:* lead the pitch with the battery-plus-band combination. Show a band-only variant
with a lower floor (for example a 150–250 W "lifeline" band) as its own sensitivity row.
Say plainly that low-income DTs need storage.

**C2. Affordability is not yet shown from the DISCOM's side.**
DISCOM NPV is about −Rs 24 lakh per DT over 10 years. Spread across the DT, the net cost
is roughly Rs 100–140 per home per month, which is a large share of a low-income home's
electricity bill. Low-income homes pay nothing directly, but someone does.
*Fix:* state who pays (ARR pass-through, DFPO budget, state scheme). Compare with the
cost of the same reliability from a utility BESS or from extra power purchase. Show the
smaller-battery and cheaper second-life cases (tornado) as the realistic path.

**C3. Supply allocation is set from the DT's actual demand.**
`simulation/deficit.py` sets the allocation as (1 − cut) × the DT's realised unmanaged
demand. A real SLDC or DISCOM cannot know that in advance, so SAANJH gets an unusually
precise target.
*Fix:* set the allocation from the forecast (P50) demand, or as a fixed MW cap per DT
for the event. Re-run the year.

## Major

**M1. The forecast's decision value is partly built in.** The deficit forecast uses the
same shortfall model that generates shortfalls, and observed weather stands in for a
weather forecast. *Fix:* use forecast weather (or add noise to it), and give the
forecaster a shortfall model with mis-specified rates.

**M2. Forecast intervals under-cover.** Demand P10–P90 bands contain the actual value
only 68–69% of the time against 80% nominal. XGBoost does worse than yesterday's
profile (MASE 1.4–1.6). *Fix:* add conformal calibration of the intervals; report it.

**M3. Battery charging creates new DT peaks.** On the featured replay day the DT's
highest load of the day (about 65 kW) comes from the community battery and inverters
recharging after a morning shortfall, not from the evening. Peak DT loading rises from
87% to 93% over the year. *Fix:* shape charging (power limit as a function of DT
headroom, spread across solar hours) and report charging-induced peaks.

**M4. Essential availability counts every banded home as "essential on".** The metric
does not check that a banded home's own critical load (lights, fans, fridge) fits within
its band. *Fix:* add a test that critical load ≤ band for every banded home and block,
and count exceptions as not essential.

**M5. Demo values in the UI that do not come from results.** The battery temperature,
inspection dates, complaint count and household credits on the status page are marked
"example". The monthly summary message ("185 minutes", "Rs 64") is not marked.
*Fix:* compute them from the household's results or label them as examples.

**M6. Baseline calibration falls short of the daily target.** The baseline matches ESMI
evening outage minutes but reaches only 39 daily minutes against 45 (peri-urban). The
share of outages caused by supply shortfall (50%) is an assumption. *Fix:* download
the minute-wise ESMI data (needs the Dataverse form) and calibrate per location.

**M7. Feeder model is simplified.** Voltages come from a lumped, balanced feeder; phase
imbalance and the distribution of homes along the line are not modelled. *Fix:* build a
radial four-feeder model with per-phase loads in PyPSA or pandapower.

**M9. The FUXA SCADA page reads the old results.** `frontend/saanjh_fuxa_adapter.py` and `build_fuxa_frontend.py` read `simulation/data/results/comparison.json`, which held the pre-correction numbers and no longer exists. The generated page (`docs/index.html`) and its test hard-coded those numbers, so both were removed in the merge. *Fix:* point the adapter at `simulation/results/results.json` and `backend/data/`, then regenerate the page.

**M8. Single-home disconnection and load limiting assume capabilities.** These assume
every RDSS meter has a working load switch and the head-end can act within 15 minutes.
*Fix:* cite the meter specification (IS 16444) and head-end latency, or keep shedding
at LT-feeder level as a fallback.

## Minor

- **m1.** Hindi and Marathi text is machine translation (marked in the UI); it needs a
  native speaker's review.
- **m2.** No privacy notice or data-retention policy under the DPDP Act, although the
  blueprint describes consent capture. Add a one-page note.
- **m3.** No licence file.
- **m4.** The hosted page cannot print or download, so the report has a print stylesheet
  but no print button, and the household table copies CSV instead of downloading.
- **m5.** The legacy one-day evening case (`simulation/feeder_sim.py`) still uses the
  UCI-trained one-step model and the uncalibrated 60-home configuration. It is kept only
  to show the accounting fix; consider moving it to `archive/`.
- **m6.** Running the full Chronos-2 evaluation needs `chronos-forecasting` and PyTorch,
  which are listed separately in `requirements-forecast.txt`.
- **m7.** The community-battery fire safety, siting and insurance are costed as one line
  item, with no siting rules.

## Checks that passed

- Every number in the README, write-up, ownership model and forecasting README is
  rendered from `simulation/results/results.json` (`tests/test_results_consistency.py`).
- **Physical sanity:**
  - battery output never exceeds the sum of inverter ratings;
  - battery SOC stays within its bounds, and inverter relays never go below the 70%
    reserve;
  - energy balances in every block;
  - recharge and rebound are added back to the feeder;
  - transformer loading uses the power factor.

  (`tests/test_physics.py`, `tests/test_mechanisms.py`)
- Both policies see identical inputs in every run.
- Household compensation covers battery wear and charging losses; payback is computed,
  not hardcoded (`tests/test_economics.py`).
- API endpoints and the console's approval flow are tested (`tests/test_api.py`,
  `ui/e2e/`).
