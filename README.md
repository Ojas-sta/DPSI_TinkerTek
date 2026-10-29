# 🤖 ICRobot Open-Source Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-ESP32--S3%20%7C%20Arduino%20Uno%20R4%20WiFi-blue)](https://www.espressif.com/en/products/socs/esp32-s3)
[![Language](https://img.shields.io/badge/Language-C%2B%2B%20%7C%20MicroPython-green)](https://micropython.org/)
[![Hardware](https://img.shields.io/badge/Hardware-School%20Robotics-orange)]()
[![Made by s4s](https://img.shields.io/badge/Made%20by-School%20for%20Schools%20(s4s)-red)]()

> **Open-source reverse-engineered hardware platform for the ICRobot school robotics system**, enabling community development, custom firmware, and expanded capabilities beyond the stock TinkerCode IDE.

---

## 🏫 What is ICRobot?

**ICRobot** is a commercially available wheeled robot designed for school STEM education, manufactured by **School for Schools (s4s)**. It features:

- An **ESP32-S3** main processor running MicroPython
- A proprietary **s4s Mainboard** (I2C address `0x0F`) controlling motors, servos, LEDs, and power
- An **Arduino Uno R4 WiFi** as the controller board (communicates with the ICRobot over serial)
- **TinkerCode** as the official block-based IDE

This repository provides **open-source libraries, documentation, and tools** so educators, students, and developers can program the ICRobot in MicroPython or Arduino C++ — without being locked to TinkerCode.

The companion **ICBricks / ICMaster** platform is also documented here — it is an ESP32-based modular brick hub that runs a Lua runtime and connects via BLE.

---

## 🖥️ Hardware Overview

### ICRobot (Main Robot Platform)

| Component | Details |
|---|---|
| **Main Processor** | ESP32-S3 |
| **Flash Storage** | 16 MB |
| **PSRAM** | 8 MB |
| **Controller Board** | Arduino Uno R4 WiFi |
| **Mainboard** | s4s Mainboard (I2C `0x0F`) |
| **Drive Motors** | 2× Encoder DC motors (motor IDs 0 & 1) |
| **Arm Servos** | 2-axis servo arm (Servo IDs 0 & 1) |
| **Distance Sensor** | Ultrasonic (I2C `0x57`) |
| **IMU / Gyroscope** | LSM6DS3 (I2C `0x6F`) |
| **Display** | OLED SH1107 128×128 (I2C `0x3C`) |
| **RGB LEDs** | Ambient lights (I2C `0x0F`, register `0x0A`) |
| **Connectivity** | WiFi + BLE (ESP32-S3) |
| **Audio** | I²S audio player |
| **Camera** | AI vision camera module |
| **Battery Monitor** | Internal % + charging status (I2C `0x0F`) |
| **Line Sensor** | 4-channel grayscale (I2C `0x6F`/`0x71`) |

### ICBricks / ICMaster (Modular Brick Hub)

| Component | Details |
|---|---|
| **Processor** | ESP32 (original, not S3) |
| **Framework** | Arduino + ESP-IDF (PlatformIO) |
| **BLE Name** | `IC Bricks` |
| **BLE Service UUID** | `108f94d5-570b-4a6c-9a47-12f428f362e6` |
| **Scripting** | Lua runtime (receives scripts from TinkerCode) |
| **Protocol** | Serial framing: `Lua:` ... `endLua` |
| **Connectivity** | WiFi + BLE |

---

## 🚀 Quick Start

### Path 1 — MicroPython (Easiest)

1. Flash MicroPython firmware to your ICRobot ESP32-S3 (or use the stock firmware)
2. Copy [`micropython/icrobot_open.py`](micropython/icrobot_open.py) to your device
3. Run a beginner example:

```python
from icrobot_open import ICRobot

robot = ICRobot(sda_pin=42, scl_pin=41)
robot.move('forward', duration_sec=2)
robot.move('left', duration_sec=1)
robot.stop()
```

➡️ See [`micropython/examples/`](micropython/examples/) for more!

---

### Path 2 — Arduino / PlatformIO (Advanced)

1. Install [PlatformIO](https://platformio.org/) in VS Code
2. Open the `arduino/` folder as a PlatformIO project
3. Connect your **Arduino Uno R4 WiFi**
4. Build & upload:

```bash
cd arduino/
pio run --target upload
```

```cpp
#include "s4s_mainBoard.h"

s4s_mainBoard hw_main_board;

void setup() {
    hw_main_board.begin();
    // Move forward at speed 80 for 2 seconds
    hw_main_board.encoder_motor_pair_set_dynamic_speed(80, 80);
    hw_main_board.encoder_motor_pair_set_action(1);  // 1 = forward
    delay(2000);
    hw_main_board.encoder_motor_pair_set_action(0);  // 0 = stop
}
```

➡️ See [`arduino/examples/`](arduino/examples/) for complete sketches!

---

### Path 3 — Raw I2C (Reverse Engineering / Custom)

Speak directly to the s4s Mainboard at I2C address `0x0F`:

```python
from machine import I2C, Pin
i2c = I2C(0, sda=Pin(42), scl=Pin(41), freq=400000)

# Move forward (Motor Pair Action register 0xC8 = action 1)
i2c.writeto_mem(0x0F, 0xC8, bytes([1]))

# Read battery level (register 0x00)
batt = i2c.readfrom_mem(0x0F, 0x00, 1)[0]
print(f"Battery: {batt}%")
```

➡️ Full register map in [`docs/hardware/ICRobot_Hardware_Reference.md`](docs/hardware/ICRobot_Hardware_Reference.md)

---

## 📁 Repository Structure

```
ICRobot-OpenSource/
├── README.md                          ← You are here
├── LICENSE                            ← MIT License
├── CONTRIBUTING.md                    ← How to contribute
├── .gitignore
│
├── firmware/                          ← Pre-built .bin firmware files
│   └── (flash with tools/flash_icrobot.sh)
│
├── micropython/                       ← MicroPython library & examples
│   ├── icrobot_open.py                ← Main ICRobot class (I2C-based)
│   └── examples/
│       ├── basic_movement.py          ← Forward, turn, stop
│       ├── arm_control.py             ← Pick-and-place arm example
│       └── obstacle_avoid.py          ← Ultrasonic obstacle avoidance
│
├── arduino/                           ← Arduino/PlatformIO project
│   ├── platformio.ini                 ← PlatformIO config (Uno R4 WiFi)
│   ├── src/                           ← Main Arduino source
│   ├── lib/                           ← s4s Mainboard library
│   │   ├── s4s_mainBoard.h
│   │   └── s4s_mainBoard.cpp
│   └── examples/
│       ├── basic_movement/            ← basic_movement.ino
│       ├── arm_control/               ← arm_control.ino
│       └── obstacle_avoid/            ← obstacle_avoid.ino
│
├── docs/
│   ├── hardware/
│   │   └── ICRobot_Hardware_Reference.md  ← I2C register map, pinout
│   └── protocol/
│       └── ICRobot_Serial_Protocol.md     ← Script upload protocol
│
├── icbricks/
│   └── ICBricks_Protocol.md           ← ICBricks/ICMaster BLE & Lua protocol
│
└── tools/
    ├── flash_icrobot.sh               ← Flash ICRobot ESP32-S3
    └── dump_firmware.sh               ← Back up existing firmware
```

---

## 📖 Documentation

| Document | Description |
|---|---|
| [Hardware Reference](docs/hardware/ICRobot_Hardware_Reference.md) | Full I2C register map, peripheral addresses, motor action codes |
| [Serial Protocol](docs/protocol/ICRobot_Serial_Protocol.md) | Script upload JSON protocol (slots 1–5) |
| [ICBricks Protocol](icbricks/ICBricks_Protocol.md) | BLE, Lua framing, ICMaster controller |
| [MicroPython Library](micropython/icrobot_open.py) | `ICRobot` class with full docstrings |

---

## 🔧 Flashing Tools

### Flash ICRobot Firmware
```bash
./tools/flash_icrobot.sh /dev/cu.usbserial-110
```

### Dump Existing Firmware (Backup)
```bash
./tools/dump_firmware.sh /dev/cu.usbserial-110
```

> **Requires:** `esptool.py` — install with `pip install esptool`

---

## 🤝 Contributing

We welcome contributions! This is a community reverse-engineering project. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Key areas where help is needed:**
- 🔬 Documenting undiscovered I2C registers
- 🎵 Audio / I²S player library
- 📷 Camera module integration
- 🧪 More MicroPython examples
- 🌐 ICBricks custom BLE firmware

---

## ⚠️ Disclaimer

This is an independent open-source project and is **not affiliated with or endorsed by School for Schools (s4s)**. Reverse-engineered register maps and protocol details are provided for educational and interoperability purposes. Use at your own risk — flashing custom firmware may void warranties.

---

## 📄 License

[MIT License](LICENSE) — © ICRobot Open-Source Contributors

---

<p align="center">
  Made with ❤️ by the open-source robotics community<br>
  <i>Empowering educators and students to go beyond the block IDE</i>
</p>
