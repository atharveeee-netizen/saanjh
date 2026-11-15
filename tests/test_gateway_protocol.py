"""Protocol parity, CRC and fail-safe node behaviour."""
import pytest

from gateway.nodes import NodeState
from gateway.protocol import (ACK_ACCEPTED, ACK_REFUSED_OPT_OUT,
                              ACK_REFUSED_RESERVE, C_DISCHARGE, Command,
                              F_RESERVE_OK, Telemetry, Ack, crc16, decode_ack,
                              decode_command, decode_frame, decode_telemetry,
                              encode_ack, encode_command, encode_telemetry)


def test_crc16_check_value():
    assert crc16(b"123456789") == 0x29B1


def test_golden_telemetry_frame():
    raw = encode_telemetry(Telemetry(101, 1, 12300, 350, 80, F_RESERVE_OK, 31, 0))
    assert raw.hex() == "534a0101650001000c305e0150011f00000e15"


def test_golden_command_frame():
    raw = encode_command(Command(101, 2, 7, 2700, 350, C_DISCHARGE))
    assert raw.hex() == "534a01026500020007008c0a5e0101f7a3"


def test_golden_ack_frame():
    raw = encode_ack(Ack(101, 2, 7, ACK_ACCEPTED, 80))
    assert raw.hex() == "534a01036500020007000050012a"


@pytest.mark.parametrize("msg", [
    Telemetry(101, 65535, 11800, 0, 0, 0, -10, 0),
    Telemetry(1, 0, 13600, 700, 100, 0b1111, 70, 1),
])
def test_telemetry_roundtrip(msg):
    assert decode_telemetry(decode_frame(encode_telemetry(msg))) == msg


def test_command_roundtrip():
    msg = Command(103, 9, 60000, 2700, 500, C_DISCHARGE)
    assert decode_command(decode_frame(encode_command(msg))) == msg


def test_ack_roundtrip():
    msg = Ack(102, 4, 99, ACK_REFUSED_RESERVE, 70)
    assert decode_ack(decode_frame(encode_ack(msg))) == msg


def test_bad_crc_rejected():
    raw = bytearray(encode_telemetry(Telemetry(101, 1, 12000, 300, 80, 0, 30, 0)))
    raw[-1] ^= 0xFF
    with pytest.raises(ValueError, match="bad CRC"):
        decode_frame(bytes(raw))


def test_bad_magic_rejected():
    raw = bytearray(encode_telemetry(Telemetry(101, 1, 12000, 300, 80, 0, 30, 0)))
    raw[0] = ord("X")
    with pytest.raises(ValueError, match="bad magic"):
        decode_frame(bytes(raw))


def test_frame_is_short():
    raw = encode_telemetry(Telemetry(101, 1, 12300, 350, 80, F_RESERVE_OK, 31, 0))
    assert len(raw) <= 32


def test_node_refuses_below_reserve():
    node = NodeState(node_id=101, soc=69.9)
    assert node.apply_command(Command(101, 1, 1, 60, 300, C_DISCHARGE)) == ACK_REFUSED_RESERVE
    assert node.relay is False


def test_node_refuses_when_opted_out_even_with_full_battery():
    node = NodeState(node_id=101, soc=100.0, opted_out=True)
    assert node.apply_command(Command(101, 1, 1, 60, 300, C_DISCHARGE)) == ACK_REFUSED_OPT_OUT
    assert node.relay is False


def test_node_discharge_stops_at_reserve():
    node = NodeState(node_id=101, soc=70.2, capacity_wh=100.0, load_w=700.0)
    node.apply_command(Command(101, 1, 1, 3600, 700, C_DISCHARGE))
    for _ in range(10):
        node.tick(60.0)
    assert node.soc >= 70.0 - 1e-9
    assert node.relay is False


def test_command_expiry_opens_relay():
    node = NodeState(node_id=101, soc=90.0)
    node.apply_command(Command(101, 1, 1, 10, 300, C_DISCHARGE))
    assert node.relay is True
    node.tick(11.0)
    assert node.relay is False
