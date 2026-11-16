"""Live gateway path with a fake radio: telemetry in, command out, ACK in, evidence out.

The replay test covers the simulated node. This test covers the live loop itself:
the serial/SPI boundary is replaced by a fake driver, so the code that decodes
telemetry, plans a command, sends it, handles the ACK and writes the live summary
runs exactly as it does on the bench.
"""
import json
import sqlite3
import time
from types import SimpleNamespace

from gateway import protocol, service


class FakeRadio:
    """Returns one telemetry frame, acknowledges each discharge command once."""

    def __init__(self):
        self.sent = []
        self.acked = set()
        self.closed = False
        self.telemetry = protocol.encode_telemetry(
            protocol.Telemetry(
                node_id=101,
                seq=1,
                battery_mv=13300,
                load_w=300,
                soc_pct=80,
                flags=protocol.F_RESERVE_OK,
                temp_c=29,
            )
        )
        self.first = True

    def recv(self, timeout_s=0.2):
        time.sleep(min(timeout_s, 0.02))  # keep the test loop from spinning
        if self.first:
            self.first = False
            return self.telemetry
        for raw in self.sent:
            frame = protocol.decode_frame(raw)
            if frame.msg_type != protocol.COMMAND:
                continue
            cmd = protocol.decode_command(frame)
            if cmd.cancel or cmd.command_id in self.acked:
                continue
            self.acked.add(cmd.command_id)
            return protocol.encode_ack(
                protocol.Ack(
                    node_id=cmd.node_id,
                    seq=1,
                    command_id=cmd.command_id,
                    status=protocol.ACK_ACCEPTED,
                    soc_pct=80,
                )
            )
        return None

    def send(self, raw):
        self.sent.append(raw)

    def close(self):
        self.closed = True


def test_live_mode_logs_telemetry_command_and_ack(tmp_path, monkeypatch, capsys):
    radio = FakeRadio()
    monkeypatch.setattr(service, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(service.lora_driver, "from_env", lambda transport: radio)
    monkeypatch.setattr(service.signal, "signal", lambda *args: None)

    args = SimpleNamespace(
        transport="serial",
        duration_min=45,
        start_hour=19.4,
        hours=0.001,
        speed=1.0,
        capacity_wh=1800.0,
        max_discharge_w=700.0,
    )
    summary = service.run_live(args)
    capsys.readouterr()

    assert summary["mode"] == "live"
    assert summary["transport"] == "serial"
    assert summary["telemetry_received"] == 1
    assert summary["packet_success_pct"] == 100.0
    assert summary["commands_sent"] >= 1
    assert summary["commands_delivered"] == summary["commands_sent"]
    assert summary["acks_received"] >= 1
    assert summary["commands_accepted"] >= 1
    assert summary["soc_min_pct"] == 80.0
    assert summary["reserve_breaches"] == 0
    assert radio.closed

    # The final transmissions are shutdown cancels, so no node is left energised.
    last = protocol.decode_command(protocol.decode_frame(radio.sent[-1]))
    assert last.node_id == 101 and last.cancel

    written = json.loads((tmp_path / "live_summary.json").read_text(encoding="utf-8"))
    assert written["mode"] == "live"
    assert written["commands_accepted"] >= 1

    db = sqlite3.connect(tmp_path / "gateway.sqlite")
    assert db.execute("select count(*) from telemetry").fetchone()[0] == 1
    assert db.execute("select count(*) from commands").fetchone()[0] >= 1
    assert db.execute("select count(*) from acks").fetchone()[0] >= 1
    db.close()
