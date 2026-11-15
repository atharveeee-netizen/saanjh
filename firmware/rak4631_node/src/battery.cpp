#include "battery.h"

#include <math.h>

namespace saanjh {
namespace {

struct Point {
  uint16_t mv;
  float soc;
};

/* 4S LiFePO4 open-circuit voltage, rested. Deliberately conservative around
 * the 70% policy line: 13.20 V reads as 70%. */
constexpr Point kOcv[] = {
    {10000, 0.0f},   {11800, 3.0f},   {12500, 8.0f},  {12800, 15.0f},
    {13000, 30.0f},  {13100, 50.0f},  {13200, 70.0f}, {13300, 90.0f},
    {13400, 100.0f},
};

float clampf(float v, float lo, float hi) {
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

}  // namespace

BatteryModel::BatteryModel(float capacity_wh, uint16_t min_mv, uint16_t max_mv)
    : capacity_wh_(capacity_wh), min_mv_(min_mv), max_mv_(max_mv) {}

void BatteryModel::begin(uint16_t mv, uint32_t now_ms) {
  plausible_ = mv >= min_mv_ && mv <= max_mv_;
  soc_pct_ = plausible_ ? soc_from_ocv(mv) : 0.0f;
  last_ms_ = now_ms;
  rest_since_ms_ = now_ms;
}

void BatteryModel::update(uint16_t mv, float current_a, uint32_t now_ms,
                          bool under_load) {
  if (mv < min_mv_ || mv > max_mv_) {
    plausible_ = false;
    soc_pct_ = 0.0f;
    last_ms_ = now_ms;
    return;
  }
  plausible_ = true;

  const uint32_t dt_ms = now_ms - last_ms_;
  last_ms_ = now_ms;

  /* Ignore absurd gaps (e.g. a long blocking flash write or a sleep cycle)
   * rather than integrating a fictitious hour of load from one sample. */
  if (dt_ms == 0 || dt_ms > 600000UL) {
    return;
  }

  const float dt_h = static_cast<float>(dt_ms) / 3600000.0f;
  const float watts = (static_cast<float>(mv) / 1000.0f) * current_a;
  soc_pct_ -= (watts * dt_h / capacity_wh_) * 100.0f;
  soc_pct_ = clampf(soc_pct_, 0.0f, 100.0f);

  const bool at_rest = !under_load && fabsf(current_a) < 0.05f;
  if (!at_rest) {
    rest_since_ms_ = now_ms;
    return;
  }
  if (now_ms - rest_since_ms_ < 60000UL) {
    return;
  }

  /* Slow OCV correction: at most 2% per update, ~70% convergence in 10 min. */
  const float alpha = fminf(0.02f, (static_cast<float>(dt_ms) / 1000.0f) * 0.002f);
  soc_pct_ += (soc_from_ocv(mv) - soc_pct_) * alpha;
  soc_pct_ = clampf(soc_pct_, 0.0f, 100.0f);
}

float BatteryModel::soc_from_ocv(uint16_t mv) {
  if (mv <= kOcv[0].mv) return 0.0f;
  constexpr size_t n = sizeof(kOcv) / sizeof(kOcv[0]);
  if (mv >= kOcv[n - 1].mv) return 100.0f;
  for (size_t i = 1; i < n; ++i) {
    if (mv <= kOcv[i].mv) {
      const float span = static_cast<float>(kOcv[i].mv - kOcv[i - 1].mv);
      const float frac = static_cast<float>(mv - kOcv[i - 1].mv) / span;
      return kOcv[i - 1].soc + frac * (kOcv[i].soc - kOcv[i - 1].soc);
    }
  }
  return 100.0f;
}

}  // namespace saanjh
