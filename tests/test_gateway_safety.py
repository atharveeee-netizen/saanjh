"""Safety supervisor and process-image registry."""
from datetime import datetime, timedelta, timezone

from gateway import service
from gateway.nodes import NodeState
from gateway.protocol import ACK_DONE, C_DISCHARGE, Ack, Command
from gateway.registry import NodeRegistry
from gateway.safety import SafetySupervisor

NOW = datetime(2026, 11, 15, 19, 0, tzinfo=timezone.utc)


def _node(**kwargs):
    base = dict(node_id=101, soc=90.0, load_w=300.0, online=True, last_seen=NOW)
    base.update(kwargs)
    return NodeState(**base)


def test_reserve_boundary_is_inclusive():
    sup = SafetySupervisor(reserve_soc=70.0)
    assert sup.check(_node(soc=70.0), NOW)[0] is False
    assert sup.check(_node(soc=70.1), NOW)[0] is True
    assert sup.check(_node(soc=90.0, opted_out=True), NOW)[1] == "opted out"
    assert sup.check(_node(soc=90.0, online=False), NOW)[1] == "offline"


def test_stale_telemetry_rejected():
    sup = SafetySupervisor(reserve_soc=70.0, stale_after_s=30)
    node = _node(last_seen=NOW - timedelta(seconds=31))
    ok, reason = sup.check(node, NOW)
    assert ok is False and "stale" in reason


def test_filter_keeps_only_safe_commands():
    sup = SafetySupervisor(reserve_soc=70.0)
    nodes = [_node(node_id=101, soc=90.0), _node(node_id=102, soc=69.0),
             _node(node_id=103, soc=90.0, opted_out=True)]
    commands = [Command(n.node_id, 0, n.node_id, 60, 300, C_DISCHARGE) for n in nodes]
    allowed, rejected = sup.filter_commands(commands, nodes, NOW)
    assert [c.node_id for c in allowed] == [101]
    assert {r["node_id"] for r in rejected} == {102, 103}


def test_expired_commands_detected():
    sup = SafetySupervisor(command_timeout_s=90)
    cmd = Command(101, 0, 7, 60, 300, C_DISCHARGE)
    assert sup.expired({7: (100.0, cmd)}, 200.0) == [(7, cmd)]
    assert sup.expired({7: (100.0, cmd)}, 120.0) == []


def test_shutdown_commands_are_cancels():
    class D:
        def _new_id(self):
            return 9
    sup = SafetySupervisor()
    cmds = sup.shutdown_commands([_node(node_id=101)], D())
    assert len(cmds) == 1 and cmds[0].cancel is True


def test_registry_updates_and_marks_stale():
    reg = NodeRegistry(stale_after_s=30)
    tel = type("T", (), {})()
    tel.node_id, tel.seq, tel.battery_mv, tel.load_w = 101, 1, 12300, 300
    tel.soc_pct, tel.flags, tel.temp_c = 90, 1, 31
    tel.opted_out = tel.relay_energised = False
    node = reg.update_from_telemetry(tel, NOW)
    assert node.online and node.last_seen == NOW and reg.relief_kw() == 0.0
    assert reg.mark_stale(NOW + timedelta(seconds=31)) == [node]
    assert node.online is False


class _Store:
    def __init__(self):
        self.acks = []
        self.events = []
        self.updates = []

    def ack(self, now, ack):
        self.acks.append(ack)

    def update_command_ack(self, *args):
        self.updates.append(args)

    def event(self, now, kind, detail):
        self.events.append((kind, detail))


def test_ack_done_counts_as_completion_not_refusal():
    rec = service.Recorder()
    store = _Store()
    ack = Ack(101, 2, 7, ACK_DONE, 70)
    service._handle_ack(ack, NOW, store, rec, {})
    assert rec.acks == 1
    assert rec.commands_completed == 1
    assert rec.commands_refused == 0
    assert rec.commands_accepted == 0
    assert store.events[0][0] == "command_done"
    assert rec.summary()["commands_completed"] == 1
