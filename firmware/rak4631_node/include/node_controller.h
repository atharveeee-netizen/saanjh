/*
 * Local safety controller. The gateway also enforces these rules, but the node
 * must survive a gateway bug, a lost cancel and a radio outage on its own.
 */
#pragma once

#include <stdint.h>

#include "config.h"
#include "saanjh_protocol.h"

namespace saanjh {

enum class ControllerEvent : uint8_t {
  None = 0,
  Completed,
  ReserveStop,
  OptOut,
  FaultStop,
};

class NodeController {
 public:
  NodeController(uint16_t node_id, float reserve_pct, float capacity_wh);

  void begin(uint32_t now_ms, float soc_pct, bool opted_out);

  /* Apply a command addressed to this node. Returns the ACK status to send. */
  uint8_t apply_command(const Command& cmd, uint32_t now_ms, float soc_pct,
                        bool sensor_ok);

  /* Enforce duration, reserve and sensor health. Call every loop. */
  ControllerEvent tick(uint32_t now_ms, float soc_pct, bool sensor_ok);

  /* Returns the new opt-out state. Stops the relay immediately on opt-out. */
  bool toggle_opt_out(uint32_t now_ms);
  bool set_opted_out(bool value, uint32_t now_ms);

  bool relay_on() const { return relay_on_; }
  bool opted_out() const { return opted_out_; }
  bool reserve_ok(float soc_pct) const { return soc_pct > reserve_pct_ + 1e-4f; }
  uint16_t node_id() const { return node_id_; }
  uint16_t last_command_id() const { return last_command_id_; }
  uint16_t last_command_seq() const { return last_command_seq_; }
  uint32_t deadline_ms() const { return deadline_ms_; }
  uint16_t power_limit_w() const { return power_limit_w_; }
  float reserve_pct() const { return reserve_pct_; }

 private:
  void stop();

  uint16_t node_id_;
  float reserve_pct_;
  float capacity_wh_;
  bool relay_on_ = false;
  bool opted_out_ = false;
  uint16_t last_command_id_ = 0;
  uint16_t last_command_seq_ = 0;
  uint16_t power_limit_w_ = 0;
  uint32_t deadline_ms_ = 0;
};

}  // namespace saanjh
