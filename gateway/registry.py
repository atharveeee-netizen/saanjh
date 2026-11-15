"""Consistent process image for gateway telemetry.

The registry is the only place that turns decoded packets into the node state the
dispatcher sees. A cycle takes one snapshot, so a decision cannot be made from a
half-updated mixture of old and new packets.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from gateway.nodes import NodeState
from gateway.protocol import Telemetry


class NodeRegistry:
    def __init__(self, stale_after_s: float = 30.0):
        self.stale_after_s = stale_after_s
        self._nodes: dict[int, NodeState] = {}

    def __len__(self):
        return len(self._nodes)

    def get(self, node_id: int) -> Optional[NodeState]:
        return self._nodes.get(node_id)

    def all(self) -> list[NodeState]:
        return list(self._nodes.values())

    def update_from_telemetry(self, tel: Telemetry, now: datetime,
                              capacity_wh: float = 1800.0,
                              max_discharge_w: float = 700.0) -> NodeState:
        node = self._nodes.get(tel.node_id)
        if node is None:
            node = NodeState(
                node_id=tel.node_id,
                capacity_wh=capacity_wh,
                max_discharge_w=max_discharge_w,
                load_w=max(50, tel.load_w),
                soc=tel.soc_pct,
                opted_out=tel.opted_out,
                relay=tel.relay_energised,
            )
            self._nodes[tel.node_id] = node
        node.soc = float(tel.soc_pct)
        node.load_w = max(50, tel.load_w)
        node.opted_out = tel.opted_out
        node.relay = tel.relay_energised
        node.commanded_w = float(tel.load_w) if tel.relay_energised else 0.0
        node.temp_c = float(tel.temp_c)
        node.online = True
        node.last_seen = now
        node.last_seq = tel.seq
        return node

    def mark_stale(self, now: datetime) -> list[NodeState]:
        """Return nodes that just crossed the stale threshold."""
        newly_stale = []
        for node in self._nodes.values():
            if node.last_seen is None:
                continue
            if node.online and (now - node.last_seen).total_seconds() > self.stale_after_s:
                node.online = False
                node._stop()
                newly_stale.append(node)
        return newly_stale

    def snapshot(self, online_only: bool = False) -> list[NodeState]:
        nodes = list(self._nodes.values())
        return [n for n in nodes if n.online] if online_only else nodes

    def relief_kw(self) -> float:
        return sum(n.relief_w() for n in self._nodes.values()
                   if n.online and not n.opted_out) / 1000.0
