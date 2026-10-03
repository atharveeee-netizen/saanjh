# SAANJH project brief (source of truth for all work in this repo)

## The hackathon
Schneider Electric Yuva Yodha 2026, track "Grid Reliability & Renewable Intermittency".
The solution must:
- keep electricity dependable when renewable supply falls below demand,
- be deployable and operable at neighbourhood / distribution-transformer level,
- be genuinely affordable for low-income urban and peri-urban communities,
- give the DISCOM data, forecasts or demand-response signals.
Required deliverables: solution write-up, architecture diagram (energy, data and money
flows), design artefacts (UX, service design, data/model design), optional software
prototype, a measurable reliability improvement against a defined baseline (outage hours
or supply availability during intermittency windows), and an ownership / O&M model with
unit economics for low-income communities. No hardware build is expected.

## What SAANJH is
An essential-supply layer for a distribution transformer (DT). During renewable-deficit
windows, every home on the DT keeps its essential loads (lights, fans, fridge, phone
charging) running, instead of the whole feeder being load-shed. It combines:
1. Essential-band load limiting through the smart meters DISCOMs are already installing
   (cap each home at a configurable essential power band instead of disconnecting it).
2. A shared community battery at the DT (second-life EV packs) for homes that own no storage.
3. Flexibility from homes that can offer it: inverter batteries (via a relay on the
   inverter's mains input that puts the inverter in backup mode) and deferrable appliances
   (only where an actuator such as a smart plug or contactor is installed).
4. A probabilistic deficit forecast that tells the operator when to pre-charge the
   community battery and when to schedule flexibility.
5. DISCOM-facing signals and reports, using open protocols (IEEE 2030.5 / OpenADR style),
   with flexibility counted toward the DISCOM's Demand Flexibility Portfolio Obligation.

## Facts we rely on (from 2026 research; cite these, never inflate them)
- Maharashtra (2024), Karnataka (Oct 2025) and Rajasthan (Feb 2026) have demand-flexibility
  obligations on DISCOMs. Maharashtra's initial target is 1.5% of peak load; Rajasthan's is
  0.25%. Rajasthan's draft regulations create an aggregator registration route and mandate
  open protocols such as OpenADR, IEEE 2030.5 and OCPP.
- Existing Indian DR pilots target affluent loads: JVVNL Jaipur raises AC setpoints by 1 °C
  for ~2,000 homes (~1 MW expected); BSES Yamuna's automated DR cut participating homes'
  peak demand by 17–20%. SAANJH is different: it protects essential supply for everyone.
- As of 30 June 2026, ~5.53 crore consumer smart meters and ~18.5 lakh DT meters were
  installed under RDSS (7.24 crore smart meters in total nationally). Time-of-Day tariffs
  apply once a consumer has a smart meter (solar hours 10–20% cheaper, peak 10–20% dearer).
- Load limiting instead of blackouts has precedent: Eskom (South Africa) limits smart-meter
  customers from 60 A to 10 A instead of early-stage load shedding; a 2026 Northwestern /
  NBER line of work argues power limits beat rolling blackouts on welfare.
- Inverter ownership is low: an IIT Madras study of six states found only 4–5% of
  households own inverters, concentrated among affluent households. Urban ownership is
  higher but nowhere near 70%. Never claim 70%.
- Typical Indian household load (Prayas eMARC smart-meter data): night 100–150 W, evening
  peak around 9 pm of 200–250 W per household in non-summer months; AC-owning homes about
  600 W and water-heater homes about 500 W at their peaks.
- Real outage data: Prayas ESMI provides minute-wise voltage data for a few hundred
  locations across India (watchyourpower.org, Harvard Dataverse). Treat voltage < 130 V
  as an outage minute.
- Time-series foundation models (Chronos-2, Moirai-2, TimesFM) forecast zero-shot. A Feb
  2026 benchmark found the best reach ~47% lower error than seasonal-naive day-ahead, and
  Chronos-2 gave well-calibrated prediction intervals.
- Second-life EV batteries are commercial in India (e.g. Lohum, Nunam). Treat cost as a
  range (assume 40–70% of new LFP pack cost) and run sensitivity on it.

## Reference URLs
- https://www.deccanherald.com/amp/story/opinion/a-future-in-flexible-power-4073955
- https://www.business-standard.com/industry/news/jaipur-discom-first-in-india-to-deploy-adr-for-household-peak-load-control-126062200689_1.html
- https://resolven.com/blog/virtual-power-plants-explained
- https://kashmirlife.net/jammu-kashmir-installs-9-71-lakh-smart-meters-under-rdss-64-8-per-cent-of-sanctioned-target-centre-445114/
- https://www.eskom.co.za/distribution/wp-content/uploads/2024/01/20240129-SMART-METER-BROCHURE-rev2.pdf
- https://www.ipr.northwestern.edu/documents/working-papers/2026/wp-26-07.pdf
- https://sciforum.net/paper/30778
- https://energy.prayaspune.org/electricity-load-patterns
- https://energy.prayaspune.org/our-work/article-and-blog/esmi-in-uttar-pradesh
- https://arxiv.org/abs/2602.10848
- https://wri-india.org/perspectives/second-charge-unlocking-second-life-potential-ev-batteries
- https://rmi.org/insight/envisioning-a-national-grid-flexibility-programme-for-india

## Ground rules for every change
1. Never invent data or results. Every number shown in the README, write-up or UI must be
   produced by code in this repo and read from a results file. No hardcoded result numbers
   in docs or UI.
2. Label everything as REAL DATA, CALIBRATED TO REAL DATA, or SIMULATED.
3. Physical sanity always holds: delivered battery power never exceeds the sum of inverter
   ratings; energy is conserved (discharge, recharge and losses all accounted for);
   recharging adds load to the feeder; deferred load comes back later (rebound).
4. Round displayed numbers to sensible precision (kW to 1 decimal, % to whole numbers).
5. Keep changes small and reviewable. Run tests after each change. Summarise what changed.
6. If something can't be done (no internet, missing package), say so, implement a clearly
   labelled fallback, and leave a TODO. Never silently fake it.
