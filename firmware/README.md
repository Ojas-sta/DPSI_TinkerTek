# Factory Firmware Binaries & Flashing Guide

This directory contains the original factory binaries preserved from the TinkerTek / School For Schools distribution, enabling 100% factory restoration or comparison with your open-source code.

---

## 📦 Firmware Files Summary

| File | Target Hardware | Chipset | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `s4s_esp32_v1.0.0.bin` | **ICRobot** | ESP32-S3 (16MB Flash) | 16 MB | Full factory MicroPython system image including runtime, camera, and WiFi bridge |
| `icrobot.mpy` | **ICRobot** | MicroPython Bytecode | 30 KB | Precompiled hardware abstraction library (`Motor`, `Gripper`, `Power`, `Taillight`) |
| `ICBricks_firmware_v2.1.bin` | **ICBricks** | ESP32 | 1.1 MB | Standard ICBricks hub firmware |
| `ICBricks_Master1.0_V3.3.4T2.bin` | **ICMaster** | ESP32 | 2.3 MB | ICBricks Master controller firmware with BLE & Lua runtime |
| `Microbit_LinkBot_V1.0.0.hex` | **micro:bit** | nRF51 / nRF52 | 1.2 MB | micro:bit LinkBot robotic firmware |

---

## ⚡ Flashing Instructions

### 1. ICRobot (ESP32-S3)
To flash the full 16MB image to the robot:
```bash
python3 -m esptool --chip esp32s3 --port /dev/cu.usbserial-110 --baud 460800 write-flash -z 0x0 s4s_esp32_v1.0.0.bin
```

### 2. ICBricks / ICMaster (ESP32)
```bash
python3 -m esptool --chip esp32 --port /dev/cu.usbserial-110 --baud 460800 write-flash -z 0x0 ICBricks_Master1.0_V3.3.4T2.bin
```

### 3. BBC micro:bit
Drag and drop `Microbit_LinkBot_V1.0.0.hex` directly onto the mounted `MICROBIT` USB drive, or flash via DAPLink:
```bash
# Via pyocd or dapjs
pyocd flash -t microbit Microbit_LinkBot_V1.0.0.hex
```
