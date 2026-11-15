/*
 * SAANJH LoRa P2P framing - portable C++ core.
 *
 * Keep byte-for-byte parity with gateway/protocol.py:
 *   magic(2) | version(1) | msg_type(1) | node_id(2) | payload | crc16(2)
 * All multi-byte fields are little-endian. CRC-16/CCITT-FALSE.
 *
 * This file has no Arduino dependency so it can be unit-tested on a host.
 */
#pragma once

#include <stddef.h>
#include <stdint.h>

namespace saanjh {

constexpr uint8_t MAGIC0 = 'S';
constexpr uint8_t MAGIC1 = 'J';
constexpr uint8_t VERSION = 1;

constexpr uint8_t MSG_TELEMETRY = 0x01;
constexpr uint8_t MSG_COMMAND = 0x02;
constexpr uint8_t MSG_ACK = 0x03;

constexpr uint8_t F_RESERVE_OK = 1 << 0;
constexpr uint8_t F_OPTED_OUT = 1 << 1;
constexpr uint8_t F_RELAY_ENERGISED = 1 << 2;
constexpr uint8_t F_FAULT = 1 << 3;

/* Reserved telemetry bits (not interpreted by the gateway yet). */
constexpr uint16_t R_TEMP_VALID = 1 << 0;

constexpr uint8_t C_DISCHARGE = 1 << 0;
constexpr uint8_t C_CANCEL = 1 << 1;

constexpr uint8_t ACK_ACCEPTED = 0;
constexpr uint8_t ACK_REFUSED_RESERVE = 1;
constexpr uint8_t ACK_REFUSED_OPT_OUT = 2;
constexpr uint8_t ACK_DONE = 3;
constexpr uint8_t ACK_ERROR = 4;

constexpr size_t HEADER_LEN = 6;
constexpr size_t TELEMETRY_PAYLOAD_LEN = 11;
constexpr size_t COMMAND_PAYLOAD_LEN = 9;
constexpr size_t ACK_PAYLOAD_LEN = 6;
constexpr size_t MAX_FRAME = 32;

struct Telemetry {
  uint16_t node_id = 0;
  uint16_t seq = 0;
  uint16_t battery_mv = 0;
  uint16_t load_w = 0;
  uint8_t soc_pct = 0;
  uint8_t flags = 0;
  int8_t temp_c = 0;
  uint16_t reserved = 0;
};

struct Command {
  uint16_t node_id = 0;
  uint16_t seq = 0;
  uint16_t command_id = 0;
  uint16_t duration_s = 0;
  uint16_t power_limit_w = 0;
  uint8_t flags = 0;

  bool discharge() const { return (flags & C_DISCHARGE) && !cancel(); }
  bool cancel() const { return (flags & C_CANCEL) != 0; }
};

struct Ack {
  uint16_t node_id = 0;
  uint16_t seq = 0;
  uint16_t command_id = 0;
  uint8_t status = ACK_ERROR;
  uint8_t soc_pct = 0;
};

/* CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, no reflection, no xorout. */
uint16_t crc16(const uint8_t* data, size_t len);

/* Encoders return the number of bytes written, or 0 if the buffer is too small. */
size_t encode_telemetry(const Telemetry& t, uint8_t* out, size_t cap);
size_t encode_ack(const Ack& a, uint8_t* out, size_t cap);

/* Returns false and sets *error (if non-null) for short/malformed frames. */
bool decode_command(const uint8_t* raw, size_t len, Command& out,
                    const char** error = nullptr);

const char* status_name(uint8_t status);

}  // namespace saanjh
