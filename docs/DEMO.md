# Demo guide — five minutes, no surprises

Two demo modes:

* **Replay demo (safe default).** No radio, no battery, fully reproducible. It
  proves the codec, dispatcher, reserve rule, logging and dashboard.
* **Live demo (stretch).** Three RAK4631 nodes and the CM4 + SX1262 HAT. It
  proves the radio path and the relay, and fills the evidence table in
  `HARDWARE.md`.

If the hardware does not cooperate, switch to replay without apologising. The
replay evidence is clearly labelled and is still end-to-end through the packet
codec.

## Recording setup

Target **1920×1080, 30 fps, one take**. The video should feel like a working
demo, not a slide deck.

* Run the dashboard at 100% browser zoom, full screen, with bookmarks hidden.
* Put the terminal on a second desktop or behind the browser. Use a large font
  (18 pt or more) and a dark background; the native-test output must be readable
  at 1080p.
* Open the architecture SVG in a third tab before recording so there is no
  waiting on load.
* Record a ten-second test and play it back. If the KPI text is not readable on
  a phone, it will not be readable for a reviewer either.
* Run the replay immediately before recording. If a number is stale, stop and
  rerun it rather than editing the video.
* Say the words **"simulated"** and **"replay evidence"** out loud. Never let a
  replay look like a field measurement.

Reset the evidence between takes:

```bash
python -m gateway.service --mode replay --nodes 3 --hours 6 \
  --duration-min 45 --packet-loss 0.02
```

Then refresh the dashboard and confirm the badge is **🟡 Replay evidence**.

## Shot list

| Time | Screen | Action |
|---|---|---|
| 0:00–0:40 | Dashboard tab 1 | Headline row: 59% → 98%, 240 → 10.8 h |
| 0:40–1:30 | Architecture SVG | Three layers and the fail-safe relay |
| 1:30–2:30 | Tabs 1 and 2 | Reliability scorecard, then the energy correction |
| 2:30–3:15 | Tab 3 | The three low-income routes and payback |
| 3:15–4:00 | Tabs 4 and 5 | Packet loss, node dropout, Indian calibration |
| 4:00–4:40 | Tab 6 + terminal | Replay badge, then 34 native tests |
| 4:40–5:00 | Tab 1 or `LIMITATIONS.md` | Bench gap and the next step |

Dashboard screenshots for the edit are in `docs/figures/dashboard/`. The
architecture diagrams are `docs/architecture/system_architecture.svg` and
`docs/architecture/deficit_event_sequence.svg`. Design mockups for the operator,
household and field-app screens are in `docs/figures/ui_*.png`.

Regenerate the tab screenshots after a UI change:

```bash
pip install playwright
python scripts/capture_dashboard.py --url http://localhost:8501
```

## Pre-flight (10 minutes before)

```bash
# from the repository root, with the venv active
python scripts/run_all.py --quick
streamlit run dashboard/app.py
```

`run_all.py --quick` validates contracts, regenerates the replay, re-validates,
checks docs against `results.json` and runs the test suite. It must end with
`All requested stages completed.`

Open the dashboard at <http://localhost:8501>. Confirm:

* the badge says **🟡 Replay evidence** (or 🟢 live if the hardware is attached);
* the sidebar shows **70% SoC**, **0 reserve breaches** and packet success near
  98%;
* all seven tabs render without an exception.

Have a second terminal ready for the firmware tests. If hardware is attached,
keep a third for the serial monitor.

## The five-minute script

### 0:00–0:40 — the problem

> "When a feeder is short of power, the DISCOM switches off the whole feeder.
> Every home loses lights, fans, the fridge and phone charging, even though the
> shortfall is often a few hundred kilowatts on a transformer that could ride
> through it. SAANJH keeps the essentials on and moves the heavy loads instead."

Show the headline row in the dashboard: **59% → 98% essential availability**,
**240 → 10.8 outage hours per home per year**.

### 0:40–1:30 — how it works

Show the architecture diagram in `docs/architecture/system_architecture.svg`.

> "Three layers. The smart meter enforces an essential band. The gateway
> forecast decides how much flexibility the transformer needs this evening. The
> nodes are the last layer: a relay, a current sensor and a 70% reserve that the
> node enforces itself, even if the gateway asks for more."

### 1:30–2:30 — reliability and energy honesty

Dashboard tab **1 · Reliability**: point at the scorecard and the fairness row.

> "Essential availability is the primary metric, not transformer temperature.
> We also report unserved energy and fairness, because a feeder can be
> thermally fine while most homes are still dark."

Dashboard tab **2 · Energy balance**.

> "This is the correction we are proudest of. The old 45-minute claim was 42.19
> kWh. The audited build delivers 7.22 kWh: 4.53 from batteries, 2.69 from
> deferred appliances, 34.97 unmet. The identity holds, and we say so. The
> annual result does not depend on the old number."

### 2:30–3:15 — low-income economics

Dashboard tab **3 · Low-income economics**.

> "A low-income home cannot buy a 5 kWh wall battery. The three routes are the
> inverter battery a home already owns, a shared community battery, and the
> combined fleet. The shared battery is the one that reaches 99% availability,
> at about ₹6,980 per home and 11 years' simple payback on DISCOM cash. That is
> indicative, not a tariff filing."

### 3:15–4:00 — robustness

Dashboard tabs **4 · Overload & robustness** and **5 · India calibration**.

> "At 20% packet loss the control path still delivers about 80% of relay
> commands, and essential availability only moves from 98.6% to 98.4%, because
> the meter band survives a radio outage. Combine that with node dropout and it
> is still 98.0%. We also show the case where a node drops out: the relay fails
> to grid, so the failure is lost flexibility, not a safety hazard. Weather is
> NASA POWER Lucknow 2023; load shapes are calibrated to Prayas eMARC; outages
> to Prayas ESMI."

### 4:00–5:00 — the control path and the gap

Dashboard tab **6 · HIL gateway**, then a terminal.

> "We built the node firmware and the CM4 gateway, but the physical bench is
> not assembled yet. What is tested is the control path: the packet codec, the
> exact 70% reserve, push-button opt-out, command expiry and the fail-safe relay
> return. Thirty-four native tests cover those, and all three node images link.
> The gateway tab you are looking at is a seeded replay, not a radio
> measurement. We label it that way. The next step is the bench, then 20–50
> homes on a measured feeder."

Show the replay badge explicitly. Then run:

```bash
cd firmware/rak4631_node
pio test -e native
```

Point at `34 Tests 0 Failures` and the three build sizes (5.8% RAM, 14.9%
flash). If hardware is attached, use the live insert below instead.

> "In the live build this is the physical loop: three RAK4631 nodes, a 12 V
> dummy load, a relay that moves the load between a 12 V grid adapter and a
> battery, and a CM4 gateway with an SX1262 HAT. Telemetry every 10 seconds,
> commands acknowledged, and the node refuses below 70% SoC or when the
> household presses opt-out."

If live hardware is attached, show the serial monitor and the relay click. If
not, do not imply it is connected. Say plainly:

> "The committed evidence is a seeded replay, not a radio measurement. The
> firmware builds and 34 native tests cover the protocol, reserve and battery
> model. The bench validation table is in `docs/HARDWARE.md`; we are not
> claiming live numbers we do not have."

Close on the limitation:

> "The physics and control logic are tested. The household response and feeder
> are modelled on calibrated data, not field-proven. The next step is 20–50
> homes and a measured feeder."

## Live demo commands

### Gateway, SPI HAT

```bash
export SAANJH_RADIO_BACKEND=auto          # lorarf first, in-tree driver fallback
python -m gateway.service --mode live --transport spi --nodes 3
```

The service writes the same CSVs and SQLite, and refreshes
`live_summary.json` every 10 s so a running session is visible in the dashboard.
The badge reads **🟢 LIVE LoRa evidence (session in progress)** while the run is
open, then **🟢 LIVE LoRa evidence** after a clean shutdown. A crashed run still
leaves the last partial summary, clearly marked as in progress.

### Gateway, USB RAK4631 bridge (Windows bench)

```bash
set SAANJH_SERIAL=COM5
python -m gateway.service --mode live --transport serial --nodes 3
```

### Node

```bash
cd firmware/rak4631_node
pio device monitor -b 115200
```

Expected command/ACK exchange:

```text
RX cmd id=42 dur=2700s limit=350W flags=0x01
RELAY battery
ACK id=42 status=accepted soc=82
TX seq=2 soc=81.9 mv=13180 w=348 a=0.35 flags=0x05
```

### Reserve refusal (the money shot)

Run the pack down to 70.0% on the bench supply, then send another command:

```text
RX cmd id=43 dur=2700s limit=350W flags=0x01
ACK id=43 status=2 soc=70
```

`status=2` is `REFUSED_RESERVE`; the relay stays on grid. Do not fake this by
editing the SoC; use the bench supply, or show the native test
`test_refuses_exactly_at_reserve` instead.

## Replay demo commands

```bash
python -m gateway.service --mode replay --nodes 3 --hours 6 \
  --duration-min 45 --packet-loss 0.02
python -m simulation.contracts
pytest -q
```

Expected replay headline:

| Metric | Value |
|---|---:|
| Telemetry sent / received | 6,480 / 6,343 (97.9%) |
| Commands sent / delivered | 34 / 33 (97.1%) |
| Mean / p95 command latency | 154.2 / 220.5 ms |
| SoC floor | 70.0% |
| Reserve breaches | 0 |
| Feeder peak | 154 kW |
| Overload before / after | 244 / 242 min |

## If something breaks

| Symptom | Recovery |
|---|---|
| Dashboard shows no gateway data | run the replay command above, then refresh |
| Streamlit port busy | `streamlit run dashboard/app.py --server.port 8502` |
| SPI radio not found | `SAANJH_RADIO_BACKEND=custom`, or switch to `--transport serial` |
| Node not joining | check antenna, 865.0625 MHz, SF9, sync 0x1424, TCXO 1.8 V |
| Relay chatters | check the 1N4007 flyback diode and the 10 kΩ gate pulldown |
| Upload fails | double-tap reset for DFU, retry `pio run -e node101 -t upload` |
| Live run has no summary | the service refreshes `live_summary.json` every 10 s; stop with Ctrl-C and wait for the final write |

Never demo with the battery below 70% and `SAANJH_ALLOW_NO_SENSOR=1`. That build
flag disables the reserve and must not be used in a submission demo.

## What to leave on screen

1. Dashboard tab **1 · Reliability** — the headline.
2. Tab **2 · Energy balance** — the honest correction.
3. Tab **6 · HIL gateway** — the relay trace and the labelled replay badge.
4. `docs/LIMITATIONS.md` — open in a second window for the Q&A.
