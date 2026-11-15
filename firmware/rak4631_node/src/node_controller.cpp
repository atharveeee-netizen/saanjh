#include "node_controller.h"

namespace saanjh {

NodeController::NodeController(uint16_t node_id, float reserve_pct,
                               float capacity_wh)
    : node_id_(node_id),
      reserve_pct_(reserve_pct),
      capacity_wh_(capacity_wh) {}

void NodeController::begin(uint32_t now_ms, float soc_pct, bool opted_out) {
  (void)now_ms;
  (void)soc_pct;
  relay_on_ = false;
  opted_out_ = opted_out;
  last_command_id_ = 0;
  last_command_seq_ = 0;
  power_limit_w_ = 0;
  deadline_ms_ = 0;
}

void NodeController::stop() {
  relay_on_ = false;
  power_limit_w_ = 0;
  deadline_ms_ = 0;
}

uint8_t NodeController::apply_command(const Command& cmd, uint32_t now_ms,
                                      float soc_pct, bool sensor_ok) {
  if (cmd.node_id != node_id_) {
    return ACK_ERROR;
  }

  if (cmd.cancel()) {
    stop();
    last_command_id_ = cmd.command_id;
    last_command_seq_ = cmd.seq;
    return ACK_ACCEPTED;
  }

  if (!cmd.discharge()) {
    return ACK_ERROR;
  }
  if (opted_out_) {
    return ACK_REFUSED_OPT_OUT;
  }
  if (!sensor_ok) {
    return ACK_ERROR;
  }
  if (!reserve_ok(soc_pct)) {
    return ACK_REFUSED_RESERVE;
  }
  if (cmd.duration_s == 0 || cmd.power_limit_w == 0) {
    return ACK_ERROR;
  }

  /* A retransmission of the command already running must not extend its
   * deadline indefinitely. Re-ACK it and leave the timer alone. */
  if (relay_on_ && cmd.command_id == last_command_id_) {
    return ACK_ACCEPTED;
  }

  uint16_t duration = cmd.duration_s;
  if (duration > SAANJH_COMMAND_MAX_DURATION_S) {
    duration = SAANJH_COMMAND_MAX_DURATION_S;
  }
  relay_on_ = true;
  power_limit_w_ = cmd.power_limit_w;
  last_command_id_ = cmd.command_id;
  last_command_seq_ = cmd.seq;
  deadline_ms_ = now_ms + static_cast<uint32_t>(duration) * 1000UL;
  return ACK_ACCEPTED;
}

ControllerEvent NodeController::tick(uint32_t now_ms, float soc_pct,
                                     bool sensor_ok) {
  if (!relay_on_) {
    return ControllerEvent::None;
  }
  if (!sensor_ok) {
    stop();
    return ControllerEvent::FaultStop;
  }
  if (!reserve_ok(soc_pct)) {
    stop();
    return ControllerEvent::ReserveStop;
  }
  /* Wrap-safe: the signed difference stays positive until the deadline. */
  if (static_cast<int32_t>(now_ms - deadline_ms_) >= 0) {
    stop();
    return ControllerEvent::Completed;
  }
  return ControllerEvent::None;
}

bool NodeController::set_opted_out(bool value, uint32_t now_ms) {
  (void)now_ms;
  if (value == opted_out_) {
    return false;
  }
  opted_out_ = value;
  if (value) {
    stop();
  }
  return true;
}

bool NodeController::toggle_opt_out(uint32_t now_ms) {
  set_opted_out(!opted_out_, now_ms);
  return opted_out_;
}

}  // namespace saanjh
