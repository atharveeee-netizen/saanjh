"""End-to-end replay: codec, dispatcher, safety supervisor, command/ACK and evidence."""
from types import SimpleNamespace

from gateway import service


def test_replay_produces_commands_and_respects_reserve(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(service, "DATA_DIR", str(tmp_path))
    args = SimpleNamespace(
        nodes=3, seed=7, duration_min=45, packet_loss=0.0,
        start=None, start_hour=19.4, hours=0.25, opt_out_hour=19.5,
    )
    summary = service.run_replay(args)
    capsys.readouterr()

    assert summary["mode"] == "replay"
    assert summary["telemetry_sent"] == summary["telemetry_received"] == 270
    assert summary["commands_sent"] > 0
    assert summary["commands_delivered"] == summary["commands_sent"]
    assert summary["commands_accepted"] > 0
    assert summary["reserve_breaches"] == 0
    assert summary["soc_min_pct"] >= 70.0
    assert summary["grid_peak_before_kw"] == 154.0
    assert summary["grid_peak_after_kw"] <= summary["grid_peak_before_kw"]
    assert any(ev["kind"] == "opt_out" for ev in summary["events"])
    assert (tmp_path / "gateway.sqlite").exists()
    assert (tmp_path / "replay_summary.json").exists()
    assert (tmp_path / "telemetry.csv").exists()
