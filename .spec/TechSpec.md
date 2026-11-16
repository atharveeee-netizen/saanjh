# Technical Specification — SAANJH

**Project:** SAANJH  
**Scope:** Architecture, Hardware, Edge Gateway, Machine Learning, and Simulation Engines  

---

## 1. System Technology Stack

| Subsystem | Components & Frameworks | Description |
|---|---|---|
| **Firmware (Edge Nodes)** | C++17, PlatformIO, Nordic nRF52 SDK, SX1262 LoRa Driver | RAK4631 WisBlock, INA226 I2C sensor, 10A NC Relay |
| **Gateway (Edge Hub)** | Raspberry Pi CM4 / Linux, Python 3.11, SQLite3, Spidev | SX1262 SPI HAT, rolling 15-min dispatcher, safety supervisor |
| **Grid Simulation** | Python 3.11, NumPy, Pandas, Pydantic v2 | 365-day Monte Carlo engine, 15-min time-series resolution |
| **Forecasting Engine** | Chronos-2, XGBoost Quantile, Scikit-learn | Day-ahead P10/P50/P90 probabilistic net load forecaster |
| **Operator Console** | Streamlit, Plotly Dark, Pandas | 7-tab evidence UI, HIL replay viewer, calibration scorecard |
| **Web & Secondary UI** | React 18, Vite, TypeScript, TailwindCSS | Multi-lingual console (Hindi, Marathi, English) |
| **Data Contracts** | Pydantic v2 Models, JSON Schema Draft 2020-12 | Bi-directional schema validation preventing data drift |

## 2. Communications Architecture
- **RF Spectrum:** 865.0625 MHz (Indian ISM band, 865–867 MHz license-exempt).
- **Modulation:** LoRa P2P, SF9, BW 125 kHz, CR 4/5, Preamble 8, Sync Word 0x12, Tx Power 14 dBm.
- **Protocol:** Packed little-endian binary struct (Header + Type + Payload + CRC-16/CCITT-FALSE).
- **Latency / Cycle:** 10 s telemetry heartbeat, 15-min dispatch evaluation window.

## 3. Physical Hardware Interfaces
- **INA226 Sensor:** I2C address 0x40, Shunt 0.002 Ω, Bus voltage up to 36 V, Current up to 20 A.
- **Fail-Safe Relay:** GPIO driven via NPN transistor / optocoupler. Relay NC contact carries AC/DC grid feed.
- **Opt-Out Button:** Hardware debounced interrupt GPIO; latches software state in MCU RAM.

## 4. Machine Learning & Forecasting Specifications
- **Forecasting Objective:** Pinball loss quantile regression ($q \in \{0.1, 0.5, 0.9\}$) for day-ahead net demand.
- **Evaluation Metrics:** MASE (Mean Absolute Scaled Error) against seasonal naive scale, empirical P10–P90 coverage.
- **Inference Profile:** Sub-50ms CPU execution on Raspberry Pi CM4.
