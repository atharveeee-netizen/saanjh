"""SAANJH DT gateway service: live LoRa mode and hardware-in-the-loop replay.

Replay (no radio needed, fully reproducible):

    python -m gateway.service --mode replay

Live (CM4 + SX1262 HAT, or a USB RAK4631 bridge):

    python -m gateway.service --mode live --transport spi

Both modes use the same packet codec, dispatcher, reserve rule and logger. Replay writes
``gateway/data/gateway.sqlite`` plus CSVs and ``replay_summary.json``; live writes the
same tables with real timestamps. The 154 kW feeder profile is the "grid" in both modes.

The replay path is deliberately end-to-end: gateway and node are two paired loopback
radios, commands are encoded and decoded, the node applies its own reserve rule, and the
gateway logs the ACK. Packet loss and latency are seeded draws in replay and measured
from the radio in live mode. The two are never mixed in the summary.
"""
import argparse
import csv
import json
import os
import random
import signal
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gateway import lora_driver, profile
from gateway.dispatch import GatewayDispatcher
from gateway.nodes import NodeState, default_nodes
from gateway.protocol import (ACK, ACK_ACCEPTED, ACK_DONE, C_CANCEL, TELEMETRY,
                              Ack, Command, decode_ack, decode_command,
                              decode_frame, decode_telemetry, encode_ack,
                              encode_command, encode_telemetry)
from gateway.registry import NodeRegistry
from gateway.safety import SafetySupervisor

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
IST = timezone(timedelta(hours=5, minutes=30))
DB_PATH = os.path.join(DATA_DIR, "gateway.sqlite")
STEP_S = 10.0
DISPATCH_S = 900.0


class Store:
    """SQLite + CSV evidence log. One row per packet, command and dispatch decision."""

    COMMAND_COLS = ["ts", "node_id", "command_id", "duration_s", "power_w", "delivered",
                    "latency_ms", "reason", "acked", "status"]

    def __init__(self, out_dir=None, reset=True):
        out_dir = out_dir or DATA_DIR
        os.makedirs(out_dir, exist_ok=True)
        self.path = os.path.join(out_dir, "gateway.sqlite")
        if reset and os.path.exists(self.path):
            os.remove(self.path)
        self.db = sqlite3.connect(self.path)
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS telemetry(
            ts TEXT, node_id INTEGER, seq INTEGER, battery_v REAL, soc_pct REAL,
            load_w REAL, reserve_ok INTEGER, opted_out INTEGER, relay INTEGER, temp_c REAL);
        CREATE TABLE IF NOT EXISTS commands(
            ts TEXT, node_id INTEGER, command_id INTEGER, duration_s INTEGER,
            power_w INTEGER, delivered INTEGER, latency_ms REAL, reason TEXT,
            acked INTEGER, status INTEGER);
        CREATE TABLE IF NOT EXISTS acks(
            ts TEXT, node_id INTEGER, command_id INTEGER, status INTEGER, soc_pct REAL);
        CREATE TABLE IF NOT EXISTS dispatch(
            ts TEXT, grid_load_kw REAL, limit_kw REAL, gap_kw REAL, commanded_kw REAL,
            expected_relief_kw REAL, residual_kw REAL, action TEXT, headline TEXT);
        CREATE TABLE IF NOT EXISTS grid(
            ts TEXT, grid_kw REAL, relief_kw REAL, net_kw REAL);
        CREATE TABLE IF NOT EXISTS events(ts TEXT, kind TEXT, detail TEXT);
        """)
        self.csv = {}
        for name, cols in {
            "telemetry": ["ts", "node_id", "seq", "battery_v", "soc_pct", "load_w",
                          "reserve_ok", "opted_out", "relay", "temp_c"],
            "commands": self.COMMAND_COLS,
            "acks": ["ts", "node_id", "command_id", "status", "soc_pct"],
            "dispatch": ["ts", "grid_load_kw", "limit_kw", "gap_kw", "commanded_kw",
                         "expected_relief_kw", "residual_kw", "action", "headline"],
            "grid": ["ts", "grid_kw", "relief_kw", "net_kw"],
            "events": ["ts", "kind", "detail"],
        }.items():
            f = open(os.path.join(out_dir, f"{name}.csv"), "w", newline="", encoding="utf-8")
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            self.csv[name] = (f, w)

    def _insert(self, table, row):
        cols = list(row)
        self.db.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES "
                        f"({','.join('?' for _ in cols)})", [row[c] for c in cols])
        f, w = self.csv[table]
        w.writerow(row)

    def telemetry(self, t, tel):
        self._insert("telemetry", {
            "ts": t.isoformat(), "node_id": tel.node_id, "seq": tel.seq,
            "battery_v": round(tel.battery_mv / 1000.0, 2), "soc_pct": tel.soc_pct,
            "load_w": tel.load_w, "reserve_ok": int(tel.reserve_ok),
            "opted_out": int(tel.opted_out), "relay": int(tel.relay_energised),
            "temp_c": tel.temp_c})

    def command(self, t, cmd, delivered, latency_ms, reason="", acked=0, status=None):
        self._insert("commands", {
            "ts": t.isoformat(), "node_id": cmd.node_id, "command_id": cmd.command_id,
            "duration_s": cmd.duration_s, "power_w": cmd.power_limit_w,
            "delivered": int(delivered), "latency_ms": latency_ms, "reason": reason,
            "acked": int(acked), "status": status})

    def update_command_ack(self, command_id, node_id, latency_ms, status):
        self.db.execute(
            "UPDATE commands SET acked=1, latency_ms=?, status=? "
            "WHERE command_id=? AND node_id=?",
            (latency_ms, status, command_id, node_id))

    def ack(self, t, ack):
        self._insert("acks", {"ts": t.isoformat(), "node_id": ack.node_id,
                              "command_id": ack.command_id, "status": ack.status,
                              "soc_pct": ack.soc_pct})

    def dispatch(self, t, decision, rec):
        self._insert("dispatch", {
            "ts": t.isoformat(), "grid_load_kw": round(decision.grid_load_kw, 2),
            "limit_kw": round(decision.limit_kw, 2), "gap_kw": round(decision.gap_kw, 2),
            "commanded_kw": round(decision.commanded_kw, 2),
            "expected_relief_kw": round(decision.expected_relief_kw, 2),
            "residual_kw": round(decision.residual_kw, 2),
            "action": rec["action"], "headline": rec["headline"]})

    def grid(self, t, grid_kw, relief_kw):
        self._insert("grid", {"ts": t.isoformat(), "grid_kw": round(grid_kw, 3),
                              "relief_kw": round(relief_kw, 3),
                              "net_kw": round(max(0.0, grid_kw - relief_kw), 3)})

    def event(self, t, kind, detail):
        self._insert("events", {"ts": t.isoformat(), "kind": kind, "detail": detail})

    def close(self):
        self.db.commit()
        for f, _ in self.csv.values():
            f.close()
        self.db.close()


class Recorder:
    """Delivery/latency statistics used for the evidence summary."""

    def __init__(self, dispatcher=None):
        self.telemetry_sent = 0
        self.telemetry_received = 0
        self.telemetry_lost = 0
        self.commands_sent = 0
        self.commands_delivered = 0
        self.command_losses = 0
        self.commands_accepted = 0
        self.commands_refused = 0
        self.commands_completed = 0
        self.acks = 0
        self.latencies = []
        self.soc_min = 100.0
        self.reserve_breaches = 0
        self.delivered_kwh = 0.0
        self.grid_before = []
        self.grid_after = []
        self.dispatch_events = 0
        self.commanded_kwh = 0.0
        self.accepted_kwh = 0.0
        self.limit_kw = dispatcher.limit_kw if dispatcher else None
        self.rating_kw = dispatcher.rating_kw if dispatcher else None

    def packet_success_pct(self):
        return (100.0 * self.telemetry_received / self.telemetry_sent
                if self.telemetry_sent else None)

    def command_success_pct(self):
        return (100.0 * self.commands_delivered / self.commands_sent
                if self.commands_sent else None)

    def command_ack_pct(self):
        return (100.0 * self.acks / self.commands_sent
                if self.commands_sent else None)

    def summary(self):
        lat = sorted(self.latencies)
        p95 = lat[min(len(lat) - 1, int(0.95 * len(lat)))] if lat else None
        before = max(self.grid_before) if self.grid_before else None
        after = max(self.grid_after) if self.grid_after else None
        rating = self.rating_kw or 95.0
        return {
            "telemetry_sent": self.telemetry_sent,
            "telemetry_received": self.telemetry_received,
            "telemetry_lost": self.telemetry_lost,
            "packet_success_pct": round(self.packet_success_pct(), 2) if self.packet_success_pct() is not None else None,
            "commands_sent": self.commands_sent,
            "commands_delivered": self.commands_delivered,
            "command_losses": self.command_losses,
            "command_success_pct": round(self.command_success_pct(), 2) if self.command_success_pct() is not None else None,
            "commands_accepted": self.commands_accepted,
            "commands_refused": self.commands_refused,
            "commands_completed": self.commands_completed,
            "acks_received": self.acks,
            "command_ack_pct": round(self.command_ack_pct(), 2) if self.command_ack_pct() is not None else None,
            "mean_command_latency_ms": round(sum(lat) / len(lat), 1) if lat else None,
            "p95_command_latency_ms": round(p95, 1) if p95 is not None else None,
            "soc_min_pct": round(self.soc_min, 1),
            "reserve_breaches": self.reserve_breaches,
            "battery_energy_delivered_kwh": round(self.delivered_kwh, 3),
            "dispatch_target_kw": round(self.limit_kw, 2) if self.limit_kw is not None else None,
            "transformer_rating_kw": round(rating, 2),
            "grid_peak_before_kw": round(before, 2) if before is not None else None,
            "grid_peak_after_kw": round(after, 2) if after is not None else None,
            "overload_minutes_before": int(sum(1 for x in self.grid_before if x > rating) * STEP_S / 60),
            "overload_minutes_after": int(sum(1 for x in self.grid_after if x > rating) * STEP_S / 60),
            "dispatch_events": self.dispatch_events,
            "commanded_kwh": round(self.commanded_kwh, 3),
            "accepted_kwh": round(self.accepted_kwh, 3),
        }


def _relief_kw(nodes):
    return sum(n.relief_w() for n in nodes if n.online and not n.opted_out) / 1000.0


def _apply_safety(decision, nodes, supervisor, now, store):
    """Remove any command the safety supervisor rejects and re-state the decision."""
    allowed, rejected = supervisor.filter_commands(decision.commands, nodes, now)
    if not rejected:
        return decision
    for item in rejected:
        store.event(now, "command_blocked",
                    f"Node {item['node_id']} blocked by safety supervisor: {item['reason']}")
    decision.commands = allowed
    decision.commanded_kw = sum(c.power_limit_w for c in allowed) / 1000.0
    decision.expected_relief_kw = decision.already_kw + decision.commanded_kw
    decision.residual_kw = max(0.0, decision.gap_kw - decision.expected_relief_kw)
    decision.reason = (f"{decision.reason} Safety supervisor blocked {len(rejected)} "
                       f"command(s).")
    return decision


def run_replay(args):
    prof = profile.load_profile()
    nodes = default_nodes(args.nodes, seed=args.seed)
    if len(nodes) >= 3:
        nodes[2].soc = 72.5           # deliberately near the reserve lock
    dispatcher = GatewayDispatcher(duration_min=args.duration_min)
    supervisor = SafetySupervisor(cfg=dispatcher.cfg)
    store = Store(reset=True)
    rec = Recorder(dispatcher)
    rng = random.Random(args.seed)
    gateway_link = lora_driver.LoopbackDriver("gateway")
    node_link = lora_driver.LoopbackDriver("node")
    gateway_link.pair(node_link)
    if args.start:
        start = datetime.fromisoformat(args.start)
        if start.tzinfo is None:
            start = start.replace(tzinfo=IST)
    else:
        start = datetime(2026, 5, 20, int(args.start_hour),
                         int(round((args.start_hour % 1) * 60)), tzinfo=IST)
    total_s = int(args.hours * 3600)
    seq = 0
    next_dispatch = 0.0
    opt_out_done = False
    event_log = []
    for t_s in range(0, total_s, int(STEP_S)):
        now = start + timedelta(seconds=t_s)
        hour = (now.hour + now.minute / 60 + now.second / 3600) % 24
        grid_kw = profile.at(prof, hour)

        # Household opt-out (push button) at 19:00 on the second node.
        if len(nodes) > 1 and not opt_out_done and abs(hour - args.opt_out_hour) < STEP_S / 3600.0:
            node = nodes[1]
            node.opted_out = True
            node._stop()
            opt_out_done = True
            store.event(now, "opt_out",
                        f"Node {node.node_id} pressed the household opt-out button; relay opened.")
            event_log.append({"ts": now.isoformat(), "kind": "opt_out", "node_id": node.node_id})
            print(f"[{now:%H:%M}] node {node.node_id} opted out")

        for node in nodes:
            node.tick(STEP_S)
            rec.soc_min = min(rec.soc_min, node.soc)
            if node.soc < node.reserve_soc - 0.05:
                rec.reserve_breaches += 1

        # Telemetry every 10 s. Packet loss is applied after encoding, so the codec and
        # the failure path are the same as live mode.
        for node in nodes:
            tel = node.telemetry()
            rec.telemetry_sent += 1
            if rng.random() < args.packet_loss:
                rec.telemetry_lost += 1
                continue
            node_link.send(encode_telemetry(tel))
            raw = gateway_link.recv(timeout_s=0)
            if raw is None:
                rec.telemetry_lost += 1
                continue
            try:
                decoded = decode_telemetry(decode_frame(raw))
            except ValueError:
                rec.telemetry_lost += 1
                continue
            rec.telemetry_received += 1
            # In replay the node is the source of truth; log the decoded packet.
            store.telemetry(now, decoded)

        # A fresh dispatch decision every 15 minutes.
        if t_s >= next_dispatch:
            next_dispatch += DISPATCH_S
            decision = dispatcher.plan(grid_kw, nodes, duration_min=args.duration_min)
            decision = _apply_safety(decision, nodes, supervisor, now, store)
            rec.dispatch_events += 1
            rec.commanded_kwh += decision.commanded_kw * args.duration_min / 60.0
            for cmd in decision.commands:
                seq = (seq + 1) & 0xFFFF
                cmd.seq = seq
                rec.commands_sent += 1
                if rng.random() < args.packet_loss:
                    rec.command_losses += 1
                    store.command(now, cmd, False, None, reason="command packet lost")
                    continue
                gateway_link.send(encode_command(cmd))
                raw = node_link.recv(timeout_s=0)
                if raw is None:
                    rec.command_losses += 1
                    store.command(now, cmd, False, None, reason="node did not receive command")
                    continue
                try:
                    got_cmd = decode_command(decode_frame(raw))
                except ValueError:
                    rec.command_losses += 1
                    store.command(now, cmd, False, None, reason="bad command frame")
                    continue
                node = next(n for n in nodes if n.node_id == got_cmd.node_id)
                status = node.apply_command(got_cmd)
                rec.commands_delivered += 1
                ack = Ack(node.node_id, got_cmd.seq, got_cmd.command_id, status,
                          int(round(node.soc)))
                node_link.send(encode_ack(ack))
                latency = rng.uniform(60, 240)
                ack_raw = gateway_link.recv(timeout_s=0)
                acked = 0
                if ack_raw is not None:
                    try:
                        got_ack = decode_ack(decode_frame(ack_raw))
                        rec.acks += 1
                        rec.latencies.append(latency)
                        store.ack(now, got_ack)
                        acked = 1
                    except ValueError:
                        pass
                store.command(now, cmd, True, round(latency, 1), reason="replay",
                              acked=acked, status=status)
                if status == ACK_ACCEPTED:
                    rec.commands_accepted += 1
                    rec.accepted_kwh += cmd.power_limit_w * cmd.duration_s / 3_600_000.0
                else:
                    rec.commands_refused += 1
                    store.event(
                        now, "command_refused",
                        f"Node {cmd.node_id} refused command {cmd.command_id}: "
                        f"status {status}, SoC {node.soc:.1f}%")
            store.dispatch(now, decision, dispatcher.discom_recommendation(decision))
            if decision.gap_kw > 0:
                store.event(now, "dispatch", decision.reason)
                print(f"[{now:%H:%M}] grid {grid_kw:.1f} kW, gap {decision.gap_kw:.1f} kW, "
                      f"commanded {decision.commanded_kw:.2f} kW, "
                      f"residual {decision.residual_kw:.1f} kW")

        # One grid sample per 10 s step, after commands have been applied.
        relief = _relief_kw(nodes)
        rec.grid_before.append(grid_kw)
        rec.grid_after.append(max(0.0, grid_kw - relief))
        store.grid(now, grid_kw, relief)
        rec.delivered_kwh = sum(n.discharged_kwh for n in nodes)

    for node in nodes:
        node._stop()
    supervisor.assert_safe_summary(rec.soc_min, rec.reserve_breaches)
    summary = rec.summary()
    summary.update({
        "mode": "replay",
        "label": "HARDWARE-IN-THE-LOOP REPLAY: simulated 154 kW feeder, packet path identical to live",
        "profile_peak_kw": max(r["load_kw"] for r in prof),
        "start": start.isoformat(),
        "hours": args.hours,
        "duration_min": args.duration_min,
        "packet_loss": args.packet_loss,
        "nodes": [n.summary() for n in nodes],
        "reserve_rule": "node refuses discharge below 70% SoC",
        "events": event_log,
        "note": ("Latency and packet loss in replay are seeded draws from the configured "
                 "values, not hardware measurements. Live mode measures them with the radio."),
    })
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, "replay_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, default=str)
    store.close()
    print(json.dumps(summary, indent=1))
    return summary


def _deliver_live(driver, cmd, now, store, rec, pending):
    """Send one command packet. Delivery is recorded now; the ACK arrives later."""
    rec.commands_sent += 1
    try:
        driver.send(encode_command(cmd))
    except Exception as exc:                       # radio timeout, unplugged HAT, ...
        rec.command_losses += 1
        store.command(now, cmd, False, None, reason=f"send failed: {exc}")
        store.event(now, "command_error", f"Node {cmd.node_id}: {exc}")
        return False
    rec.commands_delivered += 1
    pending[cmd.command_id] = (time.monotonic(), cmd)
    store.command(now, cmd, True, None, reason="live", acked=0)
    store.event(now, "command",
                f"Sent {cmd.power_limit_w} W for {cmd.duration_s} s to node {cmd.node_id}")
    return True


def _handle_ack(ack, now, store, rec, pending):
    entry = pending.pop(ack.command_id, None)
    latency = (time.monotonic() - entry[0]) * 1000.0 if entry else None
    store.ack(now, ack)
    rec.acks += 1
    if latency is not None:
        rec.latencies.append(latency)
        store.update_command_ack(ack.command_id, ack.node_id, round(latency, 1), ack.status)
    if ack.status == ACK_ACCEPTED:
        rec.commands_accepted += 1
        if entry:
            cmd = entry[1]
            rec.accepted_kwh += cmd.power_limit_w * cmd.duration_s / 3_600_000.0
    elif ack.status == ACK_DONE:
        rec.commands_completed += 1
        store.event(now, "command_done",
                    f"Node {ack.node_id} completed command {ack.command_id} "
                    f"at SoC {ack.soc_pct}%")
    else:
        rec.commands_refused += 1
        store.event(now, "command_refused",
                    f"Node {ack.node_id} refused command {ack.command_id}: "
                    f"status {ack.status}, SoC {ack.soc_pct}%")


def _write_live_summary(rec, registry, args, start, pending, complete):
    """Write live evidence atomically; a partial file is still honest evidence.

    During a run the dashboard needs a summary before the process exits, and a
    crashed run should leave the last snapshot rather than nothing. The final
    write marks the session closed.
    """
    summary = rec.summary()
    summary.update({
        "mode": "live",
        "label": "LIVE LoRa: measured on the gateway radio",
        "transport": args.transport,
        "start": start.isoformat(),
        "updated": datetime.now(IST).isoformat(),
        "session_open": not complete,
        "nodes": [n.summary() for n in registry.all()],
        "pending_commands_at_exit": len(pending) if complete else None,
        "note": ("Latency and packet success are measured from the radio, not simulated."
                 if complete else
                 "Session in progress: this summary refreshes every 10 s."),
    })
    path = os.path.join(DATA_DIR, "live_summary.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, default=str)
    try:
        os.replace(tmp, path)
    except OSError:
        # A dashboard read can briefly hold the old file on Windows; never let
        # evidence writing take the gateway down.
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=1, default=str)
    return summary


def run_live(args):
    if args.transport == "spi":
        driver = lora_driver.from_env("spi")
    elif args.transport == "serial":
        driver = lora_driver.from_env("serial")
    else:
        raise SystemExit("live mode needs --transport spi or serial")
    prof = profile.load_profile()
    dispatcher = GatewayDispatcher(duration_min=args.duration_min)
    supervisor = SafetySupervisor(cfg=dispatcher.cfg)
    registry = NodeRegistry(stale_after_s=30.0)
    store = Store(reset=True)
    rec = Recorder(dispatcher)
    start = datetime.now(IST)
    t0 = time.time()
    next_dispatch = 0.0
    next_sample = 0.0
    pending = {}
    stop = {"now": False}

    def _stop(*_):
        stop["now"] = True
    signal.signal(signal.SIGINT, _stop)

    print("Live gateway running. Ctrl+C to stop and open all relays.")
    while not stop["now"]:
        elapsed = (time.time() - t0) * args.speed
        if elapsed > args.hours * 3600:
            break
        now = datetime.now(IST)
        hour = (args.start_hour + elapsed / 3600.0) % 24
        grid_kw = profile.at(prof, hour)

        raw = driver.recv(timeout_s=0.2)
        if raw is not None:
            try:
                frame = decode_frame(raw)
            except ValueError as exc:
                store.event(now, "bad_frame", str(exc))
                frame = None
            if frame is not None and frame.msg_type == 1:       # TELEMETRY
                tel = decode_telemetry(frame)
                existing = registry.get(tel.node_id)
                prev_seq = existing.last_seq if existing else None
                node = registry.update_from_telemetry(
                    tel, now, capacity_wh=args.capacity_wh,
                    max_discharge_w=args.max_discharge_w)
                # Sequence gaps are the honest packet-loss measurement on a live link.
                if prev_seq is not None:
                    missed = (tel.seq - prev_seq - 1) % 0x10000
                    if 0 < missed < 1000:
                        rec.telemetry_lost += missed
                        rec.telemetry_sent += missed
                rec.telemetry_sent += 1
                rec.telemetry_received += 1
                rec.soc_min = min(rec.soc_min, node.soc)
                if node.soc < supervisor.reserve_soc - 0.05:
                    rec.reserve_breaches += 1
                store.telemetry(now, tel)
            elif frame is not None and frame.msg_type == 3:     # ACK
                _handle_ack(decode_ack(frame), now, store, rec, pending)

        # Snapshot only after this cycle's packets: the process image the
        # dispatcher sees must include the telemetry just decoded.
        nodes = registry.all()

        if elapsed >= next_dispatch:
            next_dispatch += DISPATCH_S
            online = [n for n in nodes if n.online]
            if online:
                decision = dispatcher.plan(grid_kw, online, duration_min=args.duration_min)
                decision = _apply_safety(decision, online, supervisor, now, store)
                rec.dispatch_events += 1
                rec.commanded_kwh += decision.commanded_kw * args.duration_min / 60.0
                for cmd in decision.commands:
                    _deliver_live(driver, cmd, now, store, rec, pending)
                store.dispatch(now, decision, dispatcher.discom_recommendation(decision))

        # Cancel commands whose ACK never arrived; the node's own expiry is the second layer.
        for command_id, cmd in supervisor.expired(pending, time.monotonic()):
            pending.pop(command_id, None)
            if cmd is not None:
                try:
                    driver.send(encode_command(supervisor.cancel(
                        next(n for n in nodes if n.node_id == cmd.node_id), dispatcher)))
                except Exception:
                    pass
            store.event(now, "command_expired",
                        f"Command {command_id} timed out without an ACK; cancel sent.")

        if elapsed >= next_sample:
            next_sample += STEP_S
            relief = _relief_kw(nodes)
            rec.grid_before.append(grid_kw)
            rec.grid_after.append(max(0.0, grid_kw - relief))
            store.grid(now, grid_kw, relief)
            rec.delivered_kwh = sum(n.discharged_kwh for n in nodes)
            _write_live_summary(rec, registry, args, start, pending, complete=False)

        # Mark silent nodes offline after 30 s without a packet.
        for n in registry.mark_stale(now):
            store.event(now, "node_stale",
                        f"Node {n.node_id} missed the 30 s telemetry window; relay opened.")

    # Fail safe: tell every node to open its relay before the process exits.
    for cmd in supervisor.shutdown_commands(registry.all(), dispatcher):
        try:
            driver.send(encode_command(cmd))
            store.event(datetime.now(IST), "shutdown",
                        f"Cancel sent to node {cmd.node_id}; relay returns to grid.")
        except Exception:
            pass
    summary = _write_live_summary(rec, registry, args, start, pending, complete=True)
    store.close()
    driver.close()
    print(json.dumps(summary, indent=1))
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=["replay", "live"], default="replay")
    ap.add_argument("--nodes", type=int, default=3)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--duration-min", type=int, default=45)
    ap.add_argument("--packet-loss", type=float, default=0.02)
    ap.add_argument("--start", default=None, help="ISO timestamp for replay")
    ap.add_argument("--start-hour", type=float, default=16.0)
    ap.add_argument("--hours", type=float, default=6.0)
    ap.add_argument("--opt-out-hour", type=float, default=19.0)
    ap.add_argument("--transport", choices=["spi", "serial"], default="spi")
    ap.add_argument("--speed", type=float, default=1.0, help="live clock multiplier")
    ap.add_argument("--capacity-wh", type=float, default=1800.0)
    ap.add_argument("--max-discharge-w", type=float, default=700.0)
    a = ap.parse_args(argv)
    if a.mode == "replay":
        return run_replay(a)
    return run_live(a)


if __name__ == "__main__":
    main()
