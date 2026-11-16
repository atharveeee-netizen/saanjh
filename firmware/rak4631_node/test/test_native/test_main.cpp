/*
 * Single native test binary for the portable node logic.
 *
 * PlatformIO's native runner compiles every source file under test/ into one
 * program, so the three domains share this one main() instead of each folder
 * defining its own. The test functions still live in their own files, and
 * Unity reports the source file for each result.
 */
#include <unity.h>

/* protocol */
void test_crc16_check_value();
void test_golden_telemetry_frame();
void test_golden_command_frame_decodes();
void test_golden_ack_frame();
void test_bad_crc_rejected();
void test_bad_magic_rejected();
void test_short_frame_rejected();
void test_wrong_type_rejected();
void test_cancel_flag_decodes();
void test_encoder_rejects_small_buffer();
void test_encoder_rejects_node_zero();
void test_status_names();

/* controller */
void test_accepts_above_reserve();
void test_refuses_exactly_at_reserve();
void test_refuses_below_reserve();
void test_refuses_opted_out_even_at_full_soc();
void test_refuses_without_sensor();
void test_wrong_node_ignored();
void test_cancel_opens_relay();
void test_duplicate_does_not_extend_deadline();
void test_expiry_stops_and_reports_completed();
void test_reserve_stop_during_tick();
void test_fault_stop_during_tick();
void test_opt_out_stops_immediately();
void test_duration_is_clamped();
void test_reserve_ok_boundary();

/* battery */
void test_ocv_curve_endpoints();
void test_ocv_curve_is_monotonic();
void test_boot_from_ocv();
void test_low_voltage_is_implausible();
void test_coulomb_counting_discharge();
void test_coulomb_counting_charge();
void test_rest_correction_moves_towards_ocv();
void test_soc_is_clamped();

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

  RUN_TEST(test_ocv_curve_endpoints);
  RUN_TEST(test_ocv_curve_is_monotonic);
  RUN_TEST(test_boot_from_ocv);
  RUN_TEST(test_low_voltage_is_implausible);
  RUN_TEST(test_coulomb_counting_discharge);
  RUN_TEST(test_coulomb_counting_charge);
  RUN_TEST(test_rest_correction_moves_towards_ocv);
  RUN_TEST(test_soc_is_clamped);

  return UNITY_END();
}
