#include <unity.h>

#include "battery.h"
#include "config.h"

using namespace saanjh;

void test_ocv_curve_endpoints() {
  TEST_ASSERT_EQUAL_FLOAT(0.0f, BatteryModel::soc_from_ocv(10000));
  TEST_ASSERT_EQUAL_FLOAT(100.0f, BatteryModel::soc_from_ocv(13400));
  TEST_ASSERT_EQUAL_FLOAT(70.0f, BatteryModel::soc_from_ocv(13200));
}

void test_ocv_curve_is_monotonic() {
  float previous = -1.0f;
  for (uint16_t mv = 10000; mv <= 13400; mv += 25) {
    const float soc = BatteryModel::soc_from_ocv(mv);
    TEST_ASSERT_TRUE(soc >= previous);
    previous = soc;
  }
}

void test_boot_from_ocv() {
  BatteryModel b(100.0f, SAANJH_BATTERY_MIN_MV, SAANJH_BATTERY_MAX_MV);
  b.begin(13300, 0);
  TEST_ASSERT_TRUE(b.plausible());
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 90.0f, b.soc_pct());
}

void test_low_voltage_is_implausible() {
  BatteryModel b(100.0f, SAANJH_BATTERY_MIN_MV, SAANJH_BATTERY_MAX_MV);
  b.begin(9000, 0);
  TEST_ASSERT_FALSE(b.plausible());
}

void test_coulomb_counting_discharge() {
  BatteryModel b(100.0f, SAANJH_BATTERY_MIN_MV, SAANJH_BATTERY_MAX_MV);
  b.begin(13400, 0);
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 100.0f, b.soc_pct());
  /* 50 W for 360 s = 5 Wh on a 100 Wh pack = 5 percentage points. */
  b.update(13400, 50.0f / 13.4f, 360000, true);
  TEST_ASSERT_FLOAT_WITHIN(0.1f, 95.0f, b.soc_pct());
}

void test_coulomb_counting_charge() {
  BatteryModel b(100.0f, SAANJH_BATTERY_MIN_MV, SAANJH_BATTERY_MAX_MV);
  b.begin(13100, 0);
  const float before = b.soc_pct();
  b.update(13100, -5.0f, 360000, false);
  TEST_ASSERT_TRUE(b.soc_pct() > before);
}

void test_rest_correction_moves_towards_ocv() {
  BatteryModel b(100.0f, SAANJH_BATTERY_MIN_MV, SAANJH_BATTERY_MAX_MV);
  b.begin(13100, 0);  /* 50% */
  b.update(13400, 0.0f, 120000, false);
  TEST_ASSERT_TRUE(b.soc_pct() > 50.0f);
  TEST_ASSERT_TRUE(b.soc_pct() < 100.0f);
}

void test_soc_is_clamped() {
  BatteryModel b(1.0f, SAANJH_BATTERY_MIN_MV, SAANJH_BATTERY_MAX_MV);
  b.begin(13400, 0);
  b.update(13400, 100.0f, 360000, true);
  TEST_ASSERT_TRUE(b.soc_pct() >= 0.0f);
  TEST_ASSERT_TRUE(b.soc_pct() <= 100.0f);
}
