# System Architecture & Topology — SAANJH

**Project:** SAANJH  
**Scope:** Energy, Data, Protocol, and Financial Mesh  

---

## 1. End-to-End System Mesh

```mermaid
flowchart TB
    subgraph DISCOM["DISCOM Distribution Tier"]
        MV["11 kV Substation Feeder"]
        HES["Smart Meter MDM / HES (RDSS)"]
        ADMS["ADMS / DERMS (OpenADR / IEEE 2030.5)"]
    end

    subgraph DT_SITE["Distribution Transformer (100 kVA Site)"]
        DT["100 kVA Distribution Transformer + Meter"]
        BESS["Community BESS (100 kWh / 40 kW Second-Life LFP)"]
        GW["SAANJH CM4 Edge Gateway<br/>• Rolling 15-min Dispatch Engine<br/>• Local Safety Supervisor<br/>• SQLite3 + CSV Time-Series Engine"]
    end

    subgraph CLOUD["Cloud Services"]
        FC["Probabilistic Forecasting Engine (Chronos-2 / XGBoost)"]
        SETTLE["Settlement & DFPO Verification"]
    end

    subgraph FLEET["Neighbourhood Consumers (200-250 Homes)"]
        SM["RDSS Smart Meter (Load Limiter)"]
        ESS["Essential Loads (Lights, Fans, Phone)"]
        LUX["Heavy / Deferrable Loads (AC, Pump, Geyser)"]
        
        subgraph INVERTER_NODES["Inverter Homes (4-15%)"]
            NODE["RAK4631 Edge Node (Nordic nRF52840 + SX1262)"]
            RELAY["Fail-Safe NC Relay"]
            INV["Home Inverter + Battery (1.8 kWh)"]
        end
    end

    MV --> DT
    DT --> BESS
    DT --> SM
    SM --> ESS
    SM --> LUX
    SM --> RELAY
    RELAY --> INV
    INV --> ESS

    NODE <-->|"LoRa P2P (865 MHz)"| GW
    DT <-->|"RS-485 / Modbus"| GW
    BESS <-->|"CAN / Modbus"| GW
    GW <-->|"Cellular 4G"| CLOUD
    GW -.->|"Load Cap Requests"| HES
    HES -->|"Disconnect/Cap Command"| SM
    ADMS <-->|"Flexibility Signals"| GW
    CLOUD -->|"M&V Records"| ADMS
```

## 2. Dispatch Priority Ladder (15-min Intervals)
1. **Rebound & Inertial Flexibility:** Suppress appliance rebound.
2. **Inverter Relay Borrowing:** Energize NC relay on home inverters (SoC > 70%), least-utilized homes first.
3. **Appliance Deferral:** Shift water heaters, pumps, AC setpoints.
4. **Community BESS Full Support:** Discharge community BESS if capacity covers total anticipated deficit.
5. **Essential Band Load Limiting:** Remote smart meter cap: 1000 W $\rightarrow$ 750 W $\rightarrow$ 500 W.
6. **Community BESS Reserve Injection:** Defend the 500 W essential floor with reserve energy.
7. **Fair Rotational Disconnect:** Disconnect single homes with least cumulative annual outage; critical loads last.
