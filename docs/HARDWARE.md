# Hardware guide — RAK4631 node and CM4 gateway

This document describes the physical prototype: what connects to what, which
pins are used, how the radio is configured and how the bench is validated. It
intentionally contains no mains wiring.

> **Scope.** ≤12 V DC bench prototype. The relay transfers a 12 V dummy load
> between a 12 V "grid" adapter and a 12 V LiFePO4 pack. A production system
> needs a certified inverter/ESS and a licensed electrician.

## System shape

```text
   12 V "grid" adapter ──NC──┐
                             ├── relay COM ── 12 V dummy load ── common GND
   12.8 V LiFePO4 ──fuse──INA226──NO──┘
        │
        └── RAK4631 + RAK5005-O ── LoRa 865.0625 MHz ── CM4 + SX1262 HAT
                                                          │
                                                    CSV + SQLite + Streamlit
```

The relay's **normally-closed contact is the grid path**. De-energised,
unpowered, reset or crashed all mean "load on grid". The node can only move the
load onto the battery by deliberately energising the coil, and it drops the coil
the moment the reserve, consent or sensor checks fail.

## Node pin map (RAK4631 + RAK5005-O)

| Signal | Pin | Direction | Notes |
|---|---|---|---|
| Relay drive | WB_IO1 / GPIO 17 | out | 220 Ω → IRLZ44N gate, 10 kΩ gate–GND |
| Push button | WB_IO3 / GPIO 21 | in | to GND, internal pull-up, 1.5 s hold |
| Status LED | GPIO 35 | out | green, heartbeat |
| Fault/opt-out LED | GPIO 36 | out | blue, slow blink = opted out, fast = fault |
| I²C SDA | GPIO 13 | bidir | INA226 SDA |
| I²C SCL | GPIO 14 | out | INA226 SCL, 400 kHz |
| INA226 supply | 3V3 / GND | — | **not** the 12 V rail |

### Internal SX1262 (RAK4630)

These are the radio's own SPI1 pins on the module, not the WisBlock IO-slot SPI
pins. Firmware sets them in `include/config.h`; do not rewire them.

| Signal | GPIO |
|---|---:|
| CS | 42 |
| SCK | 43 |
| MOSI | 44 |
| MISO | 45 |
| BUSY | 46 |
| DIO1 | 47 |
| RESET | 38 |

DIO2 drives the antenna switch and DIO3 feeds the 1.8 V TCXO. The firmware
configures both through RadioLib; there is no MCU pin to toggle.

## Node wiring

| From | To |
|---|---|
| Battery + | 2 A fuse → INA226 IN+ |
| INA226 IN− | relay NO |
| Relay COM | load + |
| Relay NC | 12 V grid adapter + |
| Load − | battery − and adapter − (common ground) |
| Relay coil + | battery + (fused) |
| Relay coil − | MOSFET drain |
| MOSFET source | battery − |
| MOSFET gate | GPIO 17 through 220 Ω; 10 kΩ gate–GND |
| 1N4007 | cathode to coil +, anode to coil − (flyback) |
| Button | GPIO 21 to GND |
| RAK4631 GND | common ground |

Use a common ground between the 12 V adapter, the battery and the RAK4631. Do
**not** connect the 12 V pack to the RAK4631 3V3 pin. Fuse the battery positive
close to the pack.

## Radio configuration

Both ends must match exactly. The firmware and `gateway/lora_driver.py` share
these constants.

| Parameter | Value |
|---|---|
| Band | 865–867 MHz Indian ISM |
| Frequency | 865.0625 MHz |
| Spreading factor | SF9 |
| Bandwidth | 125 kHz |
| Coding rate | 4/5 |
| Sync word | 0x1424 (private) |
| TX power | 14 dBm (~25 mW) |
| Preamble | 8 symbols |
| TCXO | 1.8 V |
| Regulator | DC-DC |
| Frame header | `53 4A` magic, version 1, type, node id (6 B) |

Frames are 19 B telemetry, 17 B command, 14 B ACK, with CRC-16/CCITT-FALSE.
The three golden frames in `tests/test_protocol.py` and
`test/test_protocol/test_protocol.cpp` are byte-identical across Python and C++.

## Gateway pin map (CM4 + Waveshare SX1262 HAT)

Defaults in `gateway/lora_driver.py`; every value can be overridden with an
environment variable.

| Signal | BCM GPIO | Env override |
|---|---:|---|
| SPI bus / device | 0 / 0 | `SAANJH_SPI_BUS`, `SAANJH_SPI_DEVICE` |
| RESET | 18 | `SAANJH_RESET_GPIO` |
| BUSY | 20 | `SAANJH_BUSY_GPIO` |
| DIO1 | 16 | `SAANJH_DIO1_GPIO` |
| TXEN | 6 | `SAANJH_TXEN_GPIO` |
| RXEN | driven by DIO2 | — |
| TCXO | optional | `SAANJH_TCXO` |

Gate the SPI backend with `SAANJH_RADIO_BACKEND`:

* `lorarf` — require LoRaRF-Python (preferred);
* `custom` — require the in-tree SX1262 register driver;
* `auto` — try LoRaRF, fall back to the in-tree driver (default).

On a Windows bench, a RAK4631 can act as a USB radio bridge:
`SAANJH_SERIAL=COM5 python -m gateway.service --mode live --transport serial`.

## Build and flash

```bash
cd firmware/rak4631_node
pio run -e node101 -t upload
pio run -e node102 -t upload
pio run -e node103 -t upload
pio device monitor -b 115200
```

Latest verified build (PlatformIO, release):

| Environment | RAM | Flash |
|---|---:|---:|
| node101 | 14,328 B / 248,832 B (5.8%) | 121,740 B / 815,104 B (14.9%) |
| node102 | 14,328 B / 248,832 B (5.8%) | 121,740 B / 815,104 B (14.9%) |
| node103 | 14,328 B / 248,832 B (5.8%) | 121,740 B / 815,104 B (14.9%) |

Expected boot output:

```text
SAANJH node 101 fw 1.0.0
INA226=ok mv=13320 soc=82.0%
RADIO ok 865.0625 MHz SF9 BW125 CR4/5
CONSENT opted_out=0 relay=grid
TX seq=1 soc=82.0 mv=13320 w=0 a=0.00 flags=0x01
```

## Safety behaviour

| Condition | Relay | Telemetry flag |
|---|---|---|
| Reset / no power | grid (de-energised) | — |
| No valid command | grid | `F_RESERVE_OK` if applicable |
| Discharge accepted, SoC > 70% | battery | `F_RESERVE_OK \| F_RELAY_ENERGISED` |
| SoC at or below 70.0% | grid, command refused | no `F_RESERVE_OK` |
| Push-button opt-out | grid immediately | `F_OPTED_OUT` |
| INA226 missing / implausible battery | grid, discharge refused | `F_FAULT` |
| Command duration expires | grid, `ACK_DONE` | relay bit cleared |
| Radio dies | grid after the last command expires | none (link is down) |

The gateway independently enforces the same reserve and opt-out rules in
`gateway/safety.py`; a command that violates either is dropped before it is
transmitted. The node is the second, independent layer.

## Bench validation checklist

Record the pass/fail and the measured values in the evidence table below.

1. **No battery:** boot the node. Relay stays on grid, blue LED fast-blinks,
   telemetry carries `F_FAULT`, and discharge commands are refused.
2. **Charged pack:** connect >13.2 V. `soc` reads above 70% and
   `F_RESERVE_OK` is set.
3. **Discharge:** send a command from the gateway. Relay clicks to battery, ACK
   is `0` (accepted), and the load current appears in telemetry.
4. **Opt-out:** hold the button 1.5 s. Relay opens within one loop, telemetry
   shows `F_OPTED_OUT`, and the state survives a power cycle.
5. **Expiry:** opt back in and command discharge, then disconnect the gateway.
   The node opens the relay when the command duration expires (max 60 min).
6. **Reserve:** run the pack down to 70.0%. The next command is refused with
   `ACK_REFUSED_RESERVE` and the relay stays on grid.
7. **Range:** log RSSI/SNR at the gateway over the demo distance.

### Evidence log (to be filled on the bench)

| Check | Date | Result | Measured |
|---|---|---|---|
| 1. No battery fails safe | | | |
| 2. SoC > 70% accepted | | | |
| 3. Relay transfers to battery | | | |
| 4. Opt-out survives power cycle | | | |
| 5. Command expiry opens relay | | | |
| 6. 70.0% boundary refused | | | |
| 7. RSSI / SNR at ___ m | | | |

The repository currently contains **no live hardware evidence**. All committed
gateway numbers are seeded replay until this table is filled.

## Native tests without hardware

The protocol, controller and battery model are portable C++ with Unity tests:

```bash
cd firmware/rak4631_node
pio test -e native
```

All 34 tests build as one native binary in `test/test_native/`, because
PlatformIO compiles every file under `test/` into the same program. The
coverage is the CRC check value and golden frames, rejection of bad magic / CRC
/ short frames, the exact 70.0% boundary, opt-out refusal, command expiry and
duplicate handling, coulomb counting, OCV interpolation and implausible battery
handling.

## Known hardware limits

* SoC is estimated from OCV plus coulomb counting, not a certified BMS. The
  pack's own protection board remains the last line of defence.
* No temperature sensor is fitted; telemetry carries a placeholder 25 °C and
  leaves `R_TEMP_VALID` clear.
* One relay, one load. This demonstrates the control and safety path, not a
  whole-home transfer switch.
* LoRa P2P is deliberate for three nodes. A larger deployment needs an SX130x
  concentrator and a network server.
* The radio is not frequency-hopping; it uses one 25 kHz channel inside the
  Indian 865–867 MHz band.
* The 12 V "grid" adapter is not a grid. Loss-of-supply behaviour is modelled
  in the annual simulation, not measured here.
