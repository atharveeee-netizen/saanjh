# Data Schemas & Protocol Specifications — SAANJH

**Project:** SAANJH  
**Scope:** Binary Protocol Framing, Pydantic Contract Models, and SQLite Schemas  

---

## 1. Binary LoRa Frame Schema (C++ Struct & Python Struct)

```
Offset  Field         Type    Size (B)  Description
0..1    magic         char[2] 2         Must be b"SJ" (0x53, 0x4A)
2       version       uint8   1         Protocol version (currently 1)
3       msg_type      uint8   1         0x01 = Telemetry, 0x02 = Command, 0x03 = ACK
4..5    node_id       uint16  2         Unique node ID (e.g., 101, 102, 103)
6..n-3  payload       bytes   var       Message-specific binary payload
n-2..n-1 crc16        uint16  2         CRC-16/CCITT-FALSE across bytes 0..(n-3)
```

### Telemetry Payload (10 Bytes)
```
Offset  Field         Type    Size (B)  Description
0..1    seq           uint16  2         Telemetry sequence number (monotonic)
2..3    battery_mv    uint16  2         Pack terminal voltage in millivolts
4..5    load_w        uint16  2         Instantaneous power draw in Watts
6       soc_pct       uint8   1         State of charge percentage (0-100)
7       flags         uint8   1         Bitmask: 0x01=ReserveOK, 0x02=OptOut, 0x04=RelayOn, 0x08=Fault
8       temp_c        int8    1         Temperature in Celsius (-128 to 127)
9..10   reserved      uint16  2         Reserved for future extensions
```

### Command Payload (9 Bytes)
```
Offset  Field         Type    Size (B)  Description
0..1    seq           uint16  2         Gateway command sequence number
2..3    command_id    uint16  2         Unique ID for ACK tracking and idempotency
4..5    duration_s    uint16  2         Requested discharge duration in seconds (capped at 1800s)
6..7    power_limit_w uint16  2         Maximum allowable discharge power in Watts
8       flags         uint8   1         0x01 = Discharge, 0x02 = Cancel
```

### ACK Payload (6 Bytes)
```
Offset  Field         Type    Size (B)  Description
0..1    seq           uint16  2         Echoed command sequence number
2..3    command_id    uint16  2         Targeted command ID
4       status        uint8   1         0=Accepted, 1=RefusedReserve, 2=RefusedOptOut, 3=Done, 4=Error
5       soc_pct       uint8   1         Node SoC percentage at time of ACK
```

## 2. Gateway SQLite Database Schema (`gateway/data/gateway.db`)

```sql
CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    node_id INTEGER NOT NULL,
    battery_mv INTEGER NOT NULL,
    load_w INTEGER NOT NULL,
    soc_pct INTEGER NOT NULL,
    flags INTEGER NOT NULL,
    temp_c INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    node_id INTEGER NOT NULL,
    command_id INTEGER NOT NULL,
    duration_s INTEGER NOT NULL,
    power_limit_w INTEGER NOT NULL,
    flags INTEGER NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dispatch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    grid_load_kw REAL NOT NULL,
    limit_kw REAL NOT NULL,
    gap_kw REAL NOT NULL,
    action TEXT NOT NULL,
    reason TEXT NOT NULL
);
```
