/*
 * Battery state-of-charge for a 4S LiFePO4 pack.
 *
 * A voltage-only estimate is unusable on LiFePO4 because the curve is almost
 * flat between 20% and 80%. We therefore start from open-circuit voltage and
 * then coulomb-count using the INA226. When the pack is at rest we blend slowly
 * back towards the OCV estimate so long-term drift is bounded.
 *
 * This is a prototype estimator, not a BMS. The pack's own BMS remains the
 * last line of defence against over-discharge.
 */
#pragma once

#include <stdint.h>

namespace saanjh {

class BatteryModel {
 public:
  BatteryModel(float capacity_wh, uint16_t min_mv, uint16_t max_mv);

  void begin(uint16_t mv, uint32_t now_ms);
  void update(uint16_t mv, float current_a, uint32_t now_ms, bool under_load);

  float soc_pct() const { return soc_pct_; }
  bool plausible() const { return plausible_; }
  static float soc_from_ocv(uint16_t mv);

 private:
  float capacity_wh_;
  uint16_t min_mv_;
  uint16_t max_mv_;
  float soc_pct_ = 0.0f;
  bool plausible_ = true;
  uint32_t last_ms_ = 0;
  uint32_t rest_since_ms_ = 0;
};

}  // namespace saanjh
