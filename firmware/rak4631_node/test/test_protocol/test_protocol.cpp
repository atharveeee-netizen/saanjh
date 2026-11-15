#include <string.h>

#include <unity.h>

#include "saanjh_protocol.h"

using namespace saanjh;

static void expect_hex(const uint8_t* data, size_t len, const char* hex) {
  char got[2 * MAX_FRAME + 1];
  TEST_ASSERT_TRUE(len * 2 <= sizeof(got));
  for (size_t i = 0; i < len; ++i) {
    snprintf(got + i * 2, 3, "%02x", data[i]);
  }
  TEST_ASSERT_EQUAL_STRING(hex, got);
}

void test_crc16_check_value() {
  const uint8_t data[] = {'1', '2', '3', '4', '5', '6', '7', '8', '9'};
  TEST_ASSERT_EQUAL_HEX16(0x29B1, crc16(data, sizeof(data)));
}

void test_golden_telemetry_frame() {
  Telemetry t{};
  t.node_id = 101;
  t.seq = 1;
  t.battery_mv = 12300;
  t.load_w = 350;
  t.soc_pct = 80;
  t.flags = F_RESERVE_OK;
  t.temp_c = 31;
  t.reserved = 0;
  uint8_t out[MAX_FRAME];
  const size_t n = encode_telemetry(t, out, sizeof(out));
  TEST_ASSERT_EQUAL_UINT32(19, n);
  expect_hex(out, n, "534a0101650001000c305e0150011f00000e15");
}

void test_golden_command_frame_decodes() {
  const uint8_t raw[] = {0x53, 0x4a, 0x01, 0x02, 0x65, 0x00, 0x02, 0x00,
                         0x07, 0x00, 0x8c, 0x0a, 0x5e, 0x01, 0x01, 0xf7,
                         0xa3};
  Command cmd;
  const char* err = "unset";
  TEST_ASSERT_TRUE(decode_command(raw, sizeof(raw), cmd, &err));
  TEST_ASSERT_NULL(err);
  TEST_ASSERT_EQUAL_UINT16(101, cmd.node_id);
  TEST_ASSERT_EQUAL_UINT16(2, cmd.seq);
  TEST_ASSERT_EQUAL_UINT16(7, cmd.command_id);
  TEST_ASSERT_EQUAL_UINT16(2700, cmd.duration_s);
  TEST_ASSERT_EQUAL_UINT16(350, cmd.power_limit_w);
  TEST_ASSERT_TRUE(cmd.discharge());
  TEST_ASSERT_FALSE(cmd.cancel());
}

void test_golden_ack_frame() {
  Ack a{};
  a.node_id = 101;
  a.seq = 2;
  a.command_id = 7;
  a.status = ACK_ACCEPTED;
  a.soc_pct = 80;
  uint8_t out[MAX_FRAME];
  const size_t n = encode_ack(a, out, sizeof(out));
  TEST_ASSERT_EQUAL_UINT32(14, n);
  expect_hex(out, n, "534a01036500020007000050012a");
}

void test_bad_crc_rejected() {
  uint8_t raw[] = {0x53, 0x4a, 0x01, 0x02, 0x65, 0x00, 0x02, 0x00,
                   0x07, 0x00, 0x8c, 0x0a, 0x5e, 0x01, 0x01, 0xf7,
                   0xa3};
  raw[16] ^= 0xFF;
  Command cmd;
  const char* err = nullptr;
  TEST_ASSERT_FALSE(decode_command(raw, sizeof(raw), cmd, &err));
  TEST_ASSERT_EQUAL_STRING("bad CRC", err);
}

void test_bad_magic_rejected() {
  uint8_t raw[] = {0x58, 0x4a, 0x01, 0x02, 0x65, 0x00, 0x02, 0x00,
                   0x07, 0x00, 0x8c, 0x0a, 0x5e, 0x01, 0x01, 0xf7,
                   0xa3};
  Command cmd;
  const char* err = nullptr;
  TEST_ASSERT_FALSE(decode_command(raw, sizeof(raw), cmd, &err));
  TEST_ASSERT_EQUAL_STRING("bad magic", err);
}

void test_short_frame_rejected() {
  const uint8_t raw[] = {0x53, 0x4a, 0x01, 0x02, 0x65, 0x00};
  Command cmd;
  const char* err = nullptr;
  TEST_ASSERT_FALSE(decode_command(raw, sizeof(raw), cmd, &err));
  TEST_ASSERT_EQUAL_STRING("frame too short", err);
}

void test_wrong_type_rejected() {
  Telemetry t{};
  t.node_id = 101;
  t.seq = 1;
  t.battery_mv = 12000;
  t.load_w = 300;
  t.soc_pct = 80;
  uint8_t out[MAX_FRAME];
  const size_t n = encode_telemetry(t, out, sizeof(out));
  Command cmd;
  const char* err = nullptr;
  TEST_ASSERT_FALSE(decode_command(out, n, cmd, &err));
  TEST_ASSERT_EQUAL_STRING("wrong message type", err);
}

void test_cancel_flag_decodes() {
  Command cmd{};
  cmd.node_id = 101;
  cmd.seq = 2;
  cmd.command_id = 9;
  cmd.duration_s = 0;
  cmd.power_limit_w = 0;
  cmd.flags = C_DISCHARGE | C_CANCEL;
  /* Hand-encode via a command frame is not exposed, so just assert the helpers. */
  TEST_ASSERT_TRUE(cmd.cancel());
  TEST_ASSERT_FALSE(cmd.discharge());
}

void test_encoder_rejects_small_buffer() {
  Telemetry t{};
  t.node_id = 101;
  uint8_t out[4];
  TEST_ASSERT_EQUAL_UINT32(0, encode_telemetry(t, out, sizeof(out)));
}

void test_encoder_rejects_node_zero() {
  Telemetry t{};
  t.node_id = 0;
  uint8_t out[MAX_FRAME];
  TEST_ASSERT_EQUAL_UINT32(0, encode_telemetry(t, out, sizeof(out)));
}

void test_status_names() {
  TEST_ASSERT_EQUAL_STRING("accepted", status_name(ACK_ACCEPTED));
  TEST_ASSERT_EQUAL_STRING("refused_reserve", status_name(ACK_REFUSED_RESERVE));
  TEST_ASSERT_EQUAL_STRING("refused_opt_out", status_name(ACK_REFUSED_OPT_OUT));
  TEST_ASSERT_EQUAL_STRING("done", status_name(ACK_DONE));
  TEST_ASSERT_EQUAL_STRING("error", status_name(ACK_ERROR));
}

extern "C" void setUp(void) {}
extern "C" void tearDown(void) {}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_crc16_check_value);
  RUN_TEST(test_golden_telemetry_frame);
  RUN_TEST(test_golden_command_frame_decodes);
  RUN_TEST(test_golden_ack_frame);
  RUN_TEST(test_bad_crc_rejected);
  RUN_TEST(test_bad_magic_rejected);
  RUN_TEST(test_short_frame_rejected);
  RUN_TEST(test_wrong_type_rejected);
  RUN_TEST(test_cancel_flag_decodes);
  RUN_TEST(test_encoder_rejects_small_buffer);
  RUN_TEST(test_encoder_rejects_node_zero);
  RUN_TEST(test_status_names);
  return UNITY_END();
}
