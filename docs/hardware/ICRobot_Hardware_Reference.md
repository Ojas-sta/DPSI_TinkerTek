# ICRobot Hardware Reference

> **Platform:** ICRobot (ESP32-S3) + Arduino Uno R4 WiFi Controller  
> **Mainboard:** s4s Mainboard (I2C address `0x0F`)  
> **Document version:** 1.0 — ICRobot Open-Source Contributors

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ICRobot System                           │
│                                                             │
│  ┌──────────────────┐     Serial/I2C     ┌──────────────┐  │
│  │  Arduino Uno R4  │ ◄────────────────► │  ESP32-S3    │  │
│  │  WiFi (Control)  │                    │  (Main MCU)  │  │
│  └──────────────────┘                    └──────┬───────┘  │
│                                                 │ I2C Bus   │
│                               ┌─────────────────┼──────┐   │
│                               ▼                 ▼      ▼   │
│                        ┌─────────┐  ┌───────┐  ┌────────┐  │
│                        │  s4s    │  │ULTR   │  │LSM6DS3 │  │
│                        │Mainboard│  │ 0x57  │  │  0x6F  │  │
│                        │  0x0F   │  └───────┘  └────────┘  │
│                        └────┬────┘                          │
│                    ┌────────┼────────┐                      │
│                    ▼        ▼        ▼                      │
│             ┌─────────┐ ┌──────┐ ┌──────┐                  │
│             │ Motors  │ │Servo │ │ RGB  │                   │
│             │ (L & R) │ │ Arm  │ │ LEDs │                   │
│             │ Encoder │ │ 0+1  │ │      │                   │
│             └─────────┘ └──────┘ └──────┘                  │
│                                                             │
│  Also on I2C bus:  OLED SH1107 @ 0x3C                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Peripheral I2C Addresses

| Device | I2C Address | Library |
|--------|-------------|---------|
| s4s Mainboard | `0x0F` | `s4s_mainBoard` (this repo) |
| Ultrasonic Sensor | `0x57` | `s4s_mainBoard` (built-in) |
| OLED Display (SH1107, 128×128) | `0x3C` | `Adafruit SH110X` |
| Gyroscope / IMU (LSM6DS3) | `0x6F` | `Seeed_Arduino_LSM6DS3` |
| Line Sensor (4-ch grayscale) | `0x6F` / `0x71` | `s4s_mainBoard` (built-in) |

> **Note:** The gyroscope (LSM6DS3) and the line sensor share I2C address `0x6F` on some board revisions. On those boards, the gray sensor functions use raw I2C `writeData`/`readData` with a command byte protocol instead of register-addressed reads.

---

## Complete I2C Register Map — s4s Mainboard (0x0F)

### Power / Battery (Base: `0x00`)

| Register | Hex | Description | Data Format |
|----------|-----|-------------|-------------|
| Battery Level | `0x00` | Internal battery % | `uint8` 0–100 |
| Ext. Voltage | `0x01` | External battery voltage × 10 | `uint8` (÷10 = volts) |
| Charger Status | `0x02` | Is charging? | `1`=yes, `0`=no |
| Fully Charged | `0x03` | Is fully charged? | `1`=yes, `0`=no |
| FW Version | `0x04` | Firmware version | `[major, minor, patch]` 3 bytes |

### Ambient LED (Base: `0x0A`)

| Register | Hex | Description | Data Format |
|----------|-----|-------------|-------------|
| Brightness | `0x0A` | LED brightness | `uint8` 0–255 |
| LED Red | `0x0B` | Red channel | `uint8` 0–255 |
| LED Green | `0x0C` | Green channel | `uint8` 0–255 |
| LED Blue | `0x0D` | Blue channel | `uint8` 0–255 |

> **Tip:** Write brightness first (`0x0A`), then write 3-byte colour `[R, G, B]` to `0x0B`.

### Real-Time Clock (Base: `0x14`)

| Register | Hex | Description | Data Format |
|----------|-----|-------------|-------------|
| RTC Time | `0x14` | Time read/write | `[hour, minute, second]` 3 bytes |
| RTC Week | `0x15` | Day of week | `uint8` |
| RTC Month | `0x16` | Month | `uint8` 1–12 |
| RTC Day | `0x17` | Day of month | `uint8` 1–31 |
| RTC Year | `0x18` | Year (2-digit) | `uint8` 0–99 |

### Servo Arm (Base: `0x1E`)

| Register | Hex | Description | Data Format |
|----------|-----|-------------|-------------|
| Servo 0 Angle (Arm Axis 1) | `0x1E` | Base / elevation angle | `uint8` 0–180° |
| Servo 1 Angle (Arm Axis 2) | `0x1F` | Gripper angle | `uint8` 0–180° |
| Cont. Servo 0 Speed | `0x20` | Continuous rotation speed | `int8` –100 to 100 |
| Cont. Servo 1 Speed | `0x21` | Continuous rotation speed | `int8` –100 to 100 |
| Servo 0 Release | `0x22` | De-energize servo 0 | Write `0x00` |
| Servo 1 Release | `0x23` | De-energize servo 1 | Write `0x00` |

### Voice Module (Base: `0x28`)

| Register | Hex | Description | Data Format |
|----------|-----|-------------|-------------|
| Voice State | `0x28` | Last recognised command ID | `uint8` |
| Voice Version | `0x29` | Module firmware version | `[major, minor, patch]` |

### Individual Encoder Motors (Bases: `0x50`, `0x6E`, `0x8C`, `0xAA`)

Each of the 4 motor channels has an identical register layout starting at its base:

| Offset | Description | Data Format |
|--------|-------------|-------------|
| `+0` (4 bytes) | Encoder angle (write 0 to reset) | `int32` big-endian |
| `+1` (2 bytes) | RPM speed (read) | `int16` big-endian |
| `+2` (2 bytes) | Dynamic speed (read) | `int16` big-endian |
| `+3` (2 bytes) | Motor power (read) | `uint16` big-endian |
| `+4` | Action command | `uint8` (see action codes below) |
| `+5` (2 bytes) | RPM speed setpoint | `uint16` big-endian |
| `+6` (2 bytes) | Dynamic speed setpoint | `uint16` big-endian |
| `+7` | Power setpoint | `uint8` 0–100 |
| `+8` (2 bytes) | Ring (lap count) setpoint | `uint16` |
| `+9` (2 bytes) | Relative angle setpoint | `uint16` |
| `+10` (2 bytes) | Run time (seconds) | `uint16` |
| `+11` (2 bytes) | Distance (centimeters) | `uint16` |
| `+12` | Action running status | `uint8` 0=stopped, 1=running |

### Motor Pair — Differential Drive (Base: `0xC8`)

| Register | Hex | Description | Data Format |
|----------|-----|-------------|-------------|
| Motor Pair Action | `0xC8` | Drive command | `uint8` action code (see below) |
| Motor Pair Group | `0xC9` | Set L+R motor IDs | `[left_id, right_id]` 2 bytes |
| Motor Pair Speed | `0xCA` | Left + right speed | `[L_hi, L_lo, R_hi, R_lo]` 4 bytes |
| Motor Pair Time | `0xCB` | Run duration (ms) | `uint16` big-endian |
| Motor Pair Ring | `0xCC` | Lap count | `[L_hi, L_lo, R_hi, R_lo]` 4 bytes |
| Motor Pair Distance | `0xCD` | Distance (cm) | `[L_hi, L_lo, R_hi, R_lo]` 4 bytes |
| Pair Action Running | `0xCE` | Is pair still executing? | `uint8` 0=stop, 1=running |

---

## Motor Action Code Reference

### Individual Motor Actions (`encoder_motor_set_action`)

| Code | Mode | Direction |
|------|------|-----------|
| `0` | — | Stop |
| `1` | RPM speed | Forward |
| `2` | RPM speed | Backward |
| `3` | Dynamic speed | Forward |
| `4` | Dynamic speed | Backward |
| `5` | Power | Forward |
| `6` | Power | Backward |
| `7` | Ring (laps) | Forward |
| `8` | Ring (laps) | Backward |
| `9` | Angle | Forward |
| `10` | Angle | Backward |
| `11` | Timed (seconds) | Forward |
| `12` | Timed (seconds) | Backward |
| `13` | Distance (cm) | Forward |
| `14` | Distance (cm) | Backward |

### Motor Pair Actions (`encoder_motor_pair_set_action`)

| Code | Mode | Direction |
|------|------|-----------|
| `0` | — | Stop |
| `1` | Speed | Forward |
| `2` | Speed | Backward |
| `3` | Speed | Turn Left |
| `4` | Speed | Turn Right |
| `5` | Timed | Forward |
| `6` | Timed | Backward |
| `7` | Timed | Turn Left |
| `8` | Timed | Turn Right |
| `9` | Ring (laps) | Forward |
| `10` | Ring | Backward |
| `11` | Ring | Turn Left |
| `12` | Ring | Turn Right |
| `13` | Distance (cm) | Forward |
| `14` | Distance (cm) | Backward |
| `15` | Distance (cm) | Turn Left |
| `16` | Distance (cm) | Turn Right |

---

## Ultrasonic Sensor (I2C `0x57`)

| Register | Description | Data Format |
|----------|-------------|-------------|
| `0x01` | Distance measurement | 3-byte big-endian, unit = 0.1 mm |
| `0x02` | LED colour control | `[brightness, R, G, B]` 4 bytes |

> **Timing:** Consecutive reads must be at least **50 ms** apart. The library enforces this automatically and returns the last cached value for requests within the window.

**Conversion formula:**
```
raw = (data[0] << 16) | (data[1] << 8) | data[0]
distance_cm = raw / 10000
```

---

## Servo Wiring Notes

- Servo arm uses **Servo ID 0** (axis 1 / base) and **Servo ID 1** (axis 2 / gripper).
- Control is entirely via **I2C** — no direct PWM pins are used or exposed.
- Angle range: **0–180°** for positional servo mode.
- Speed range: **–100 to 100** for continuous rotation mode.
- After completing a task, call `servo_release(id)` to de-energize the servo and reduce heat / power consumption.

---

## ESP32-S3 Pin Usage

| GPIO | Function |
|------|----------|
| `42` | I2C SDA (primary — mainboard) |
| `41` | I2C SCL (primary — mainboard) |
| `1` | I2C SDA secondary (ESP32 only — peripherals) |
| `2` | I2C SCL secondary (ESP32 only — peripherals) |
| Others | Camera, audio I²S, UART — TBD / under investigation |

> **Note:** On Arduino Uno R4 WiFi (Renesas RA4M1), the standard `Wire.begin()` is called without pin arguments. I2C uses the board's hardware I2C pins (A4/A5 or dedicated SDA/SCL header).

---

## Board Revision Notes

| Feature | Status |
|---------|--------|
| Motor pair centimeter command (0xCD) | ✅ Confirmed via source |
| Servo release registers (0x22, 0x23) | ✅ Confirmed via source |
| Ultrasonic LED (0x57 reg 0x02) | ✅ Confirmed via source |
| Voice module (0x28) | ✅ Confirmed, module-dependent |
| Camera / AI module | 🔬 Under investigation |
| Audio I²S player | 🔬 Under investigation |
| Magnetometer (QMC5883P) | 🔬 Referenced in platformio.ini deps |

---

## 🔬 Firmware Reverse Engineering Details

### ESP32-S3 Flash Memory Map (16 MB Total)
| Offset | Size | Partition Name | Type / Subtype | Contents |
|---|---|---|---|---|
| `0x000000` | 36 KB | **Bootloader** | - | ESP32-S3 2nd stage bootloader |
| `0x008000` | 4 KB | **Partition Table** | - | Standard ESP-IDF partition entries |
| `0x009000` | 24 KB | **nvs** | `0x01 / 0x02` | Non-Volatile Storage (WiFi credentials, calibration) |
| `0x00F000` | 4 KB | **phy_init** | `0x01 / 0x01` | RF PHY initialization data |
| `0x010000` | 6 MB | **factory** | `0x00 / 0x00` | ESP-IDF MicroPython runtime (FreeRTOS, LVGL, I2S, Camera) |
| `0x610000` | ~10 MB | **vfs** | `0x01 / 0x81` | LittleFS Filesystem (`s4s.py`, `s4sble.py`, `ui.py`, `main.py`) |

### Microcontroller Pin Mapping (ESP32-S3)
* **SPI Bus (LCD Screen - ST7789 320x240)**:
  * MOSI: `GPIO 40`
  * MISO: `GPIO 38`
  * SCK: `GPIO 39`
* **I2C Bus 0 (Internal Mainboard / Motors / Servos)**:
  * SDA: `GPIO 42`
  * SCL: `GPIO 41`
  * Speed: 100 kHz
* **I2C Bus 1 (External Sensors & K210 AI Camera)**:
  * SDA: `GPIO 1`
  * SCL: `GPIO 2`
  * Speed: 100 kHz

### LittleFS Extracted System Files
Located in `firmware/extracted_vfs/`:
* `s4s.py`: Full hardware abstraction layer (`Movement`, `Servo`, `LSM6DS3`, `Ultrasonic`, `Line_sensor`, `Voice`, `Vision`, `Light`).
* `s4sble.py`: Low-energy Bluetooth stack with full service UUID definitions.
* `ui.py`: LVGL-driven user interface for status display, IP, battery, and server state.
* `boot.py`: Bootloader with XMODEM mainboard firmware flashing support.
* `main.py`: Interactive execution loop, websocket client, and dual REPL output.
