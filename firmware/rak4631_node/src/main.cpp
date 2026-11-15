/*
 * SAANJH RAK4631 node firmware.
 *
 * SAFETY MODEL
 *   - The relay is de-energised (load on the 12 V "grid" supply) at reset and
 *     whenever the node is unsure: no INA226, no radio, stale command, or SoC at
 *     or below the 70% reserve.
 *   - The gateway can request discharge, but the node independently refuses at
 *     or below the reserve and on opt-out, and stops on command expiry.
 *   - Opt-out is persisted across power cycles in the internal littlefs.
 *
 * This is a <=12 V DC bench prototype. It does not switch mains.
 */
#include <Arduino.h>
#include <SPI.h>
#include <Wire.h>
#include <math.h>
#include <stddef.h>

#include <RadioLib.h>

/* config.h must come before the persistence guard below, because it is what
 * defines SAANJH_PERSIST_OPT_OUT. */
#include "config.h"

#if SAANJH_PERSIST_OPT_OUT
#include <Adafruit_LittleFS.h>
#include <InternalFileSystem.h>
using namespace Adafruit_LittleFS_Namespace;
#endif

#include "battery.h"
#include "ina226.h"
#include "node_controller.h"
#include "saanjh_protocol.h"

using namespace saanjh;

/* ---------------------------------------------------------------- objects */
/* The RAK4631's internal SX1262 is on SPI1. The constructor argument order in
 * the nRF52 core is MISO, SCK, MOSI. Do not use the WisBlock IO-slot SPI here. */
static SPIClass radioSPI(NRF_SPIM1, PIN_RADIO_MISO, PIN_RADIO_SCK, PIN_RADIO_MOSI);
static Module radioModule(PIN_RADIO_CS, PIN_RADIO_DIO1, PIN_RADIO_RESET,
                          PIN_RADIO_BUSY, radioSPI);
static SX1262 radio(&radioModule);

static INA226 ina;
static BatteryModel battery(SAANJH_BATTERY_CAPACITY_WH,
                            SAANJH_BATTERY_MIN_MV, SAANJH_BATTERY_MAX_MV);
static NodeController controller(SAANJH_NODE_ID, SAANJH_RESERVE_PCT,
                                 SAANJH_BATTERY_CAPACITY_WH);

/* ------------------------------------------------------------ runtime state */
static uint16_t g_mv = 0;
static float g_current_a = 0.0f;
static float g_power_w = 0.0f;
static float g_soc_pct = 0.0f;
static bool g_sensor_ok = false;
static bool g_ina_ok = false;
static bool g_radio_ok = false;
static bool g_rx_armed = false;
static uint16_t g_telemetry_seq = 1;
static uint32_t g_next_telemetry_ms = 0;
static uint32_t g_last_radio_retry_ms = 0;
static uint32_t g_tx_ok = 0;
static uint32_t g_rx_ok = 0;
static uint32_t g_rx_bad = 0;

#if SAANJH_PERSIST_OPT_OUT
namespace {
constexpr const char* CFG_PATH = "/saanjh.cfg";
constexpr uint32_t CFG_MAGIC = 0x534A4346UL;  /* "SJCF" */
constexpr uint16_t CFG_VERSION = 1;

struct __attribute__((packed)) PersistConfig {
  uint32_t magic;
  uint16_t version;
  uint8_t opted_out;
  uint8_t reserved;
  uint16_t crc;
};
}  // namespace
#endif

/* ---------------------------------------------------------------- helpers */
static void apply_relay() {
  static bool last_on = false;
  const bool on = controller.relay_on();
  digitalWrite(PIN_RELAY, on ? RELAY_ACTIVE_LEVEL : RELAY_INACTIVE_LEVEL);
  if (on != last_on) {
    last_on = on;
    Serial.printf("RELAY %s\n", on ? "battery" : "grid");
  }
}

static const char* event_name(ControllerEvent ev) {
  switch (ev) {
    case ControllerEvent::Completed: return "completed";
    case ControllerEvent::ReserveStop: return "reserve_stop";
    case ControllerEvent::FaultStop: return "fault_stop";
    default: return "none";
  }
}

#if SAANJH_PERSIST_OPT_OUT
static bool load_opt_out() {
  if (!InternalFS.begin()) {
    Serial.println("CFG littlefs begin failed; consent not persisted");
    return false;
  }
  if (!InternalFS.exists(CFG_PATH)) {
    return false;  /* first boot: participating */
  }
  File f = InternalFS.open(CFG_PATH, FILE_O_READ);
  if (!f) {
    Serial.println("CFG open failed; defaulting to opted-out");
    return true;
  }
  PersistConfig cfg{};
  const int n = f.read(&cfg, sizeof(cfg));
  f.close();
  if (n != static_cast<int>(sizeof(cfg)) || cfg.magic != CFG_MAGIC ||
      cfg.version != CFG_VERSION ||
      cfg.crc != crc16(reinterpret_cast<const uint8_t*>(&cfg),
                       offsetof(PersistConfig, crc))) {
    Serial.println("CFG invalid; defaulting to opted-out");
    return true;
  }
  return cfg.opted_out != 0;
}

static bool save_opt_out(bool opted_out) {
  if (!InternalFS.begin()) {
    return false;
  }
  InternalFS.remove(CFG_PATH);
  File f = InternalFS.open(CFG_PATH, FILE_O_WRITE);
  if (!f) {
    return false;
  }
  PersistConfig cfg{};
  cfg.magic = CFG_MAGIC;
  cfg.version = CFG_VERSION;
  cfg.opted_out = opted_out ? 1 : 0;
  cfg.crc = crc16(reinterpret_cast<const uint8_t*>(&cfg),
                  offsetof(PersistConfig, crc));
  const size_t n = f.write(reinterpret_cast<const uint8_t*>(&cfg), sizeof(cfg));
  f.close();
  return n == sizeof(cfg);
}
#else
static bool load_opt_out() { return false; }
static bool save_opt_out(bool) { return false; }
#endif

/* ----------------------------------------------------------------- radio */
static bool radio_init() {
  const int state = radio.begin(
      SAANJH_RADIO_FREQ_MHZ, SAANJH_RADIO_BW_KHZ, SAANJH_RADIO_SF,
      SAANJH_RADIO_CR, RADIOLIB_SX126X_SYNC_WORD_PRIVATE,
      SAANJH_RADIO_POWER_DBM, SAANJH_RADIO_PREAMBLE, SAANJH_RADIO_TCXO_V,
      false /* DC-DC regulator, as required by the RAK4631 */);
  if (state != RADIOLIB_ERR_NONE) {
    Serial.printf("RADIO begin failed: %d\n", state);
    return false;
  }
  const int rf = radio.setDio2AsRfSwitch(true);
  if (rf != RADIOLIB_ERR_NONE) {
    Serial.printf("RADIO DIO2 RF switch failed: %d\n", rf);
    return false;
  }
  radio.setCurrentLimit(90.0);
  radio.setOutputPower(SAANJH_RADIO_POWER_DBM);
  Serial.printf("RADIO ok %.4f MHz SF%u BW%.0f CR4/%u\n",
                SAANJH_RADIO_FREQ_MHZ, SAANJH_RADIO_SF, SAANJH_RADIO_BW_KHZ,
                SAANJH_RADIO_CR);
  return true;
}

/* Non-blocking receive: arm the radio, then poll DIO1 from loop(). A blocking
 * radio.receive() would stall telemetry, the push-button and the reserve check
 * for as long as no packet arrives. */
static void arm_receive() {
  if (!g_radio_ok) {
    g_rx_armed = false;
    return;
  }
  g_rx_armed = radio.startReceive() == RADIOLIB_ERR_NONE;
}

/* --------------------------------------------------------------- telemetry */
static void send_telemetry() {
  Telemetry t{};
  t.node_id = SAANJH_NODE_ID;
  t.seq = g_telemetry_seq++;
  t.battery_mv = g_mv;
  t.load_w = controller.relay_on()
                 ? static_cast<uint16_t>(constrain(lroundf(g_power_w), 0L, 65535L))
                 : 0;
  t.soc_pct = static_cast<uint8_t>(constrain(lroundf(g_soc_pct), 0L, 100L));
  t.flags = 0;
  if (g_sensor_ok && controller.reserve_ok(g_soc_pct)) t.flags |= F_RESERVE_OK;
  if (controller.opted_out()) t.flags |= F_OPTED_OUT;
  if (controller.relay_on()) t.flags |= F_RELAY_ENERGISED;
  if (!g_sensor_ok) t.flags |= F_FAULT;
  /* No temperature sensor is fitted; R_TEMP_VALID deliberately stays clear. */
  t.temp_c = SAANJH_TEMP_PLACEHOLDER_C;
  t.reserved = 0;

  uint8_t frame[MAX_FRAME];
  const size_t n = encode_telemetry(t, frame, sizeof(frame));
  if (n == 0) {
    Serial.println("TX encode failed");
    return;
  }

  if (g_radio_ok) {
    const int state = radio.transmit(frame, n);
    if (state == RADIOLIB_ERR_NONE) {
      ++g_tx_ok;
    } else {
      Serial.printf("TX failed: %d\n", state);
    }
    arm_receive();  /* transmit leaves the radio in standby */
  }
  Serial.printf("TX seq=%u soc=%.1f mv=%u w=%u a=%.2f flags=0x%02X\n", t.seq,
                g_soc_pct, g_mv, t.load_w, g_current_a, t.flags);
  g_next_telemetry_ms = millis() + SAANJH_TELEMETRY_MS;
}

static void send_ack(uint16_t seq, uint16_t command_id, uint8_t status) {
  Ack a{};
  a.node_id = SAANJH_NODE_ID;
  a.seq = seq;
  a.command_id = command_id;
  a.status = status;
  a.soc_pct = static_cast<uint8_t>(constrain(lroundf(g_soc_pct), 0L, 100L));

  uint8_t frame[MAX_FRAME];
  const size_t n = encode_ack(a, frame, sizeof(frame));
  if (n == 0) return;
  if (g_radio_ok) {
    const int state = radio.transmit(frame, n);
    if (state != RADIOLIB_ERR_NONE) {
      Serial.printf("ACK TX failed: %d\n", state);
    }
    arm_receive();  /* transmit leaves the radio in standby */
  }
  Serial.printf("ACK id=%u status=%s soc=%u\n", command_id,
                status_name(status), a.soc_pct);
}

/* ---------------------------------------------------------------- sensors */
static void read_sensors() {
  uint16_t mv = 0;
  float current_a = 0.0f;
  float power_w = 0.0f;

  if (ina.present()) {
    const float volts = ina.bus_voltage();
    current_a = ina.current();
    power_w = ina.power();
    g_ina_ok = !ina.fault();
    if (g_ina_ok) {
      mv = static_cast<uint16_t>(
          constrain(lroundf(volts * 1000.0f), 0L, 65535L));
    }
  } else {
    g_ina_ok = false;
  }

#if SAANJH_ALLOW_NO_SENSOR
  if (!g_ina_ok) {
    g_mv = 13200;
    g_current_a = 0.0f;
    g_power_w = 0.0f;
    g_soc_pct = 85.0f;
    g_sensor_ok = true;
    return;
  }
#endif

  battery.update(mv, current_a, millis(), controller.relay_on());
  g_mv = mv;
  g_current_a = current_a;
  g_power_w = power_w;
  g_soc_pct = battery.soc_pct();
  g_sensor_ok = g_ina_ok && battery.plausible();
}

/* --------------------------------------------------------------- commands */
static void handle_frame(const uint8_t* raw, size_t len) {
  Command cmd;
  const char* error = nullptr;
  if (!decode_command(raw, len, cmd, &error)) {
    ++g_rx_bad;
    Serial.printf("RX bad: %s\n", error ? error : "?");
    return;
  }
  if (cmd.node_id != SAANJH_NODE_ID) {
    return;
  }
  ++g_rx_ok;
  Serial.printf("RX cmd id=%u dur=%us limit=%uW flags=0x%02X\n", cmd.command_id,
                cmd.duration_s, cmd.power_limit_w, cmd.flags);

  const uint8_t status =
      controller.apply_command(cmd, millis(), g_soc_pct, g_sensor_ok);
  apply_relay();
  send_ack(cmd.seq, cmd.command_id, status);
  send_telemetry();
}

/* ---------------------------------------------------------------- button */
static void button_tick() {
  static bool last_reading = HIGH;
  static bool pressed = false;
  static bool fired = false;
  static uint32_t changed_at = 0;
  static uint32_t pressed_at = 0;

  const uint32_t now = millis();
  const bool reading = digitalRead(PIN_BUTTON);
  if (reading != last_reading) {
    changed_at = now;
    last_reading = reading;
  }
  if (now - changed_at < SAANJH_BUTTON_DEBOUNCE_MS) {
    return;
  }

  if (reading == LOW) {
    if (!pressed) {
      pressed = true;
      pressed_at = now;
      fired = false;
    }
    if (!fired && now - pressed_at >= SAANJH_BUTTON_HOLD_MS) {
      fired = true;
      const bool opted_out = controller.toggle_opt_out(now);
      apply_relay();
      const bool saved = save_opt_out(opted_out);
      Serial.printf("OPT_OUT=%d persisted=%d\n", opted_out, saved);
      send_telemetry();
    }
  } else {
    pressed = false;
    fired = false;
  }
}

/* ------------------------------------------------------------------- LEDs */
static void led_tick() {
  const uint32_t now = millis();
  const bool fault = !g_radio_ok || !g_sensor_ok;
  if (fault) {
    digitalWrite(PIN_LED_STATUS, LOW);
    digitalWrite(PIN_LED_FAULT, ((now / 100) % 2) ? HIGH : LOW);
  } else if (controller.opted_out()) {
    digitalWrite(PIN_LED_STATUS, LOW);
    digitalWrite(PIN_LED_FAULT, ((now / 1000) % 2) ? HIGH : LOW);
  } else if (controller.relay_on()) {
    digitalWrite(PIN_LED_FAULT, LOW);
    digitalWrite(PIN_LED_STATUS, (now % 2000) < 100 ? HIGH : LOW);
  } else {
    digitalWrite(PIN_LED_FAULT, LOW);
    digitalWrite(PIN_LED_STATUS, HIGH);
  }
}

/* ------------------------------------------------------------------ setup */
void setup() {
  pinMode(PIN_RELAY, OUTPUT);
  digitalWrite(PIN_RELAY, RELAY_INACTIVE_LEVEL);
  pinMode(PIN_LED_STATUS, OUTPUT);
  pinMode(PIN_LED_FAULT, OUTPUT);
  digitalWrite(PIN_LED_STATUS, LOW);
  digitalWrite(PIN_LED_FAULT, LOW);
  pinMode(PIN_BUTTON, INPUT_PULLUP);

  Serial.begin(SAANJH_SERIAL_BAUD);
  delay(100);
  Serial.printf("\nSAANJH node %u fw %s\n", SAANJH_NODE_ID, SAANJH_FW_VERSION);

  Wire.begin();
  Wire.setClock(SAANJH_I2C_CLOCK);
  g_ina_ok = ina.begin(Wire, INA226_ADDRESS);
  if (g_ina_ok) {
    delay(5);
    g_mv = static_cast<uint16_t>(
        constrain(lroundf(ina.bus_voltage() * 1000.0f), 0L, 65535L));
  }
  battery.begin(g_mv, millis());
  g_soc_pct = battery.soc_pct();
  g_sensor_ok = g_ina_ok && battery.plausible();
  Serial.printf("INA226=%s mv=%u soc=%.1f%%\n", g_ina_ok ? "ok" : "MISSING",
                g_mv, g_soc_pct);

  const bool opted_out = load_opt_out();
  controller.begin(millis(), g_soc_pct, opted_out);
  apply_relay();

  g_radio_ok = radio_init();
  arm_receive();
  g_last_radio_retry_ms = millis();
  g_next_telemetry_ms = millis() + 1000;
  Serial.printf("CONSENT opted_out=%d relay=%s\n", controller.opted_out(),
                controller.relay_on() ? "battery" : "grid");
}

/* ------------------------------------------------------------------- loop */
void loop() {
  button_tick();
  read_sensors();

  const ControllerEvent ev = controller.tick(millis(), g_soc_pct, g_sensor_ok);
  if (ev != ControllerEvent::None) {
    apply_relay();
    Serial.printf("COMMAND %s\n", event_name(ev));
    send_ack(controller.last_command_seq(), controller.last_command_id(),
             ACK_DONE);
    send_telemetry();
  }

  if (g_radio_ok) {
    if (!g_rx_armed) {
      arm_receive();
    }
    if (g_rx_armed && digitalRead(PIN_RADIO_DIO1) == HIGH) {
      uint8_t buffer[MAX_FRAME];
      size_t n = radio.getPacketLength();
      if (n > sizeof(buffer)) n = sizeof(buffer);
      const int state =
          (n > 0) ? radio.readData(buffer, n) : RADIOLIB_ERR_NONE;
      g_rx_armed = false;
      if (state == RADIOLIB_ERR_NONE && n > 0) {
        Serial.printf("RX rssi=%.1f snr=%.1f\n", radio.getRSSI(), radio.getSNR());
        handle_frame(buffer, n);
      } else if (state == RADIOLIB_ERR_CRC_MISMATCH) {
        ++g_rx_bad;
      } else if (state != RADIOLIB_ERR_NONE) {
        Serial.printf("RX error: %d\n", state);
        if (state == RADIOLIB_ERR_CHIP_NOT_FOUND ||
            state == RADIOLIB_ERR_SPI_CMD_TIMEOUT) {
          g_radio_ok = false;
          g_last_radio_retry_ms = millis();
        }
      }
      arm_receive();
    }
  } else if (millis() - g_last_radio_retry_ms >= SAANJH_RADIO_RETRY_MS) {
    g_last_radio_retry_ms = millis();
    g_radio_ok = radio_init();
    arm_receive();
  }

  if (static_cast<int32_t>(millis() - g_next_telemetry_ms) >= 0) {
    send_telemetry();
  }

  led_tick();
}
