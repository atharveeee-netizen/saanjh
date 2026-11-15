#include "saanjh_protocol.h"

namespace saanjh {
namespace {

void put_u16(uint8_t* p, uint16_t v) {
  p[0] = static_cast<uint8_t>(v & 0xFF);
  p[1] = static_cast<uint8_t>((v >> 8) & 0xFF);
}

uint16_t get_u16(const uint8_t* p) {
  return static_cast<uint16_t>(p[0]) |
         static_cast<uint16_t>(static_cast<uint16_t>(p[1]) << 8);
}

size_t encode_frame(uint8_t msg_type, uint16_t node_id, const uint8_t* payload,
                    size_t payload_len, uint8_t* out, size_t cap) {
  const size_t total = HEADER_LEN + payload_len + 2;
  if (out == nullptr || total > cap || node_id == 0) {
    return 0;
  }
  out[0] = MAGIC0;
  out[1] = MAGIC1;
  out[2] = VERSION;
  out[3] = msg_type;
  put_u16(out + 4, node_id);
  for (size_t i = 0; i < payload_len; ++i) {
    out[HEADER_LEN + i] = payload[i];
  }
  const uint16_t crc = crc16(out, HEADER_LEN + payload_len);
  put_u16(out + HEADER_LEN + payload_len, crc);
  return total;
}

bool check_header(const uint8_t* raw, size_t len, uint8_t expected_type,
                  uint16_t& node_id, size_t& payload_len, const char** error) {
  auto fail = [&](const char* msg) {
    if (error != nullptr) *error = msg;
    return false;
  };
  if (raw == nullptr) return fail("null frame");
  if (len < HEADER_LEN + 2) return fail("frame too short");
  if (raw[0] != MAGIC0 || raw[1] != MAGIC1) return fail("bad magic");
  if (raw[2] != VERSION) return fail("unsupported version");
  if (raw[3] != expected_type) return fail("wrong message type");
  node_id = get_u16(raw + 4);
  if (node_id == 0) return fail("node id 0");
  const uint16_t want = static_cast<uint16_t>(raw[len - 2]) |
                        static_cast<uint16_t>(
                            static_cast<uint16_t>(raw[len - 1]) << 8);
  if (crc16(raw, len - 2) != want) return fail("bad CRC");
  payload_len = len - HEADER_LEN - 2;
  return true;
}

}  // namespace

uint16_t crc16(const uint8_t* data, size_t len) {
  uint16_t crc = 0xFFFF;
  for (size_t i = 0; i < len; ++i) {
    crc ^= static_cast<uint16_t>(data[i]) << 8;
    for (int bit = 0; bit < 8; ++bit) {
      if (crc & 0x8000) {
        crc = static_cast<uint16_t>((crc << 1) ^ 0x1021);
      } else {
        crc = static_cast<uint16_t>(crc << 1);
      }
    }
  }
  return crc;
}

size_t encode_telemetry(const Telemetry& t, uint8_t* out, size_t cap) {
  uint8_t payload[TELEMETRY_PAYLOAD_LEN];
  put_u16(payload + 0, t.seq);
  put_u16(payload + 2, t.battery_mv);
  put_u16(payload + 4, t.load_w);
  payload[6] = t.soc_pct;
  payload[7] = t.flags;
  payload[8] = static_cast<uint8_t>(t.temp_c);
  put_u16(payload + 9, t.reserved);
  return encode_frame(MSG_TELEMETRY, t.node_id, payload, sizeof(payload), out, cap);
}

size_t encode_ack(const Ack& a, uint8_t* out, size_t cap) {
  uint8_t payload[ACK_PAYLOAD_LEN];
  put_u16(payload + 0, a.seq);
  put_u16(payload + 2, a.command_id);
  payload[4] = a.status;
  payload[5] = a.soc_pct;
  return encode_frame(MSG_ACK, a.node_id, payload, sizeof(payload), out, cap);
}

bool decode_command(const uint8_t* raw, size_t len, Command& out,
                    const char** error) {
  uint16_t node_id = 0;
  size_t payload_len = 0;
  if (!check_header(raw, len, MSG_COMMAND, node_id, payload_len, error)) {
    return false;
  }
  if (payload_len < COMMAND_PAYLOAD_LEN) {
    if (error != nullptr) *error = "short command payload";
    return false;
  }
  const uint8_t* p = raw + HEADER_LEN;
  out.node_id = node_id;
  out.seq = get_u16(p + 0);
  out.command_id = get_u16(p + 2);
  out.duration_s = get_u16(p + 4);
  out.power_limit_w = get_u16(p + 6);
  out.flags = p[8];
  if (error != nullptr) *error = nullptr;
  return true;
}

const char* status_name(uint8_t status) {
  switch (status) {
    case ACK_ACCEPTED: return "accepted";
    case ACK_REFUSED_RESERVE: return "refused_reserve";
    case ACK_REFUSED_OPT_OUT: return "refused_opt_out";
    case ACK_DONE: return "done";
    case ACK_ERROR: return "error";
    default: return "unknown";
  }
}

}  // namespace saanjh
