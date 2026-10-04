"""Architecture diagrams as code (Mermaid), rendered to SVG and PNG.

    python scripts/make_diagrams.py

Writes docs/architecture/*.mmd and, if the Mermaid CLI is installed in ui/node_modules,
renders each to .svg and .png. Line styles in the system diagram: energy solid,
data dashed, money dotted (set with linkStyle, legend included).
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "architecture")

ENERGY, DATA, MONEY = "energy", "data", "money"
STYLE = {
    ENERGY: "stroke:#1D2421,stroke-width:2.5px",
    DATA: "stroke:#1B5E8C,stroke-width:1.5px,stroke-dasharray:6 4",
    MONEY: "stroke:#2F7A4F,stroke-width:2px,stroke-dasharray:2 3",
}


def system():
    nodes = """
    subgraph HOMES["Homes on the DT (by segment)"]
      PV["Rooftop PV<br/>(few homes)"]
      LOADS["Household loads<br/>low-income / middle / affluent"]
      SM["Smart meter with<br/>load-limit relay (RDSS)"]
      INV["Inverter + battery"]
      NODE["SAANJH relay node<br/>(normally closed)"]
      ACT["Appliance actuator<br/>(geyser / pump / AC)"]
    end
    subgraph DTSITE["Distribution transformer site"]
      DT["100 kVA DT<br/>+ DT meter"]
      CB["Community battery<br/>second-life pack, BMS, PCS"]
      GW["SAANJH DT gateway<br/>runs dispatch locally<br/>even if backhaul fails"]
    end
    subgraph CLOUD["SAANJH cloud"]
      FC["Forecasting<br/>(Chronos-2, baselines)"]
      PLAN["Planning, M&V,<br/>settlement"]
    end
    subgraph DISCOM["DISCOM"]
      FDR["11 kV feeder"]
      HES["MDM / head-end<br/>(smart meters)"]
      ADMS["ADMS / DERMS<br/>IEEE 2030.5 / OpenADR"]
      BILL["Billing (credits)"]
    end
    subgraph PEOPLE["People"]
      OPAPP["Local operator app<br/>(RWA / SHG)"]
      MSG["Household WhatsApp /<br/>SMS / IVR"]
    end
    IES["India Energy Stack<br/>(future integration)"]
    subgraph LEGEND["Legend"]
      L1[" "] -->|"energy"| L2[" "]
      L3[" "] -->|"data"| L4[" "]
      L5[" "] -->|"money"| L6[" "]
    end
"""
    links = [
        ("FDR", "DT", "", ENERGY), ("DT", "SM", "", ENERGY), ("SM", "LOADS", "", ENERGY),
        ("PV", "LOADS", "", ENERGY), ("SM", "INV", "mains input via relay", ENERGY), ("INV", "LOADS", "backed-up circuits", ENERGY),
        ("CB", "DT", "LV bus", ENERGY), ("DT", "CB", "charging", ENERGY),
        ("DT", "GW", "DT meter readings", DATA), ("NODE", "GW", "LoRa", DATA), ("GW", "NODE", "open / close relay", DATA),
        ("GW", "ACT", "defer", DATA), ("GW", "CB", "set-points", DATA), ("HES", "SM", "load limit", DATA),
        ("GW", "HES", "band requests", DATA), ("ADMS", "GW", "allocation, events", DATA), ("GW", "PLAN", "telemetry", DATA),
        ("FC", "PLAN", "P10/P50/P90", DATA), ("PLAN", "GW", "approved plan", DATA), ("PLAN", "ADMS", "flexibility reports", DATA),
        ("PLAN", "OPAPP", "tasks", DATA), ("PLAN", "MSG", "notices", DATA), ("PLAN", "IES", "", DATA),
        ("BILL", "LOADS", "credits to inverter homes", MONEY), ("DISCOM", "OPAPP", "operator fee", MONEY),
        ("ADMS", "PLAN", "DFPO value", MONEY),
    ]
    lines = ["flowchart LR", nodes]
    for a, b, label, _ in links:
        lines.append(f'    {a} -->|"{label}"| {b}' if label else f"    {a} --> {b}")
    lines += [f"    linkStyle {i} {STYLE[kind]}" for i, kind in enumerate([ENERGY, DATA, MONEY])]
    offset = 3
    lines += [f"    linkStyle {i + offset} {STYLE[kind]}" for i, (_, _, _, kind) in enumerate(links)]
    lines.append("    style LEGEND fill:#ffffff,stroke:#C9CFCB")
    return "\n".join(lines)


SEQUENCE = """sequenceDiagram
    autonumber
    participant SLDC as SLDC / DISCOM ADMS
    participant CL as SAANJH cloud
    participant SDO as Sub-division engineer
    participant GW as DT gateway
    participant HH as Homes (meters, relays, actuators)
    participant CB as Community battery
    participant OP as Local operator
    CL->>CL: Midnight: day-ahead demand and deficit forecast (P10/P50/P90)
    CL->>CB: Pre-charge in solar hours, keep P90 reserve for the evening
    CL->>SDO: Recommended plan for the deficit window
    SDO->>CL: Approve (or modify) plan
    CL->>GW: Approved plan (cached locally)
    CL->>HH: Day-ahead WhatsApp / SMS / IVR notice
    SLDC->>GW: Shortfall: allocation for the DT (OpenADR-style event)
    GW->>HH: Hold appliance rebound, open inverter relays
    GW->>CB: Discharge (full support or essential-only)
    GW->>HH: If still short: essential band via smart meter load limit
    GW->>HH: Last resort: disconnect single homes in fair rotation
    loop every 15 minutes
      HH-->>GW: Meter and node readings
      GW->>GW: Re-plan, log every decision with its reason
    end
    SLDC->>GW: Shortfall ends
    GW->>HH: Release relays and appliances, staggered recharge and rebound
    GW->>CL: Event log and measurements
    CL->>CL: M&V against baseline (what rotational shedding would have done)
    CL->>SLDC: Flexibility report (counts toward DFPO)
    CL->>HH: Credits to inverter homes via billing, monthly summary
    HH->>OP: Complaints (COMPLAINT keyword or call)
"""

FAILURES = """flowchart TB
    subgraph F1["Backhaul to cloud down"]
      A1["Gateway keeps the last approved plan<br/>and local safety rules"] --> A2["Events still run from DT meter data;<br/>logs sync when the link returns"]
    end
    subgraph F2["Gateway down"]
      B1["No new limits or relay commands"] --> B2["Relays stay closed (fail-safe);<br/>meter limits revert to sanctioned load"] --> B3["DISCOM falls back to its normal<br/>load-shedding schedule"]
    end
    subgraph F3["Relay node down"]
      C1["Relay is normally closed"] --> C2["Inverter stays on grid;<br/>home is simply not counted as flexible"]
    end
    subgraph F4["Smart-meter communication delayed"]
      D1["Band request not acknowledged"] --> D2["Gateway uses battery and relays first,<br/>sheds the smallest blocks if the DT would exceed its limit"] --> D3["Console shows a stale-data warning"]
    end
    subgraph F5["Community battery fault"]
      E1["BMS opens contactor; thermal alarm"] --> E2["Dispatcher drops the battery from plans;<br/>essential band carries the gap"] --> E3["Operator and technician alerted;<br/>fire-safety procedure"]
    end
"""

ERD = """erDiagram
    DT ||--o{ FEEDER : "has LT feeders"
    DT ||--o{ HOUSEHOLD : supplies
    DT ||--o| COMMUNITY_BATTERY : hosts
    FEEDER ||--o{ HOUSEHOLD : connects
    HOUSEHOLD ||--|| METER : "has smart meter"
    HOUSEHOLD ||--o{ DEVICE : "relay node / actuator"
    HOUSEHOLD ||--o{ ENROLMENT : consents
    DT ||--o{ FORECAST : "day-ahead"
    DT ||--o{ EVENT : "deficit event"
    EVENT ||--|| PLAN : follows
    PLAN ||--o{ DISPATCH_COMMAND : issues
    DISPATCH_COMMAND }o--|| DEVICE : targets
    METER ||--o{ MEASUREMENT : records
    EVENT ||--o{ MEASUREMENT : "verified by"
    HOUSEHOLD ||--o{ CREDIT : earns
    EVENT ||--o{ CREDIT : generates
    HOUSEHOLD ||--o{ COMPLAINT : raises
    DT { string dt_id PK
         float rating_kva
         string feeder_11kv
         string subdivision }
    FEEDER { string feeder_id PK
             int lt_index }
    HOUSEHOLD { string household_id PK
                string segment
                bool critical_flag
                int band_w
                string phase }
    METER { string meter_no PK
            bool load_limit_capable }
    DEVICE { string device_id PK
             string kind
             string state }
    ENROLMENT { string enrolment_id PK
                date consented_on
                string language
                string consent_audio_ref
                bool opted_out }
    COMMUNITY_BATTERY { string battery_id PK
                        float capacity_kwh
                        float power_kw }
    FORECAST { string forecast_id PK
               date for_date
               string model
               json quantiles }
    EVENT { string event_id PK
            datetime start
            datetime end
            float peak_gap_kw
            string status }
    PLAN { string plan_id PK
           float battery_reserve_kwh
           int band_floor_w
           string approved_by }
    DISPATCH_COMMAND { string command_id PK
                       datetime at
                       string action
                       string reason }
    MEASUREMENT { string measurement_id PK
                  datetime at
                  float kw
                  float voltage_v }
    CREDIT { string credit_id PK
             float kwh
             float amount_rs }
    COMPLAINT { string complaint_id PK
                datetime raised_at
                string status }
"""

MONEY_FLOWS = """flowchart LR
    subgraph A["A. DISCOM-owned"]
      AD["DISCOM"] -->|"capex, O&M"| AA["Battery, gateway, nodes"]
      AD -->|"monthly fee"| AO["Local operator"]
      AD -->|"credits per kWh lent"| AH["Inverter homes"]
      AR["Regulator (ARR / DFPO)"] -->|"cost recovery, DFPO credit"| AD
    end
    subgraph B["B. Community-owned"]
      BG["Grant (state / CSR)"] -->|"part of capex"| BC["RWA / cooperative / SHG"]
      BL["Lender"] -->|"loan"| BC
      BD["DISCOM"] -->|"availability fee per kW-month"| BC
      BC -->|"credits"| BH["Inverter homes"]
      BC -->|"repayments"| BL
    end
    subgraph C["C. Third-party aggregator"]
      CD["DISCOM"] -->|"availability fee per kW-month"| CA["Registered aggregator"]
      CA -->|"credits"| CH["Inverter homes"]
      CA -->|"fee"| CO["Local operator"]
      CI["Investors"] -->|"capital, expects 15%"| CA
    end
"""


def main():
    os.makedirs(OUT, exist_ok=True)
    files = {"system_architecture": system(), "deficit_event_sequence": SEQUENCE, "failure_modes": FAILURES,
             "data_model": ERD, "money_flows": MONEY_FLOWS}
    for name, text in files.items():
        with open(os.path.join(OUT, f"{name}.mmd"), "w", encoding="utf-8") as f:
            f.write(text)
    mmdc = os.path.join(ROOT, "ui", "node_modules", ".bin", "mmdc.cmd" if os.name == "nt" else "mmdc")
    if not os.path.exists(mmdc):
        print("Mermaid CLI not installed (cd ui && npm i -D @mermaid-js/mermaid-cli); wrote .mmd sources only.")
        return 0
    cfg = os.path.join(OUT, "mermaid.config.json")
    with open(cfg, "w", encoding="utf-8") as f:
        f.write('{"theme":"neutral","themeVariables":{"fontFamily":"IBM Plex Sans, Arial, sans-serif","fontSize":"14px"},'
                '"flowchart":{"htmlLabels":true,"curve":"basis"}}')
    for name in files:
        src = os.path.join(OUT, f"{name}.mmd")
        for ext, extra in (("svg", []), ("png", ["-s", "2"])):
            r = subprocess.run([mmdc, "-i", src, "-o", os.path.join(OUT, f"{name}.{ext}"), "-c", cfg, "-b", "white", *extra],
                               capture_output=True, text=True, shell=os.name == "nt")
            if r.returncode != 0:
                print(f"{name}.{ext} failed: {r.stderr[-400:]}")
                return 1
        print(f"docs/architecture/{name}.svg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
