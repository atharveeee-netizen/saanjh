# Bill of materials — Phase 1 prototype

This is the bill of materials for the **bench prototype**, not a production
design. It builds three household nodes and one gateway. All prices are rough
Indian retail prices in November 2026, rounded up, and are included to show the
order of magnitude. They are not quotations.

> **Safety scope.** Everything here is ≤12 V DC. The prototype does not switch
> mains, does not connect to a live service, and must not be installed in a
> consumer's wiring. A production unit needs a certified inverter/ESS, a
> licensed electrician and the DISCOM's approval.

## Household node (×3)

| # | Item | Example part | Qty | Unit ₹ | Line ₹ | Notes |
|---|---|---|---:|---:|---:|---|
| 1 | WisBlock core | RAK4631 (nRF52840 + SX1262) | 1 | 3,200 | 3,200 | 865 MHz variant |
| 2 | WisBlock base | RAK5005-O | 1 | 1,100 | 1,100 | IO slot for relay and button |
| 3 | Current/voltage sense | INA226 breakout, 0.05 Ω shunt | 1 | 250 | 250 | I²C 0x40, high-side in battery + |
| 4 | Power relay | SRD-12VDC-SL-C, 10 A SPDT | 1 | 120 | 120 | 12 V coil; **NC = grid** |
| 5 | Relay driver | IRLZ44N logic-level MOSFET | 1 | 40 | 40 | 3.3 V gate |
| 6 | Flyback diode | 1N4007 | 1 | 5 | 5 | across coil |
| 7 | Gate resistor | 220 Ω, ¼ W | 1 | 2 | 2 | series with gate |
| 8 | Gate pulldown | 10 kΩ, ¼ W | 1 | 2 | 2 | relay off if MCU floats |
| 9 | Push button | momentary, panel mount | 1 | 30 | 30 | to GND on WB_IO3 |
| 10 | Battery | 12.8 V 6 Ah LiFePO4 with BMS | 1 | 2,800 | 2,800 | ~77 Wh, 4S |
| 11 | Grid supply | 12 V 2 A DC adapter | 1 | 350 | 350 | **DC only** |
| 12 | Dummy load | 12 V 10 W lamp or power resistor | 1 | 150 | 150 | ≤0.9 A |
| 13 | Fuse | 2 A blade fuse + holder | 1 | 80 | 80 | battery positive |
| 14 | Enclosure | ABS box, ~150×100×70 mm | 1 | 250 | 250 | ventilation for the dummy load |
| 15 | Wiring | terminal blocks, 18 AWG, heatshrink | 1 | 200 | 200 | |
| | **Node subtotal** | | | | **8,579** | |
| | **Three nodes** | | 3 | | **25,737** | |

The INA226 shunt sits in the **battery positive** lead. At 0.9 A it drops 45 mV
and dissipates 40 mW. The 0.05 Ω value keeps the shunt-voltage register inside
its ±81.92 mV range up to 1.6 A.

## Gateway (×1)

| # | Item | Example part | Qty | Unit ₹ | Line ₹ | Notes |
|---|---|---|---:|---:|---:|---|
| 1 | Compute module | Raspberry Pi CM4, 4 GB RAM, no eMMC | 1 | 7,500 | 7,500 | CM4 Lite is fine with microSD |
| 2 | Carrier board | CM4 IO board or compact carrier | 1 | 3,500 | 3,500 | 40-pin GPIO + USB |
| 3 | LoRa HAT | Waveshare SX1262 865 MHz HAT | 1 | 2,200 | 2,200 | SPI0, CS0 |
| 4 | Antenna | 865–867 MHz, SMA, 3 dBi | 1 | 350 | 350 | never transmit without one |
| 5 | microSD | 32 GB A1/A2 | 1 | 500 | 500 | OS + logs |
| 6 | Power supply | USB-C 27 W (CM4 IO board) | 1 | 700 | 700 | official supply preferred |
| 7 | Enclosure | ventilated ABS case | 1 | 500 | 500 | |
| | **Gateway subtotal** | | | | **15,250** | |

## Bench equipment (not shipped, assumed available)

| Item | Purpose |
|---|---|
| Digital multimeter | verify 12 V rails, polarity and fuse continuity |
| USB power meter | measure node idle and transmit current |
| Adjustable bench supply (0–30 V, 3 A) | run the pack down to the 70% boundary safely |
| Oscilloscope (optional) | relay coil flyback and DIO1 timing |
| USB micro/cable for RAK4631 | flashing and serial console |

## Prototype total

| Build | Cost (₹) |
|---|---:|
| 3 × household node | 25,737 |
| 1 × gateway | 15,250 |
| **Bench prototype** | **40,987** |

For comparison, the annual simulation's shared-battery case costs about
₹6,980 per home at 100% adoption, dominated by storage rather than radios. The
bench BOM is dominated by the CM4 and the three LiFePO4 packs; neither price
scales to a production per-home cost.

## What the prototype deliberately does not contain

* No mains contactor, energy meter, CT clamp or inverter. It is a 12 V DC
  analogue of the transfer decision, not a service entrance.
* No fingerprint sensor, camera, CO₂ sensor, microphone, load cell or
  accelerometer. None is needed for the control path, and each adds cost,
  privacy surface and failure modes.
* No certified BMS beyond the pack's own protection board. SoC is estimated,
  not guaranteed.
* No weatherproofing or surge protection. It is a bench unit.

## Reuse and licences

The firmware vendors **RadioLib** (MIT) and builds against the Adafruit nRF52
Arduino core (LGPL-2.1, linked as a library). The gateway prefers
**LoRaRF-Python** (MIT) and falls back to the in-tree SX1262 driver (MIT). See
[`OPEN_SOURCE_NOTICES.md`](OPEN_SOURCE_NOTICES.md) for the full list and the
distribution obligations.
