/*
 * SAANJH RAK4631 node - compile-time configuration.
 *
 * The node is a 12 V DC prototype only. It never touches mains. The relay
 * transfers a 12 V dummy load between a 12 V "grid" supply (NC contact) and a
 * 12 V battery (NO contact). De-energised therefore means "load on grid".
 */
#pragma once

#include <stdint.h>

#ifndef SAANJH_NODE_ID
#define SAANJH_NODE_ID 101
#endif

#ifndef SAANJH_RESERVE_PCT
#define SAANJH_RESERVE_PCT 70.0f
#endif

#ifndef SAANJH_TELEMETRY_MS
#define SAANJH_TELEMETRY_MS 10000UL
#endif

#ifndef SAANJH_BATTERY_CAPACITY_WH
#define SAANJH_BATTERY_CAPACITY_WH 76.8f   /* 12.8 V x 6 Ah LiFePO4 */
#endif

#define SAANJH_FW_VERSION "1.0.0"

/* ------------------------------------------------------------------ radio */
/* RAK4631 internal SX1262. These are the RAK4630 SPI1 pins, NOT the WisBlock
 * IO-slot SPI pins (26/3/29/30). Confirmed against the RAK4631 datasheet and
 * the Meshtastic RAK4631 variant. DIO2 drives the antenna switch; DIO3 feeds
 * the 1.8 V TCXO. Do not configure the RF switch pins from the MCU. */
#define PIN_RADIO_CS 42
#define PIN_RADIO_DIO1 47
#define PIN_RADIO_RESET 38
#define PIN_RADIO_BUSY 46
#define PIN_RADIO_MISO 45
#define PIN_RADIO_SCK 43
#define PIN_RADIO_MOSI 44

#define SAANJH_RADIO_FREQ_MHZ 865.0625f   /* India 865-867 MHz ISM */
#define SAANJH_RADIO_BW_KHZ 125.0f
#define SAANJH_RADIO_SF 9
#define SAANJH_RADIO_CR 5                 /* 4/5, matches gateway LoRaRF call */
#define SAANJH_RADIO_POWER_DBM 14         /* ~25 mW; well inside Indian ERP limit */
#define SAANJH_RADIO_PREAMBLE 8
#define SAANJH_RADIO_TCXO_V 1.8f
#define SAANJH_RADIO_RETRY_MS 5000UL

/* --------------------------------------------------------------- hardware */
/* WisBlock IO-slot pins on the RAK5005-O base board. */
#define PIN_RELAY 17        /* WB_IO1, drives the relay MOSFET gate */
#define PIN_BUTTON 21       /* WB_IO3, to GND, internal pull-up */
#define PIN_LED_STATUS 35   /* green */
#define PIN_LED_FAULT 36    /* blue */

#define RELAY_ACTIVE_HIGH 1
#if RELAY_ACTIVE_HIGH
#define RELAY_ACTIVE_LEVEL HIGH
#define RELAY_INACTIVE_LEVEL LOW
#else
#define RELAY_ACTIVE_LEVEL LOW
#define RELAY_INACTIVE_LEVEL HIGH
#endif

/* INA226 high-side shunt in the battery positive lead.
 * 0.05 ohm keeps the shunt-voltage register inside +/-81.92 mV up to 1.6 A. */
#define INA226_ADDRESS 0x40
#define INA226_SHUNT_OHMS 0.05f
#define INA226_CURRENT_LSB_A 0.001f
#define INA226_CALIBRATION 102            /* round(0.00512 / (0.001 * 0.05)) */
#define SAANJH_I2C_CLOCK 400000UL

#define SAANJH_BATTERY_MIN_MV 10500       /* 4S LiFePO4 lower sanity bound */
#define SAANJH_BATTERY_MAX_MV 15000
#define SAANJH_BUTTON_HOLD_MS 1500UL
#define SAANJH_BUTTON_DEBOUNCE_MS 30UL
#define SAANJH_COMMAND_MAX_DURATION_S 3600
#define SAANJH_TEMP_PLACEHOLDER_C 25
#define SAANJH_SERIAL_BAUD 115200UL

/* Persist consent (opt-out) across power cycles in the internal littlefs. */
#ifndef SAANJH_PERSIST_OPT_OUT
#define SAANJH_PERSIST_OPT_OUT 1
#endif

/* Bench-only escape hatch: allow discharge with no INA226 fitted. Never enable
 * this for a submission demo; without current sensing the 70% reserve is not
 * enforceable. */
#ifndef SAANJH_ALLOW_NO_SENSOR
#define SAANJH_ALLOW_NO_SENSOR 0
#endif
