/* Minimal INA226 driver: bus voltage, current and power. */
#pragma once

#include <Arduino.h>
#include <Wire.h>

namespace saanjh {

class INA226 {
 public:
  bool begin(TwoWire& wire, uint8_t address);
  bool present() const { return present_; }
  bool fault() const { return fault_; }

  float bus_voltage();   /* V */
  float current();       /* A, positive = discharge */
  float power();         /* W */

 private:
  uint16_t read16(uint8_t reg);
  void write16(uint8_t reg, uint16_t value);

  TwoWire* wire_ = nullptr;
  uint8_t address_ = 0x40;
  bool present_ = false;
  bool fault_ = false;
};

}  // namespace saanjh
