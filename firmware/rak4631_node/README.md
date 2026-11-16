# SAANJH RAK4631 node firmware

Firmware for the hardware-in-the-loop prototype: one RAK4631 WisBlock node per
household, a 12 V DC dummy load, a 12 V battery and a fail-safe relay. The node
sends telemetry every 10 s over LoRa P2P at 865.0625 MHz, accepts discharge
commands from the CM4 gateway, acknowledges them, and refuses to discharge at or
below **70% SoC** or when the household has opted out.

> **This is a ≤12 V DC bench prototype.** It does not switch mains. The relay
> transfers a 12 V dummy load between a 12 V "grid" supply and a 12 V battery.
> A production system needs a certified inverter/ESS and a licensed electrician.

## Safety behaviour

| Condition | Relay | Telemetry flag |
|---|---|---|
| Reset / no power | grid (de-energised) | — |
| No valid command | grid | `F_RESERVE_OK` if applicable |
| Discharge accepted, SoC > 70% | battery | `F_RESERVE_OK \| F_RELAY_ENERGISED` |
| SoC at or below 70% | grid, discharge refused | no `F_RESERVE_OK` |
| Push-button opt-out | grid immediately | `F_OPTED_OUT` |
| INA226 missing / battery implausible | grid, discharge refused | `F_FAULT` |
| Command duration expires | grid, `ACK_DONE` sent | relay bit cleared |
| Radio dies | grid (after last command expires) | none (link is down) |

The gateway enforces the same rules in `gateway/safety.py`; the node is the
second, independent layer. The relay's **NC contact is the grid path**, so a
brown-out, reset or unplugged GPIO returns the load to grid.

## Bill of materials (one node)

| Item | Example part | Qty | Notes |
|---|---|---|---|
| WisBlock core | RAK4631 (nRF52840 + SX1262) | 1 | 865 MHz variant |
| Base board | RAK5005-O | 1 | IO slot for relay/button |
| Current/voltage sense | INA226 breakout, 0.05 Ω shunt | 1 | I2C address 0x40 |
| Relay | SRD-12VDC-SL-C, 10 A, SPDT | 1 | 12 V coil; NC = grid |
| Relay driver | IRLZ44N logic-level MOSFET | 1 | 3.3 V gate compatible |
| Flyback diode | 1N4007 | 1 | across coil |
| Gate resistor | 220 Ω | 1 | series with gate |
| Gate pulldown | 10 kΩ | 1 | relay off if MCU floats |
| Push button | momentary, panel mount | 1 | to GND on WB_IO3 |
| Battery | 12.8 V 6 Ah LiFePO4 with BMS | 1 | ~77 Wh |
| Grid supply | 12 V 2 A DC adapter | 1 | **DC only, no mains** |
| Dummy load | 12 V 10 W lamp or power resistor | 1 | ≤0.9 A |
| Enclosure, fuses | ABS box, 2 A blade fuse | 1 | fuse battery positive |

The INA226 shunt is in the **battery positive** lead. At 0.9 A the shunt drops
45 mV and dissipates 40 mW; the 0.05 Ω value keeps the INA226 shunt-voltage
register inside its ±81.92 mV range up to 1.6 A.

## Wiring

| Signal | RAK4631 pin | Connects to |
|---|---|---|
| Relay drive | WB_IO1 (GPIO 17) | 220 Ω → IRLZ44N gate; 10 kΩ gate–GND |
| Button | WB_IO3 (GPIO 21) | button to GND; internal pull-up |
| I2C SDA | 13 | INA226 SDA |
| I2C SCL | 14 | INA226 SCL |
| I2C 3V3/GND | 3V3 / GND | INA226 VCC/GND |
| Battery + | — | 2 A fuse → INA226 IN+ |
| INA226 IN− | — | relay NO |
| Relay COM | — | load + |
| Relay NC | — | 12 V grid adapter + |
| Load − | — | battery − / adapter − (common ground) |
| Relay coil + | — | battery + (fused) |
| Relay coil − | — | MOSFET drain; source to battery −; diode across coil |

Use a common ground between the 12 V supply, battery and RAK4631 GND. Do **not**
connect the 12 V battery to the RAK4631 3V3 pin.

## Build and upload

PlatformIO is pinned in `platformio.ini`. One image per node:

```bash
cd firmware/rak4631_node
pio run -e node101 -t upload
pio run -e node102 -t upload
pio run -e node103 -t upload
```

The RAK4631 bootloader exposes a USB CDC port. If upload fails, double-tap the
reset button to enter DFU mode and retry.

Override the defaults with build flags if needed:

```bash
pio run -e node101 --project-option "build_flags=-DSAANJH_NODE_ID=104 ..."
```

## Serial console

```bash
pio device monitor -b 115200
```

Expected boot output:

```
SAANJH node 101 fw 1.0.0
INA226=ok mv=13320 soc=82.0%
RADIO ok 865.0625 MHz SF9 BW125 CR4/5
CONSENT opted_out=0 relay=grid
TX seq=1 soc=82.0 mv=13320 w=0 a=0.00 flags=0x01
```

A command and ACK look like:

```
RX cmd id=42 dur=2700s limit=350W flags=0x01
RELAY battery
ACK id=42 status=accepted soc=82
TX seq=2 soc=81.9 mv=13180 w=348 a=0.35 flags=0x05
```

## Push-button consent

Hold the button for **1.5 s** to toggle opt-out. The blue LED blinks slowly
while opted out; the relay opens immediately and the state is written to
`/saanjh.cfg` in the internal littlefs. A corrupt or unreadable config defaults
to **opted out** (conservative). Hold again to opt back in.

## Test without hardware

The protocol, controller and battery model are portable C++ and have native
unit tests. PlatformIO compiles every file under `test/` into one binary, so
the three domains share `test/test_native/test_main.cpp`:

```bash
pio test -e native
```

The tests cover:

* CRC-16/CCITT-FALSE check value and the three golden frames shared with
  `gateway/protocol.py`;
* rejection of bad magic, bad CRC, short frames and wrong message types;
* the exact 70.0% reserve boundary;
* opt-out refusal and immediate relay opening;
* command expiry, duplicate-command handling and duration clamping;
* coulomb counting, OCV interpolation and implausible-battery handling.

## Bench validation checklist

1. With no battery connected, boot the node: relay must stay on **grid**, blue
   LED fast-blinks, and telemetry must carry `F_FAULT`.
2. Connect a charged pack (>13.2 V). Confirm `soc` is above 70% and
   `F_RESERVE_OK` is set.
3. From the gateway, send a discharge command. Confirm the relay clicks to
   **battery**, the ACK is `accepted`, and the load current appears in telemetry.
4. Hold the button 1.5 s. Confirm the relay opens within one loop, telemetry
   shows `F_OPTED_OUT`, and the state survives a power cycle.
5. Opt back in, command discharge, then disconnect the gateway. Confirm the node
   opens the relay when the command duration expires (max 60 min).
6. Run the pack down to 70.0% (or bench-test with the OCV table) and confirm the
   next command is refused with `ACK_REFUSED_RESERVE` and the relay stays on
   grid.
7. Log RSSI/SNR at the gateway over the demo distance and record it in
   `docs/HARDWARE.md`.

## Limitations

* SoC is estimated from OCV + coulomb counting, not a certified BMS; the pack
  BMS remains the last line of defence.
* No temperature sensor is fitted. Telemetry carries a placeholder 25 °C and
  leaves the `R_TEMP_VALID` reserved bit clear.
* One relay, one load. The prototype demonstrates the control path, not a
  whole-home transfer switch.
* LoRa P2P is deliberate for three nodes. A larger deployment needs an SX130x
  concentrator and a network server (see `docs/CODE_REUSE_RESEARCH.md`).
* The radio is not frequency-hopping; 865.0625 MHz is a single 25 kHz channel
  inside the Indian 865–867 MHz ISM band.
