# Methodology notes

This file collects the design rationale, data provenance and third-party attribution that
were previously spread across a set of generated audit reports. It is plain prose and
contains no result numbers; all results live in `simulation/results/results.json` and are
rendered into the README and write-up by `scripts/render_results.py`.

## Why the control loop runs at the distribution transformer

Cloud-dispatched demand response depends on household internet links, and those links are
least reliable during exactly the evening events SAANJH is meant to handle (voltage sags
reboot home routers; mobile networks congest). SAANJH therefore places its dispatch logic
in a gateway at the distribution transformer (DT). The gateway can keep applying the last
approved plan and the local safety rules if the backhaul to the DISCOM or to the SAANJH
cloud is lost. The cloud side does forecasting, planning, measurement and verification,
and settlement, none of which are needed second-by-second.

The original prototype used RAKwireless WisBlock RAK4631 nodes (nRF52840 MCU, SX1262 LoRa
radio, 865–867 MHz licence-exempt band) at homes and a Raspberry Pi CM4 with an SX1262 HAT
as the gateway. The current design relies first on the smart meters already being installed
under RDSS for load limiting, and uses a LoRa relay node only at homes that offer inverter
flexibility. No hardware build is part of this submission.

## Fail-safe principle

Every SAANJH actuator fails toward normal supply. The inverter relay is normally closed, so
a dead node leaves the inverter on grid. A smart-meter load limit that cannot be refreshed
reverts to the meter's default sanctioned load. A gateway that loses its plan stops issuing
new limits rather than guessing.

## Data provenance (forecasting benchmark)

The UCI "Individual Household Electric Power Consumption" dataset (one household near
Paris, December 2006 onward, 1-minute resolution) was used to develop the original
load-forecasting pipeline. Source:
https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip
(SHA-256 of the downloaded archive:
`9f84b46ade8a2d8e1286ec4b2b6c2987a45a755c59f263be3b3b3d10dfbda3ff`). It is **not Indian
data**. It is kept only as a forecasting benchmark and is labelled as non-Indian wherever
it appears. Indian household behaviour is calibrated from Prayas eMARC published load
patterns; see `docs/DATA_SOURCES.md`.

## Electrical validation

Feeder voltages and line losses are computed with PyPSA's Newton–Raphson AC power flow on
a radial low-voltage feeder model. The model is a simplification (balanced three-phase
equivalent, lumped loads), and its assumptions are stated next to every result that uses it.

## Third-party components and licences

- **NREL Virtual Battery Aggregator** (BSD-3-Clause): the idea of summing power and energy
  envelopes across distributed batteries informed SAANJH's aggregation step. No NREL code
  is vendored; attribution is kept in the module docstring.
- **PyPSA** (MIT): used as an imported library for power-flow validation.
- **eDisGo** (AGPL-3.0): studied for its approach to LV voltage-limit checks. No code was
  copied.
- **XGBoost** (Apache-2.0), **scikit-learn** (BSD-3-Clause), **pandas** and **NumPy**
  (BSD-3-Clause), **FastAPI** (MIT): unmodified dependencies.

## Rollout stages (proposal)

1. One DT pilot over three months with a cooperating DISCOM sub-division: essential-band
   limiting through existing smart meters, a small community battery, and a handful of
   relay-equipped inverter homes.
2. A cluster of DTs on adjacent 11 kV feeders, integrating with the DISCOM's head-end and
   ADMS/DERMS through open protocols.
3. Sub-division scale, with flexibility reported toward the DISCOM's demand-flexibility
   obligation.
