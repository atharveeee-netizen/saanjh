#include <unity.h>

#include "config.h"
#include "node_controller.h"

using namespace saanjh;

namespace {
Command discharge(uint16_t id, uint16_t command_id, uint16_t duration_s,
                  uint16_t power_w) {
  Command cmd{};
  cmd.node_id = id;
  cmd.seq = command_id;
  cmd.command_id = command_id;
  cmd.duration_s = duration_s;
  cmd.power_limit_w = power_w;
  cmd.flags = C_DISCHARGE;
  return cmd;
}
}  // namespace

void test_accepts_above_reserve() {
  NodeController c(101, 70.0f, 100.0f);
  c.begin(0, 90.0f, false);
  TEST_ASSERT_EQUAL_UINT8(ACK_ACCEPTED,
                          c.apply_command(discharge(101, 1, 60, 300), 0, 90.0f,
                                          true));
  TEST_ASSERT_TRUE(c.relay_on());
  TEST_ASSERT_EQUAL_UINT32(60000, c.deadline_ms());
  TEST_ASSERT_EQUAL_UINT16(300, c.power_limit_w());
}

void test_refuses_exactly_at_reserve() {
  NodeController c(101, 70.0f, 100.0f);
  c.begin(0, 70.0f, false);
  TEST_ASSERT_EQUAL_UINT8(ACK_REFUSED_RESERVE,
                          c.apply_command(discharge(101, 1, 60, 300), 0, 70.0f,
                                          true));
  TEST_ASSERT_FALSE(c.relay_on());
}

void test_refuses_below_reserve() {
  NodeController c(101, 70.0f, 100.0f);
  c.begin(0, 69.9f, false);
  TEST_ASSERT_EQUAL_UINT8(ACK_REFUSED_RESERVE,
                          c.apply_command(discharge(101, 1, 60, 300), 0, 69.9f,
                                          true));
  TEST_ASSERT_FALSE(c.relay_on());
}

void test_refuses_opted_out_even_at_full_soc() {
  NodeController c(101, 70.0f, 100.0f);
  c.begin(0, 100.0f, true);
  TEST_ASSERT_EQUAL_UINT8(ACK_REFUSED_OPT_OUT,
                          c.apply_command(discharge(101, 1, 60, 300), 0, 100.0f,
                                          true));
  TEST_ASSERT_FALSE(c.relay_on());
}

void test_refuses_without_sensor() {
  NodeController c(101, 70.0f, 100.0f);
  c.begin(0, 100.0f, false);
  TEST_ASSERT_EQUAL_UINT8(ACK_ERROR,
                          c.apply_command(discharge(101, 1, 60, 300), 0, 100.0f,
                                          false));
  TEST_ASSERT_FALSE(c.relay_on());
}

void test_wrong_node_ignored() {
  NodeController c(101, 70.0f, 100.0f);
  c.begin(0, 100.0f, false);
  TEST_ASSERT_EQUAL_UINT8(ACK_ERROR,
                          c.apply_command(discharge(102, 1, 60, 300), 0, 100.0f,
                                          true));
  TEST_ASSERT_FALSE(c.relay_on());
}

void test_cancel_opens_relay() {
  NodeController c(101, 70.0f, 100.0f);
  c.begin(0, 100.0f, false);
  c.apply_command(discharge(101, 1, 60, 300), 0, 100.0f, true);
  Command cancel{};
  cancel.node_id = 101;
  cancel.seq = 2;
  cancel.command_id = 2;
  cancel.flags = C_CANCEL;
  TEST_ASSERT_EQUAL_UINT8(ACK_ACCEPTED, c.apply_command(cancel, 1000, 100.0f, true));
  TEST_ASSERT_FALSE(c.relay_on());
}

void test_duplicate_does_not_extend_deadline() {
  NodeController c(101, 70.0f, 100.0f);
  c.begin(0, 100.0f, false);
  c.apply_command(discharge(101, 7, 60, 300), 0, 100.0f, true);
  TEST_ASSERT_EQUAL_UINT8(ACK_ACCEPTED,
                          c.apply_command(discharge(101, 7, 600, 300), 30000,
                                          100.0f, true));
  TEST_ASSERT_EQUAL_UINT32(60000, c.deadline_ms());
}

void test_expiry_stops_and_reports_completed() {
  NodeController c(101, 70.0f, 100.0f);
  c.begin(0, 100.0f, false);
  c.apply_command(discharge(101, 1, 60, 300), 0, 100.0f, true);
  TEST_ASSERT_EQUAL(static_cast<int>(ControllerEvent::None),
                    static_cast<int>(c.tick(59999, 100.0f, true)));
  TEST_ASSERT_EQUAL(static_cast<int>(ControllerEvent::Completed),
                    static_cast<int>(c.tick(60000, 100.0f, true)));
  TEST_ASSERT_FALSE(c.relay_on());
}

void test_reserve_stop_during_tick() {
  NodeController c(101, 70.0f, 100.0f);
  c.begin(0, 90.0f, false);
  c.apply_command(discharge(101, 1, 600, 300), 0, 90.0f, true);
  TEST_ASSERT_EQUAL(static_cast<int>(ControllerEvent::ReserveStop),
                    static_cast<int>(c.tick(1000, 70.0f, true)));
  TEST_ASSERT_FALSE(c.relay_on());
}

void test_fault_stop_during_tick() {
  NodeController c(101, 70.0f, 100.0f);
  c.begin(0, 90.0f, false);
  c.apply_command(discharge(101, 1, 600, 300), 0, 90.0f, true);
  TEST_ASSERT_EQUAL(static_cast<int>(ControllerEvent::FaultStop),
                    static_cast<int>(c.tick(1000, 90.0f, false)));
  TEST_ASSERT_FALSE(c.relay_on());
}

void test_opt_out_stops_immediately() {
  NodeController c(101, 70.0f, 100.0f);
  c.begin(0, 90.0f, false);
  c.apply_command(discharge(101, 1, 600, 300), 0, 90.0f, true);
  TEST_ASSERT_TRUE(c.toggle_opt_out(1000));
  TEST_ASSERT_TRUE(c.opted_out());
  TEST_ASSERT_FALSE(c.relay_on());
  TEST_ASSERT_FALSE(c.toggle_opt_out(2000));
  TEST_ASSERT_FALSE(c.opted_out());
}

void test_duration_is_clamped() {
  NodeController c(101, 70.0f, 100.0f);
  c.begin(0, 100.0f, false);
  c.apply_command(discharge(101, 1, 7200, 300), 0, 100.0f, true);
  TEST_ASSERT_EQUAL_UINT32(
      static_cast<uint32_t>(SAANJH_COMMAND_MAX_DURATION_S) * 1000UL,
      c.deadline_ms());
}

void test_reserve_ok_boundary() {
  NodeController c(101, 70.0f, 100.0f);
  TEST_ASSERT_FALSE(c.reserve_ok(70.0f));
  TEST_ASSERT_TRUE(c.reserve_ok(70.001f));
}

extern "C" void setUp(void) {}
extern "C" void tearDown(void) {}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_accepts_above_reserve);
  RUN_TEST(test_refuses_exactly_at_reserve);
  RUN_TEST(test_refuses_below_reserve);
  RUN_TEST(test_refuses_opted_out_even_at_full_soc);
  RUN_TEST(test_refuses_without_sensor);
  RUN_TEST(test_wrong_node_ignored);
  RUN_TEST(test_cancel_opens_relay);
  RUN_TEST(test_duplicate_does_not_extend_deadline);
  RUN_TEST(test_expiry_stops_and_reports_completed);
  RUN_TEST(test_reserve_stop_during_tick);
  RUN_TEST(test_fault_stop_during_tick);
  RUN_TEST(test_opt_out_stops_immediately);
  RUN_TEST(test_duration_is_clamped);
  RUN_TEST(test_reserve_ok_boundary);
  return UNITY_END();
}
