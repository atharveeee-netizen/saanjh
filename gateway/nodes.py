"""Household node state and a replay model of the RAK4631 + relay + dummy load.

The replay model is deliberately the same shape as the firmware: a 12 V battery, an
INA226-style load measurement, a normally-closed relay that moves the dummy load from the
grid source to the battery, a 70 % reserve lock and a local opt-out button. It is used to
exercise the real packet codec, dispatcher and logger without hardware.
"""
from dataclasses import dataclass, field
from datetime import datetime
import random

from gateway.protocol import (ACK_ACCEPTED, ACK_DONE, ACK_REFUSED_OPT_OUT,
                              ACK_REFUSED_RESERVE, Command, F_OPTED_OUT,
                              F_RELAY_ENERGISED, F_RESERVE_OK, Telemetry)

RESERVE_SOC = 70.0


@dataclass
class NodeState:
    node_id: int
    capacity_wh: float = 1800.0          # 12 V, 150 Ah equivalent
    max_discharge_w: float = 700.0
    load_w: float = 350.0
    soc: float = 100.0
    reserve_soc: float = RESERVE_SOC
    opted_out: bool = False
    relay: bool = False
    temp_c: float = 31.0
    seq: int = 0
    command_id: int = 0
    command_remaining_s: float = 0.0
    commanded_w: float = 0.0
    discharged_kwh: float = 0.0
    last_ack: int = ACK_DONE
    online: bool = True
    last_seen: datetime = None
    last_seq: int = None
    rng: random.Random = field(default_factory=random.Random, repr=False)

    # ------------------------------------------------------------------ physics
    def battery_v(self) -> float:
        # 12 V lead-acid open-circuit approximation: 11.8 V empty, 13.6 V full.
        return 11.8 + 1.8 * max(0.0, min(100.0, self.soc)) / 100.0

    def _stop(self):
        self.relay = False
        self.command_remaining_s = 0.0
        self.commanded_w = 0.0

    def apply_command(self, cmd: Command) -> int:
        self.command_id = cmd.command_id
        if cmd.cancel:
            self._stop()
            self.last_ack = ACK_DONE
            return ACK_DONE
        if self.opted_out:
            self._stop()
            self.last_ack = ACK_REFUSED_OPT_OUT
            return ACK_REFUSED_OPT_OUT
        if self.soc < self.reserve_soc:
            self._stop()
            self.last_ack = ACK_REFUSED_RESERVE
            return ACK_REFUSED_RESERVE
        self.relay = True
        self.command_remaining_s = float(cmd.duration_s)
        # The node never draws more than the command asked for, even if the home load is higher.
        self.commanded_w = float(max(0, cmd.power_limit_w)) or self.load_w
        self.last_ack = ACK_ACCEPTED
        return ACK_ACCEPTED

    def relief_w(self) -> float:
        """Measured grid relief while the relay is in battery mode."""
        if not self.relay or self.opted_out:
            return 0.0
        return min(self.load_w, self.commanded_w) if self.commanded_w else self.load_w

    def tick(self, dt_s: float, grid_available: bool = True):
        if self.command_remaining_s > 0:
            self.command_remaining_s = max(0.0, self.command_remaining_s - dt_s)
            if self.command_remaining_s <= 0:
                self._stop()
                self.last_ack = ACK_DONE
        if self.relay:
            if self.soc <= self.reserve_soc + 1e-9:
                self._stop()
                self.last_ack = ACK_REFUSED_RESERVE
            else:
                energy_wh = self.relief_w() * dt_s / 3600.0
                dsoc = energy_wh / self.capacity_wh * 100.0 / 0.9  # discharge efficiency
                self.soc = max(self.reserve_soc, self.soc - dsoc)
                self.discharged_kwh += energy_wh / 1000.0
                if self.soc <= self.reserve_soc + 1e-9:
                    self._stop()
                    self.last_ack = ACK_DONE
        elif grid_available and self.soc < 100.0:
            energy_wh = 120.0 * dt_s / 3600.0 * 0.9      # 120 W charger
            self.soc = min(100.0, self.soc + energy_wh / self.capacity_wh * 100.0)
        # Slow thermal drift around ambient; DS18B20 reports this on hardware.
        self.temp_c += (30.5 - self.temp_c) * min(1.0, dt_s / 3600.0) + self.rng.uniform(-0.02, 0.02)

    # ------------------------------------------------------------------ packets
    def telemetry(self) -> Telemetry:
        self.seq = (self.seq + 1) & 0xFFFF
        flags = 0
        if self.soc >= self.reserve_soc:
            flags |= F_RESERVE_OK
        if self.opted_out:
            flags |= F_OPTED_OUT
        if self.relay:
            flags |= F_RELAY_ENERGISED
        return Telemetry(self.node_id, self.seq, int(round(self.battery_v() * 1000)),
                         int(round(self.load_w)), int(round(self.soc)), flags,
                         int(round(self.temp_c)), 0)

    def summary(self):
        return {
            "node_id": self.node_id, "soc_pct": round(self.soc, 1),
            "battery_v": round(self.battery_v(), 2), "load_w": round(self.load_w, 0),
            "relay_energised": self.relay, "relief_w": round(self.relief_w(), 0),
            "opted_out": self.opted_out, "reserve_soc": self.reserve_soc,
            "discharged_kwh": round(self.discharged_kwh, 3),
            "online": self.online, "temp_c": round(self.temp_c, 1),
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


def default_nodes(count=3, seed=7):
    rng = random.Random(seed)
    nodes = []
    for i in range(count):
        nodes.append(NodeState(node_id=101 + i, load_w=300 + 50 * i,
                               soc=96.0 - 2 * i, temp_c=30 + rng.random(),
                               rng=random.Random(seed * 100 + i)))
    return nodes


def energy_for_command(nodes, duration_s):
    """Battery energy (kWh) the nodes can actually deliver for a command."""
    kwh = 0.0
    for n in nodes:
        usable_pct = max(0.0, n.soc - n.reserve_soc)
        usable_kwh = usable_pct / 100.0 * n.capacity_wh / 1000.0
        kwh += min(n.load_w * duration_s / 3_600_000.0, usable_kwh)
    return kwh
