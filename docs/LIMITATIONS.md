# Limitations and honest claims

SAANJH makes a strong claim: that a distribution transformer can keep essentials
on during a supply shortfall without shedding the whole feeder. This document
states exactly how far the evidence goes, so reviewers do not have to discover
the gaps themselves.

The one-line version: **the physics and control logic are tested; the household
response, the feeder and the hardware at scale are modelled or logic-tested, not
field-proven.**

## Evidence status

| Claim | Status | Where the evidence is |
|---|---|---|
| Essential-supply availability improves from 59% to 98% on a peri-urban low-income DT | **SIMULATED**, calibrated inputs | `simulation/results/results.json`, 30 seeds |
| Outage hours fall from 240 to 10.8 per home per year | **SIMULATED**, same run | same |
| The 70% reserve is enforced at the node and the gateway | **TESTED** — 34 native C++ tests + Python safety tests | `firmware/rak4631_node/test/`, `tests/test_gateway_safety.py` |
| A three-node LoRa control path delivers telemetry and commands with ~2% loss | **SEEDED REPLAY**, not radio measurements | `gateway/data/replay_summary.json` |
| The relay returns the load to grid on reset, fault, opt-out or expiry | **TESTED in logic**, **not yet bench-validated** | `src/node_controller.cpp`, `docs/HARDWARE.md` checklist |
| Indian weather and load shapes are realistic | **CALIBRATED to NASA POWER and Prayas eMARC/ESMI** | `simulation/results/calibration.json` |
| The economics are investable | **INDICATIVE**, simple payback, not NPV or a tariff filing | `simulation/results/low_income.json` |

There is **no live hardware evidence committed yet**. The dashboard labels the
gateway tab "replay" whenever `live_summary.json` is absent, and the replay
summary itself says its latency and loss are seeded draws.

## Simulation limits

* **One lumped feeder.** The power flow is a balanced LT feeder with a single
  transformer. It does not model per-phase imbalance, voltage unbalance,
  conductor temperature or protection coordination.
* **Synthetic households.** Appliances, ownership and behaviour come from a
  parameterised fleet, not from metered homes. The segment split below
  "middle" is an assumption.
* **Outage calibration is aggregate.** Prayas ESMI gives category averages, not
  a per-location distribution. The share of outages caused by supply shortfall
  rather than faults is assumed at 0.5 and varied in sensitivity runs.
* **Weather is reanalysis.** NASA POWER is a ~50 km grid, not a rooftop sensor.
  Hourly values are held flat within the hour.
* **Forecast skill is modest.** The best model beats seasonal naive only
  narrowly (MASE 0.99 vs 1.02 on the peri-urban DT; 0.83 vs 1.01 on the mixed
  urban DT). The 80% P10–P90 interval covers only 68–69% of realised days, so
  the intervals are too narrow. The dispatch results are therefore a test of
  the mechanism, not proof that the forecast is production-grade.
* **The annual `results.json` is deliberately frozen.** New analyses are
  separate bundles, so the headline cannot drift silently. Regenerating it
  requires `simulation/run_year.py` and the 30-seed run.
* **Monte Carlo seed counts differ by analysis.** The annual run uses 30 seeds;
  the faster analysis bundles use fewer. Every JSON records its own seed count.

## The energy-balance correction

The legacy 45-minute claim was **42.19 kWh** of delivered energy. The audited
reconciliation in `energy_balance.json` finds:

| Component | kWh |
|---|---:|
| Battery | 4.53 |
| Deferred appliances | 2.69 |
| **Delivered** | **7.22** |
| Unmet | 34.97 |
| **Total** | **42.19** |

So the legacy case delivers **17.1% of its own headline**, not 100%. The
identity holds (`battery + deferred + unmet = claim`), which is why the number
is trustworthy as an audit rather than a new claim. The annual simulation does
**not** depend on the legacy number; it computes availability from the fleet.

The fleet reality check is equally blunt: the legacy case needs about 81
inverter homes at 0.7 kW each to meet the power claim, but the fleet has 13.
The shortfall has to come from deferred appliances and a community battery,
which the legacy case did not model.

## Low-income economics

* **Simple payback, not NPV.** Payback is capex divided by annual DISCOM cash
  (energy sales plus DFPO). It ignores discount rates, tariff escalation,
  battery degradation and replacement.
* **The DFPO value is a policy assumption**, not an observed market price.
* **VoLL is reported separately.** The societal value of avoided outage uses a
  value-of-lost-load assumption; it is not DISCOM cash and is not counted in
  payback.
* **The shared battery dominates capex.** At 100% adoption the best case is
  about ₹6,980 per home and 11 years' simple payback on DISCOM cash. Relays
  alone cannot carry the evening; the storage is the cost.
* **No subsidy, financing or collection-risk model.** A real DISCOM business
  case would need all three.

## Overload and robustness

* Overload "success" is defined by essential-supply availability and unserved
  energy, not thermal peak alone. A case can pass a thermal limit while leaving
  most demand unserved; the analysis reports both.
* Packet loss is modelled as independent per node and per block. Real LoRa
  fading is bursty and correlated, so the 5% and 20% cases are optimistic about
  consecutive losses.
* Node dropout is modelled as a fraction of nodes offline per block. It does
  not model a node that is receiving but cannot transmit, or a stuck relay.
* The smart-meter essential band is assumed to survive a radio outage. That is
  a meter function, not a SAANJH function; if the meter loses its profile, the
  floor is not guaranteed.
* A relay node that misses a command leaves its inverter on grid (normally
  closed). The failure mode is lost flexibility, not a safety hazard.

## Hardware limits

* **≤12 V DC only.** The prototype does not switch mains, does not measure a
  real service entrance and has no certified isolation.
* **Three nodes.** LoRa P2P is deliberate at this scale. A real deployment
  needs an SX130x concentrator, a network server and duty-cycle management.
* **SoC is estimated**, from an OCV table plus INA226 coulomb counting. It is
  not a certified BMS and drifts if the pack is not rested periodically.
* **No temperature sensing.** Telemetry carries a placeholder 25 °C and leaves
  `R_TEMP_VALID` clear. Thermal protection is the pack BMS, not SAANJH.
* **One relay, one dummy load.** This is a control-path demonstrator, not a
  whole-home transfer switch.
* **No enclosure ingress protection, surge protection or EMI testing.** It is a
  bench unit, not an installable product.
* **The RAK4631 radio is not frequency-hopping.** It uses a single 25 kHz
  channel at 865.0625 MHz inside the Indian 865–867 MHz ISM band.

## Communications and security

* The frame format has a CRC but **no authentication or encryption**. Anyone
  with a matching radio and sync word can inject a well-formed command. The
  node's reserve and opt-out checks still apply, but a production system needs
  authenticated commands and replay protection.
* The gateway trusts its serial/SPI link. There is no secure boot, no signed
  firmware and no key management.
* Logs contain node IDs, SoC and load, not personal data. A production system
  would still need a privacy notice and a retention policy.
* No penetration test, threat model review or red-team exercise has been done.

## Regulatory and commercial

* The 865–867 MHz band is used at 14 dBm with a duty cycle far below the
  exemption limits for the demo, but the deployment as a whole has not been
  type-approved.
* No DISCOM approval, no metering certification, no grid-code compliance and
  no electrical inspectorate sign-off.
* The prototype is not a substitute for a licensed installer. Mains work,
  inverter installation and service-entrance transfer require a certified
  product and a licensed electrician.

## What would change the conclusions

1. **Field data from 20–50 homes** on load shapes, inverter availability and
   willingness to opt in. This is the single largest uncertainty.
2. **A measured feeder** with per-phase voltages and protection settings,
   rather than a lumped model.
3. **A bench run with the actual RAK4631 nodes and CM4 HAT**, filling the
   evidence table in `HARDWARE.md`, including RSSI/SNR and relay timing.
4. **A tariff and subsidy model** from the relevant DISCOM, plus battery
   degradation and replacement costs.
5. **A security review** with authenticated frames and a key-management plan.

Until then, the honest claim is: **the control logic and safety interlocks are
tested, the system-level benefit is modelled with calibrated inputs, and the
hardware is a bench prototype awaiting live evidence.**
