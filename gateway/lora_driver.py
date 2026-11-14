"""LoRa drivers for the CM4 gateway.

Four transports implement the same small interface:

    driver.send(bytes) -> None
    driver.recv(timeout_s) -> bytes | None
    driver.close()

* ``LoRaRfDriver`` wraps ``chandrawi/LoRaRF-Python`` (MIT), the library used by
  the Waveshare sample. It is the preferred SPI backend because it drives the
  HAT's TXEN pin and handles the DIO2 RXEN switch.
* ``SX1262Driver`` talks to the Waveshare-class SX1262 SPI HAT directly
  (spidev + RPi.GPIO). Pins are configurable; defaults match the Waveshare
  SX1262 XXXM HAT sample (CS0, RESET 18, BUSY 20, DIO1 16, TXEN 6, RXEN -1).
* ``SerialDriver`` reads hex frames from a USB-connected RAK4631 used as a radio bridge,
  handy on a bench or on Windows.
* ``LoopbackDriver`` is an in-memory pair used by tests and the replay service.

The SPI register sequence follows the Semtech SX1261/2 datasheet. It is intentionally
small and explicit rather than hiding behind a vendor SDK; the replay mode exercises the
packet codec and dispatcher even when no radio is attached.
"""
import os
import queue
import time

try:  # optional on non-Pi machines
    import serial
except ImportError:  # pragma: no cover
    serial = None

FREQ_HZ = 865_062_500          # India ISM 865-867 MHz
SF = 9
BW = 0x04                      # 125 kHz
CR = 0x01                      # 4/5
PREAMBLE = 8
TX_DBM = 14
SYNC_WORD = 0x1424             # private LoRa sync word, must match firmware

# SX126x opcodes
SET_SLEEP = 0x84
SET_STANDBY = 0x80
SET_PACKET_TYPE = 0x8A
SET_RF_FREQUENCY = 0x86
SET_PA_CONFIG = 0x95
SET_TX_PARAMS = 0x8E
SET_BUFFER_BASE = 0x8F
SET_MODULATION = 0x8B
SET_PACKET_PARAMS = 0x8C
SET_DIO_IRQ = 0x8D
SET_TX = 0x83
SET_RX = 0x82
GET_IRQ = 0x12
CLEAR_IRQ = 0x02
GET_RX_BUFFER = 0x13
GET_PACKET_STATUS = 0x14
WRITE_BUFFER = 0x0E
READ_BUFFER = 0x1E
WRITE_REGISTER = 0x0D
SET_DIO2_RF = 0x9D
SET_REGULATOR = 0x96
CALIBRATE_IMAGE = 0x89
SET_TCXO = 0x97

IRQ_TX_DONE = 0x0001
IRQ_RX_DONE = 0x0002
IRQ_CRC_ERR = 0x0040
IRQ_TIMEOUT = 0x0200
IRQ_ALL = 0x03FF


class RadioDriver:
    def send(self, payload: bytes) -> None:
        raise NotImplementedError

    def recv(self, timeout_s: float = 1.0):
        raise NotImplementedError

    def close(self):
        pass


class SX1262Driver(RadioDriver):
    """Minimal SX126x SPI driver. Requires ``spidev`` and ``RPi.GPIO`` on the CM4."""

    def __init__(self, bus=0, device=0, reset_pin=18, busy_pin=20, dio1_pin=16,
                 txen_pin=6, frequency_hz=FREQ_HZ, tx_dbm=TX_DBM, tcxo_voltage=None):
        import spidev
        import RPi.GPIO as GPIO

        self.GPIO = GPIO
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = 2_000_000
        self.spi.mode = 0
        self.reset_pin, self.busy_pin, self.dio1_pin = reset_pin, busy_pin, dio1_pin
        self.txen_pin = txen_pin
        self.frequency_hz, self.tx_dbm, self.tcxo_voltage = frequency_hz, tx_dbm, tcxo_voltage
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(reset_pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(busy_pin, GPIO.IN)
        GPIO.setup(dio1_pin, GPIO.IN)
        # Waveshare HAT: TXEN low = transmit, high = receive. RXEN is tied to DIO2.
        if txen_pin is not None and txen_pin >= 0:
            GPIO.setup(txen_pin, GPIO.OUT, initial=GPIO.HIGH)
        self._reset()
        self._configure()

    # ---------------------------------------------------------------- low level
    def _wait_busy(self, timeout=0.2):
        t0 = time.time()
        while self.GPIO.input(self.busy_pin):
            if time.time() - t0 > timeout:
                raise TimeoutError("SX1262 BUSY stuck high")
            time.sleep(0.0005)

    def _cmd(self, opcode, data=b"", wait=True):
        self.spi.xfer2([opcode] + list(data))
        if wait:
            self._wait_busy()

    def _read_cmd(self, opcode, n):
        rx = self.spi.xfer2([opcode, 0x00] + [0x00] * n)
        self._wait_busy()
        return bytes(rx[2:2 + n])

    def _reset(self):
        self.GPIO.output(self.reset_pin, self.GPIO.LOW)
        time.sleep(0.01)
        self.GPIO.output(self.reset_pin, self.GPIO.HIGH)
        time.sleep(0.02)
        self._wait_busy()

    def _configure(self):
        self._cmd(SET_STANDBY, [0x00])
        self._cmd(SET_REGULATOR, [0x01])              # DC-DC
        if self.tcxo_voltage:
            code = {1.6: 0x00, 1.7: 0x01, 1.8: 0x02, 2.2: 0x03,
                    2.4: 0x04, 2.7: 0x05, 3.0: 0x06, 3.3: 0x07}[self.tcxo_voltage]
            self._cmd(SET_TCXO, [code, 0x00, 0x00, 0x05])  # 5 ms timeout
        self._cmd(SET_DIO2_RF, [0x01])
        self._cmd(CALIBRATE_IMAGE, [0x6B, 0x6F])      # 863-870 MHz
        self._cmd(SET_PACKET_TYPE, [0x01])            # LoRa
        freq = int(self.frequency_hz * (1 << 25) / 32_000_000)
        self._cmd(SET_RF_FREQUENCY, list(freq.to_bytes(4, "big")))
        self._cmd(SET_PA_CONFIG, [0x04, 0x07, 0x00, 0x01])
        self._cmd(SET_TX_PARAMS, [self.tx_dbm, 0x04])
        self._cmd(SET_BUFFER_BASE, [0x00, 0x00])
        self._cmd(SET_MODULATION, [SF, BW, CR, 0x00])
        self._cmd(SET_PACKET_PARAMS, [PREAMBLE, 0x00, 0xFF, 0x01, 0x00])
        self._cmd(SET_DIO_IRQ, list(IRQ_ALL.to_bytes(2, "big")) * 2 + [0, 0, 0, 0])
        self._cmd(WRITE_REGISTER, [0x07, 0x40, (SYNC_WORD >> 8) & 0xFF, SYNC_WORD & 0xFF])

    def _irq(self):
        return int.from_bytes(self._read_cmd(GET_IRQ, 2), "big")

    def _clear(self):
        self._cmd(CLEAR_IRQ, [0xFF, 0xFF])

    def _set_txen(self, transmitting: bool):
        if self.txen_pin is not None and self.txen_pin >= 0:
            self.GPIO.output(self.txen_pin,
                             self.GPIO.LOW if transmitting else self.GPIO.HIGH)

    # ---------------------------------------------------------------- public
    def send(self, payload: bytes) -> None:
        if not 0 < len(payload) <= 255:
            raise ValueError("payload must be 1..255 bytes")
        self._cmd(SET_STANDBY, [0x00])
        self._cmd(SET_BUFFER_BASE, [0x00, 0x00])
        self._cmd(WRITE_BUFFER, [0x00] + list(payload))
        self._cmd(SET_PACKET_PARAMS, [PREAMBLE, 0x00, len(payload), 0x01, 0x00])
        self._clear()
        self._set_txen(transmitting=True)
        try:
            self._cmd(SET_TX, [0x00, 0x00, 0x00])
            t0 = time.time()
            while not self.GPIO.input(self.dio1_pin):
                if time.time() - t0 > 2.0:
                    raise TimeoutError("SX1262 TX timeout")
                time.sleep(0.001)
        finally:
            self._set_txen(transmitting=False)
        self._clear()
        self._cmd(SET_STANDBY, [0x00])

    def recv(self, timeout_s: float = 1.0):
        self._clear()
        self._cmd(SET_PACKET_PARAMS, [PREAMBLE, 0x00, 0xFF, 0x01, 0x00])
        self._set_txen(transmitting=False)
        self._cmd(SET_RX, [0xFF, 0xFF, 0xFF])         # continuous
        t0 = time.time()
        while not self.GPIO.input(self.dio1_pin):
            if time.time() - t0 > timeout_s:
                self._cmd(SET_STANDBY, [0x00])
                return None
            time.sleep(0.001)
        irq = self._irq()
        self._clear()
        self._cmd(SET_STANDBY, [0x00])
        if irq & IRQ_CRC_ERR and not irq & IRQ_RX_DONE:
            return None
        if not irq & IRQ_RX_DONE:
            return None
        buf = self._read_cmd(GET_RX_BUFFER, 2)
        start, length = buf[0], buf[1]
        rx = self.spi.xfer2([READ_BUFFER, start] + [0x00] * length)
        self._wait_busy()
        return bytes(rx[2:])

    def packet_status(self):
        raw = self._read_cmd(GET_PACKET_STATUS, 3)
        rssi = -int(raw[0]) / 2.0
        snr = int.from_bytes(raw[1:2], "big", signed=True) / 4.0
        return {"rssi_dbm": rssi, "snr_db": snr}

    def close(self):
        try:
            self._cmd(SET_SLEEP, [0x04])
        finally:
            self.spi.close()
            pins = [self.reset_pin, self.busy_pin, self.dio1_pin]
            if self.txen_pin is not None and self.txen_pin >= 0:
                pins.append(self.txen_pin)
            self.GPIO.cleanup(pins)


class LoRaRfDriver(RadioDriver):
    """SX126x SPI transport using ``LoRaRF-Python`` (MIT).

    This is the preferred backend for the Waveshare SX1262 XXXM HAT because the
    library drives TXEN (BCM6) and configures DIO2 as the RXEN RF switch. Pin
    defaults are the values in Waveshare's own sample:

        reset=18, busy=20, irq=16, txen=6, rxen=-1
    """

    def __init__(self, bus=0, device=0, reset_pin=18, busy_pin=20, dio1_pin=16,
                 txen_pin=6, frequency_hz=FREQ_HZ, tx_dbm=TX_DBM):
        try:
            from LoRaRF import SX126x
        except ImportError as exc:  # pragma: no cover - Pi-only dependency
            raise RuntimeError(
                "LoRaRF is not installed: pip install LoRaRF (or set "
                "SAANJH_RADIO_BACKEND=custom)") from exc

        self.LoRa = SX126x()
        if not self.LoRa.begin(bus, device, reset_pin, busy_pin, dio1_pin,
                               txen_pin, -1):
            raise RuntimeError("LoRaRF could not initialise the SX1262")
        self.LoRa.setDio2RfSwitch()
        self.LoRa.setFrequency(frequency_hz)
        self.LoRa.setTxPower(tx_dbm, self.LoRa.TX_POWER_SX1262)
        self.LoRa.setLoRaModulation(SF, 125_000, 5)       # CR 4/5
        self.LoRa.setLoRaPacket(self.LoRa.HEADER_EXPLICIT, PREAMBLE, 255, True)
        self.LoRa.setSyncWord(SYNC_WORD)

    def send(self, payload: bytes) -> None:
        if not 0 < len(payload) <= 255:
            raise ValueError("payload must be 1..255 bytes")
        self.LoRa.beginPacket()
        self.LoRa.put(payload)
        self.LoRa.endPacket()
        if not self.LoRa.wait(2000):
            raise TimeoutError("SX1262 TX timeout")

    def recv(self, timeout_s: float = 1.0):
        timeout_ms = max(1, int(timeout_s * 1000))
        self.LoRa.request(timeout_ms)
        self.LoRa.wait(timeout_ms + 50)
        available = self.LoRa.available()
        if available <= 0:
            return None
        return bytes(self.LoRa.read(available))

    def packet_status(self):
        return {"rssi_dbm": self.LoRa.packetRssi(), "snr_db": self.LoRa.snr()}

    def close(self):
        try:
            self.LoRa.end()
        finally:
            pass


class SerialDriver(RadioDriver):
    """Hex-frame transport over USB serial (e.g. a RAK4631 USB bridge)."""

    def __init__(self, port, baud=115200, timeout=0.2):
        if serial is None:
            raise RuntimeError("pyserial is not installed: pip install pyserial")
        self.ser = serial.Serial(port, baud, timeout=timeout)

    def send(self, payload: bytes) -> None:
        self.ser.write(payload.hex().encode("ascii") + b"\n")
        self.ser.flush()

    def recv(self, timeout_s: float = 1.0):
        t0 = time.time()
        while time.time() - t0 < timeout_s:
            line = self.ser.readline().strip()
            if not line:
                continue
            try:
                return bytes.fromhex(line.decode("ascii"))
            except ValueError:
                continue
        return None

    def close(self):
        self.ser.close()


class LoopbackDriver(RadioDriver):
    """In-memory link. ``peer`` is the other end of the link; ``drop`` simulates loss."""

    def __init__(self, name="radio", drop=0.0, rng=None):
        self.name = name
        self.peer = None
        self.drop = drop
        self.rng = rng
        self.inbox = queue.Queue()

    def pair(self, other):
        self.peer = other
        other.peer = self

    def send(self, payload: bytes) -> None:
        if self.peer is None:
            return
        if self.rng is not None and self.rng.random() < self.drop:
            return
        self.peer.inbox.put(payload)

    def recv(self, timeout_s: float = 1.0):
        try:
            return self.inbox.get(timeout=timeout_s)
        except queue.Empty:
            return None

    def inject(self, payload: bytes):
        self.inbox.put(payload)


def _spi_pins():
    return {
        "bus": int(os.environ.get("SAANJH_SPI_BUS", "0")),
        "device": int(os.environ.get("SAANJH_SPI_DEVICE", "0")),
        "reset_pin": int(os.environ.get("SAANJH_RESET_GPIO", "18")),
        "busy_pin": int(os.environ.get("SAANJH_BUSY_GPIO", "20")),
        "dio1_pin": int(os.environ.get("SAANJH_DIO1_GPIO", "16")),
        "txen_pin": int(os.environ.get("SAANJH_TXEN_GPIO", "6")),
    }


def from_env(mode="live"):
    """Build a driver from environment variables; used by gateway.service.

    ``SAANJH_RADIO_BACKEND`` selects the SPI backend:
      * ``lorarf``  - require LoRaRF-Python;
      * ``custom``  - require the in-tree SX1262 register driver;
      * ``auto``    - try LoRaRF, fall back to the in-tree driver.
    """
    if mode == "serial":
        return SerialDriver(os.environ.get("SAANJH_SERIAL", "COM5"),
                            int(os.environ.get("SAANJH_BAUD", "115200")))

    pins = _spi_pins()
    backend = os.environ.get("SAANJH_RADIO_BACKEND", "auto").lower()
    if backend not in ("auto", "lorarf", "custom"):
        raise ValueError("SAANJH_RADIO_BACKEND must be auto, lorarf or custom")

    if backend in ("auto", "lorarf"):
        try:
            return LoRaRfDriver(**pins)
        except Exception:
            if backend == "lorarf":
                raise
    return SX1262Driver(
        **pins,
        tcxo_voltage=float(os.environ["SAANJH_TCXO"]) if os.environ.get("SAANJH_TCXO") else None,
    )
