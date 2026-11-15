#include "ina226.h"

#include "config.h"

namespace saanjh {
namespace {
constexpr uint8_t REG_CONFIG = 0x00;
constexpr uint8_t REG_BUS = 0x02;
constexpr uint8_t REG_POWER = 0x03;
constexpr uint8_t REG_CURRENT = 0x04;
constexpr uint8_t REG_CALIBRATION = 0x05;
constexpr uint8_t REG_MANUFACTURER = 0xFE;
}  // namespace

bool INA226::begin(TwoWire& wire, uint8_t address) {
  wire_ = &wire;
  address_ = address;
  fault_ = false;

  /* 16 averages, 1.1 ms bus + 1.1 ms shunt, continuous shunt and bus. */
  write16(REG_CONFIG, 0x4527);
  write16(REG_CALIBRATION, INA226_CALIBRATION);
  delay(2);

  const uint16_t mfr = read16(REG_MANUFACTURER);
  present_ = (mfr == 0x5449);
  fault_ = !present_;
  return present_;
}

uint16_t INA226::read16(uint8_t reg) {
  if (wire_ == nullptr) {
    fault_ = true;
    return 0;
  }
  wire_->beginTransmission(address_);
  wire_->write(reg);
  if (wire_->endTransmission(false) != 0) {
    fault_ = true;
    return 0;
  }
  if (wire_->requestFrom(static_cast<int>(address_), 2) != 2) {
    fault_ = true;
    return 0;
  }
  const uint16_t hi = wire_->read();
  const uint16_t lo = wire_->read();
  fault_ = false;
  return static_cast<uint16_t>((hi << 8) | lo);
}

void INA226::write16(uint8_t reg, uint16_t value) {
  if (wire_ == nullptr) {
    fault_ = true;
    return;
  }
  wire_->beginTransmission(address_);
  wire_->write(reg);
  wire_->write(static_cast<uint8_t>(value >> 8));
  wire_->write(static_cast<uint8_t>(value & 0xFF));
  if (wire_->endTransmission() != 0) {
    fault_ = true;
  }
}

float INA226::bus_voltage() {
  if (!present_) return 0.0f;
  return static_cast<float>(read16(REG_BUS)) * 0.00125f;
}

float INA226::current() {
  if (!present_) return 0.0f;
  return static_cast<float>(static_cast<int16_t>(read16(REG_CURRENT))) * 0.00100392f;
}

float INA226::power() {
  if (!present_) return 0.0f;
  return static_cast<float>(read16(REG_POWER)) * 0.025098f;
}

}  // namespace saanjh
