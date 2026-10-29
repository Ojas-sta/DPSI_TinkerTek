# ICRobot Native C / ESP-IDF Driver & Project

This directory contains a pure **C / ESP-IDF** implementation for the **School For Schools (s4s) ICRobot**, replacing MicroPython with native, zero-overhead compiled C running on FreeRTOS.

---

## 🚀 Why ESP-IDF / Raw C?

1. **Microsecond Precision**: Real-time control without MicroPython garbage collection pauses.
2. **True Dual-Core Multiprocessing**:
   - **Core 0**: Wi-Fi, Bluetooth LE, WebSocket telemetry, or camera streaming.
   - **Core 1**: Dedicated motion planning, PID motor loops, and 2-axis arm inverse kinematics.
3. **Small Binary Footprint**: Only a few hundred kilobytes instead of 6+ MB.

---

## 🛠️ Quick Start

### 1. Set Up the ESP-IDF Environment
Ensure you have ESP-IDF v4.4+ or v5.x installed:
```bash
# Set up ESP-IDF environment variables
. $HOME/esp/esp-idf/export.sh
```

### 2. Set Target to ESP32-S3
```bash
cd esp_idf
idf.py set-target esp32s3
```

### 3. Build & Flash
Connect your ICRobot via USB and run:
```bash
idf.py build flash -p /dev/cu.usbserial-110 monitor
```

---

## 📖 API Reference

See [`main/icrobot.h`](main/icrobot.h) for full documentation:

* `icrobot_init()` — Sets up I2C on GPIO 42 (SDA) / GPIO 41 (SCL) and binds motors.
* `icrobot_set_arm(axis1, axis2)` — Direct 0–180° servo control.
* `icrobot_release_arm()` — De-energizes servos to save power.
* `icrobot_move_cm(dir, distance)` — Move forward/backward/turn with encoder precision.
* `icrobot_set_speed(left, right)` — Independent wheel speed control (0–100%).
* `icrobot_get_battery(&pct)` — Read battery level percentage.
* `icrobot_set_led(r, g, b, brightness)` — Ambient RGB LED lighting.
