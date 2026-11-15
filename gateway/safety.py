"""Safety supervisor: the hard constraints above the dispatcher.

The dispatcher answers "what relief can we ask for?". This module answers "is it
safe to ask this node, right now?". It is deliberately independent of the
optimiser and is applied again at the node firmware, so a gateway bug cannot
take a household below its reserve or override an opt-out.

Rules:
  * offline or stale node -> no command;
  * opted-out node -> no command;
  * SoC at or below the reserve -> no discharge command;
  * command expiry -> cancel, relay returns to grid;
  * shutdown -> send cancel to every node.
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

from gateway.nodes import NodeState
from gateway.protocol import C_CANCEL, Command
from simulation.config import load_config


class SafetySupervisor:
    def __init__(self, cfg=None, reserve_soc: Optional[float] = None,
                 stale_after_s: float = 30.0, command_timeout_s: float = 90.0):
        self.cfg = cfg or load_config()
        self.reserve_soc = (float(reserve_soc) if reserve_soc is not None
                            else float(self.cfg["inverter_battery"]["reserve_soc"]) * 100.0)
        self.stale_after_s = stale_after_s
        self.command_timeout_s = command_timeout_s

    # ------------------------------------------------------------------ checks
    def check(self, node: NodeState, now: Optional[datetime] = None) -> tuple[bool, str]:
        if not node.online:
            return False, "offline"
        if node.opted_out:
            return False, "opted out"
        if node.soc <= self.reserve_soc + 1e-9:
            return False, f"SoC {node.soc:.1f}% at/below {self.reserve_soc:.0f}% reserve"
        if now is not None and node.last_seen is not None:
            age = (now - node.last_seen).total_seconds()
            if age > self.stale_after_s:
                return False, f"stale telemetry ({age:.0f} s)"
        return True, ""

    def filter_commands(self, commands: Iterable[Command], nodes: Iterable[NodeState],
                        now: Optional[datetime] = None) -> tuple[list[Command], list[dict]]:
        by_id = {n.node_id: n for n in nodes}
        allowed, rejected = [], []
        for cmd in commands:
            node = by_id.get(cmd.node_id)
            if node is None:
                rejected.append({"node_id": cmd.node_id, "reason": "unknown node"})
                continue
            ok, reason = self.check(node, now)
            if ok:
                allowed.append(cmd)
            else:
                rejected.append({"node_id": cmd.node_id, "reason": reason})
        return allowed, rejected

    # ------------------------------------------------------------------ timing
    def expired(self, pending: dict, now_monotonic: float) -> list[tuple[int, Command]]:
        """Return pending (command_id, command) entries older than the timeout."""
        stale = []
        for command_id, entry in list(pending.items()):
            sent_at = entry[0] if isinstance(entry, tuple) else entry
            cmd = entry[1] if isinstance(entry, tuple) else None
            if now_monotonic - sent_at > self.command_timeout_s:
                stale.append((command_id, cmd))
        return stale

    def cancel(self, node: NodeState, dispatcher) -> Command:
        return Command(node.node_id, 0, dispatcher._new_id(), 0, 0, C_CANCEL)

    def shutdown_commands(self, nodes: Iterable[NodeState], dispatcher) -> list[Command]:
        return [self.cancel(n, dispatcher) for n in nodes]

    def assert_safe_summary(self, soc_min_pct: float, reserve_breaches: int) -> None:
        if reserve_breaches:
            raise AssertionError(f"{reserve_breaches} reserve breaches recorded")
        if soc_min_pct < self.reserve_soc - 0.05:
            raise AssertionError(f"SoC minimum {soc_min_pct:.1f}% below reserve "
                                 f"{self.reserve_soc:.0f}%")
