"""Gateway dispatch policy.

This is the same policy as ``simulation/dispatcher.py`` reduced to the information a
gateway actually has: the DT loading, the node telemetry, and the reserve rule. The
physical safety rules are enforced at the node as well, so a gateway bug cannot take a
household below its 70 % reserve.

Decision order:
    1. count relief already being delivered by energised relays;
    2. command idle nodes with SoC above the reserve, least-used first;
    3. cap each command at the home's measured load and the inverter rating;
    4. never promise more energy than the battery can deliver for the full duration;
    5. report the residual gap honestly for the DISCOM recommendation.
"""
from dataclasses import dataclass, field

from gateway.protocol import Command, C_DISCHARGE
from simulation.config import load_config


@dataclass
class DispatchDecision:
    grid_load_kw: float
    limit_kw: float
    gap_kw: float
    already_kw: float
    commanded_kw: float
    expected_relief_kw: float
    residual_kw: float
    commands: list = field(default_factory=list)
    reason: str = ""

    def summary(self):
        return {
            "grid_load_kw": round(self.grid_load_kw, 2),
            "limit_kw": round(self.limit_kw, 2),
            "gap_kw": round(self.gap_kw, 2),
            "already_relief_kw": round(self.already_kw, 2),
            "commanded_kw": round(self.commanded_kw, 2),
            "expected_relief_kw": round(self.expected_relief_kw, 2),
            "residual_overload_kw": round(self.residual_kw, 2),
            "n_commands": len(self.commands),
            "reason": self.reason,
        }


class GatewayDispatcher:
    def __init__(self, cfg=None, duration_min=45):
        self.cfg = cfg or load_config()
        inv = self.cfg["inverter_battery"]
        tr = self.cfg["transformer"]
        self.rating_kw = tr["rating_kva"] * self.cfg["electrical"]["power_factor"]
        self.target_pct = tr["dispatch_target_pct"]
        self.limit_kw = self.rating_kw * self.target_pct / 100.0
        self.reserve_soc = inv["reserve_soc"]
        self.inverter_kw = inv["inverter_kw"]
        self.duration_s = int(duration_min * 60)
        self.duration_min = duration_min
        self._next_id = 1

    def _new_id(self):
        cid = self._next_id
        self._next_id = (self._next_id % 65535) + 1
        return cid

    def plan(self, grid_load_kw, nodes, duration_min=None):
        duration_s = int((duration_min or self.duration_min) * 60)
        gap = max(0.0, float(grid_load_kw) - self.limit_kw)
        already = sum(n.load_w for n in nodes if n.relay and n.online and not n.opted_out) / 1000.0
        remaining = max(0.0, gap - already)
        commands = []
        if remaining > 1e-6:
            candidates = sorted(
                [n for n in nodes if n.online and not n.opted_out and not n.relay
                 and n.soc > self.reserve_soc + 0.1],
                key=lambda n: (n.discharged_kwh, -n.soc))
            for n in candidates:
                if remaining <= 1e-6:
                    break
                usable_kwh = max(0.0, n.soc - self.reserve_soc) / 100.0 * n.capacity_wh / 1000.0 * 0.9
                max_by_energy_w = usable_kwh * 3_600_000.0 / duration_s if duration_s else 0.0
                power_w = min(n.max_discharge_w, n.load_w, max_by_energy_w,
                              remaining * 1000.0)
                if power_w < 50:
                    continue
                cmd = Command(n.node_id, 0, self._new_id(), duration_s,
                              int(round(power_w)), C_DISCHARGE)
                commands.append(cmd)
                remaining -= power_w / 1000.0
        commanded = sum(c.power_limit_w for c in commands) / 1000.0
        relief = already + commanded
        decision = DispatchDecision(
            grid_load_kw=float(grid_load_kw), limit_kw=self.limit_kw, gap_kw=gap,
            already_kw=already, commanded_kw=commanded, expected_relief_kw=relief,
            residual_kw=max(0.0, gap - relief), commands=commands,
            reason=(f"Dispatch {commanded:.2f} kW for {self.duration_min} min across "
                    f"{len(commands)} nodes; {relief:.2f} kW expected relief, "
                    f"{max(0.0, gap - relief):.2f} kW residual."),
        )
        return decision

    def cancel_commands(self, nodes):
        return [Command(n.node_id, 0, self._new_id(), 0, 0, 0)
                for n in nodes if n.relay]

    def discom_recommendation(self, decision):
        if decision.gap_kw <= 1e-6:
            return {
                "action": "HOLD",
                "headline": "No dispatch needed",
                "detail": f"DT loading {decision.grid_load_kw:.1f} kW is below the "
                          f"{decision.limit_kw:.1f} kW target.",
                "dispatch_kw": 0.0, "duration_min": 0, "residual_kw": 0.0,
            }
        if decision.residual_kw <= 1e-6:
            return {
                "action": "DISPATCH",
                "headline": f"Dispatch {decision.commanded_kw:.1f} kW for {self.duration_min} min",
                "detail": f"Across {len(decision.commands)} nodes, keeping every battery at or "
                          f"above {self.reserve_soc*100:.0f}% reserve. Expected DT loading "
                          f"{decision.grid_load_kw - decision.expected_relief_kw:.1f} kW.",
                "dispatch_kw": round(decision.commanded_kw, 1),
                "duration_min": self.duration_min,
                "residual_kw": 0.0,
            }
        return {
            "action": "PARTIAL + ESCALATE",
            "headline": f"Dispatch {decision.commanded_kw:.1f} kW; {decision.residual_kw:.1f} kW still short",
            "detail": f"The enrolled nodes cannot close the gap. Keep the community battery "
                      f"for essential supply, curtail non-essential feeders, or call the "
                      f"contracted load-shedding block. Do not lower the 70% household reserve.",
            "dispatch_kw": round(decision.commanded_kw, 1),
            "duration_min": self.duration_min,
            "residual_kw": round(decision.residual_kw, 1),
        }
