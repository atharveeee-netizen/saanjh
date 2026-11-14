"""SAANJH LoRa P2P packet protocol (firmware <-> gateway).

One frame == one LoRa payload. Multi-byte fields are little-endian. A frame is:

    magic(2) | version(1) | msg_type(1) | node_id(2) | payload(n) | crc16(2)

CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF) covers everything before the CRC. The
same layout is implemented in ``firmware/rak4631_node/src/main.cpp``; keep them in sync.

Messages
    0x01 TELEMETRY  node -> gateway, every ~10 s
    0x02 COMMAND    gateway -> node, discharge/cancel
    0x03 ACK        node -> gateway, accepted/refused/done

The radio is LoRa P2P (no LoRaWAN join, no network server). Frames are short (< 32 B) so
they fit SF9/125 kHz with a 10 % duty-cycle budget.
"""
from dataclasses import dataclass, asdict
import struct

MAGIC = b"SJ"
VERSION = 1
TELEMETRY = 0x01
COMMAND = 0x02
ACK = 0x03

# Telemetry flags
F_RESERVE_OK = 1 << 0
F_OPTED_OUT = 1 << 1
F_RELAY_ENERGISED = 1 << 2
F_FAULT = 1 << 3

# Command flags
C_DISCHARGE = 1 << 0
C_CANCEL = 1 << 1

# ACK status
ACK_ACCEPTED = 0
ACK_REFUSED_RESERVE = 1
ACK_REFUSED_OPT_OUT = 2
ACK_DONE = 3
ACK_ERROR = 4

HEADER = struct.Struct("<2sBBH")
TELEMETRY_PAYLOAD = struct.Struct("<HHHBBbH")   # seq, mV, W, soc%, flags, temp C, reserved
COMMAND_PAYLOAD = struct.Struct("<HHHHB")       # seq, command id, duration s, limit W, flags
ACK_PAYLOAD = struct.Struct("<HHBB")            # seq, command id, status, soc%


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


@dataclass
class Telemetry:
    node_id: int
    seq: int
    battery_mv: int
    load_w: int
    soc_pct: int
    flags: int = 0
    temp_c: int = 25
    reserved: int = 0

    @property
    def reserve_ok(self) -> bool:
        return bool(self.flags & F_RESERVE_OK)

    @property
    def opted_out(self) -> bool:
        return bool(self.flags & F_OPTED_OUT)

    @property
    def relay_energised(self) -> bool:
        return bool(self.flags & F_RELAY_ENERGISED)

    @property
    def fault(self) -> bool:
        return bool(self.flags & F_FAULT)

    def to_dict(self):
        d = asdict(self)
        d.update(reserve_ok=self.reserve_ok, opted_out=self.opted_out,
                 relay_energised=self.relay_energised, fault=self.fault)
        return d


@dataclass
class Command:
    node_id: int
    seq: int
    command_id: int
    duration_s: int
    power_limit_w: int
    flags: int = C_DISCHARGE

    @property
    def discharge(self) -> bool:
        return bool(self.flags & C_DISCHARGE) and not self.cancel

    @property
    def cancel(self) -> bool:
        return bool(self.flags & C_CANCEL)

    def to_dict(self):
        d = asdict(self)
        d.update(discharge=self.discharge, cancel=self.cancel)
        return d


@dataclass
class Ack:
    node_id: int
    seq: int
    command_id: int
    status: int
    soc_pct: int

    def to_dict(self):
        return asdict(self)


@dataclass
class Frame:
    msg_type: int
    node_id: int
    payload: bytes
    version: int = VERSION


def encode_frame(msg_type: int, node_id: int, payload: bytes) -> bytes:
    if not 0 < node_id < 0x10000:
        raise ValueError("node_id must be 1..65535")
    body = HEADER.pack(MAGIC, VERSION, msg_type, node_id) + payload
    return body + struct.pack("<H", crc16(body))


def decode_frame(raw: bytes) -> Frame:
    if len(raw) < HEADER.size + 2:
        raise ValueError("frame too short")
    magic, version, msg_type, node_id = HEADER.unpack_from(raw)
    if magic != MAGIC:
        raise ValueError("bad magic")
    if version != VERSION:
        raise ValueError(f"unsupported version {version}")
    body, crc = raw[:-2], struct.unpack("<H", raw[-2:])[0]
    if crc16(body) != crc:
        raise ValueError("bad CRC")
    if msg_type not in (TELEMETRY, COMMAND, ACK):
        raise ValueError(f"unknown message type {msg_type}")
    return Frame(msg_type, node_id, raw[HEADER.size:-2], version)


def encode_telemetry(t: Telemetry) -> bytes:
    flags = t.flags
    return encode_frame(TELEMETRY, t.node_id, TELEMETRY_PAYLOAD.pack(
        t.seq, t.battery_mv, t.load_w, t.soc_pct, flags, max(-128, min(127, t.temp_c)),
        t.reserved))


def decode_telemetry(frame: Frame) -> Telemetry:
    if frame.msg_type != TELEMETRY:
        raise ValueError("not a telemetry frame")
    seq, mv, watts, soc, flags, temp, reserved = TELEMETRY_PAYLOAD.unpack(frame.payload[:TELEMETRY_PAYLOAD.size])
    return Telemetry(frame.node_id, seq, mv, watts, soc, flags, temp, reserved)


def encode_command(c: Command) -> bytes:
    return encode_frame(COMMAND, c.node_id, COMMAND_PAYLOAD.pack(
        c.seq, c.command_id, c.duration_s, c.power_limit_w, c.flags))


def decode_command(frame: Frame) -> Command:
    if frame.msg_type != COMMAND:
        raise ValueError("not a command frame")
    seq, cid, duration, limit, flags = COMMAND_PAYLOAD.unpack(frame.payload[:COMMAND_PAYLOAD.size])
    return Command(frame.node_id, seq, cid, duration, limit, flags)


def encode_ack(a: Ack) -> bytes:
    return encode_frame(ACK, a.node_id, ACK_PAYLOAD.pack(a.seq, a.command_id, a.status, a.soc_pct))


def decode_ack(frame: Frame) -> Ack:
    if frame.msg_type != ACK:
        raise ValueError("not an ack frame")
    seq, cid, status, soc = ACK_PAYLOAD.unpack(frame.payload[:ACK_PAYLOAD.size])
    return Ack(frame.node_id, seq, cid, status, soc)
