# ICBricks / ICMaster Platform — Protocol & Architecture

> **Platform:** ICBricks / ICMaster (ESP32-based modular brick hub)  
> **Made by:** School for Schools (s4s)  
> **Document version:** 1.0 — ICRobot Open-Source Contributors

---

## Overview

**ICBricks** is a modular robotics brick system built on the **ESP32** microcontroller (the original ESP32, not the S3 variant). It is designed to be controlled via the **TinkerCode** block-based IDE over BLE or USB serial.

**ICMaster** is the central controller brick that receives Lua scripts from TinkerCode and executes them to orchestrate the connected brick modules (motors, sensors, lights, etc.).

This document describes the hardware, BLE protocol, and serial framing format — enabling community developers to build custom firmware or connect alternative controllers.

---

## Hardware Specifications

| Property | Value |
|----------|-------|
| **Processor** | ESP32 (Xtensa LX6 dual-core, original — not S3) |
| **Framework** | Arduino + ESP-IDF |
| **Build system** | PlatformIO (`framework-arduinoespressif32`) |
| **Connectivity** | WiFi 802.11 b/g/n + BLE 4.2 |
| **Scripting runtime** | Lua (executed on the ESP32) |
| **Firmware file** | `ICBricks_firmware_v2.1(0x0).bin` |
| **Flash address** | `0x0` (full firmware image) |

---

## BLE Advertisement

The ICMaster advertises itself over BLE with the following identity:

| Property | Value |
|----------|-------|
| **Advertised name** | `IC Bricks` |
| **Service UUID** | `108f94d5-570b-4a6c-9a47-12f428f362e6` |

### Connecting via Python (bleak)

```python
import asyncio
from bleak import BleakClient, BleakScanner

SERVICE_UUID = "108f94d5-570b-4a6c-9a47-12f428f362e6"

async def find_icbricks():
    devices = await BleakScanner.discover(timeout=5.0)
    for d in devices:
        if d.name and "IC Bricks" in d.name:
            print(f"Found ICBricks: {d.address}")
            return d.address
    return None

asyncio.run(find_icbricks())
```

---

## Serial / BLE Script Protocol — Lua Framing

TinkerCode uploads Lua scripts to the ICMaster using a simple **delimiter-framed** text protocol. The same framing is used over both BLE (GATT write) and USB serial.

### Frame Format

```
Lua:<lua_source_code>endLua
```

| Part | Description |
|------|-------------|
| `Lua:` | Start delimiter — signals the beginning of a Lua script |
| `<lua_source_code>` | The full Lua script body (UTF-8 text) |
| `endLua` | End delimiter — triggers execution of the script |

### Example — Move a motor brick forward

```
Lua:
motor.setSpeed(1, 80)
motor.forward(1)
wait(2000)
motor.stop(1)
endLua
```

### Sending over serial (Python example)

```python
import serial
import time

ser = serial.Serial('/dev/cu.usbserial-110', 115200, timeout=2)
time.sleep(1)

lua_script = """
motor.setSpeed(1, 80)
motor.forward(1)
wait(2000)
motor.stop(1)
"""

payload = f"Lua:{lua_script}endLua"
ser.write(payload.encode('utf-8'))
time.sleep(3)
ser.close()
```

---

## Firmware Flashing

### Pre-built Firmware

| File | Target | Flash Address | Notes |
|------|--------|---------------|-------|
| `ICBricks_firmware_v2.1(0x0).bin` | ESP32 (original) | `0x0` | Official stock firmware |

### Flash Command

```bash
# Using esptool.py
esptool.py --chip esp32 --port /dev/cu.usbserial-110 --baud 460800 \
  write_flash -z 0x0 ICBricks_firmware_v2.1\(0x0\).bin
```

> **Important:** ICBricks uses the original **ESP32** (not ESP32-S3). Do not use `--chip esp32s3`.

### Backup Existing Firmware First

```bash
esptool.py --chip esp32 --port /dev/cu.usbserial-110 \
  read_flash 0x0 0x400000 icbricks_backup.bin
```

---

## Open-Source Replacement Options

Since the ICBricks protocol is now documented, you can replace the stock Lua firmware with a fully open alternative:

### Option 1 — MicroPython

Flash MicroPython for ESP32 and write Python scripts that accept BLE commands using the same service UUID:

```bash
# Flash MicroPython (ESP32 generic)
esptool.py --chip esp32 --port /dev/cu.usbserial-110 \
  write_flash -z 0x1000 esp32-micropython.bin
```

Then deploy a BLE server script that accepts the `Lua:...endLua` framing and interprets commands.

### Option 2 — Custom Arduino Sketch

Write an Arduino sketch (PlatformIO, `framework-arduinoespressif32`) that:
1. Advertises as `IC Bricks` with the same service UUID
2. Accepts BLE GATT writes
3. Parses the `Lua:...endLua` framing
4. Maps Lua function calls to motor/sensor control code

This allows TinkerCode to continue working as a frontend while you control the hardware with custom logic.

---

## ICMaster Controller Role

```
TinkerCode IDE  ─── BLE / USB ──►  ICMaster (ESP32)
                                        │
                                  Parses Lua script
                                        │
                         ┌──────────────┼──────────────┐
                         ▼              ▼              ▼
                    Motor Bricks   Sensor Bricks   LED Bricks
```

The ICMaster is the central hub that:
- Receives Lua scripts from TinkerCode
- Executes them locally on the ESP32
- Communicates with attached brick modules (motors, sensors, LEDs) over its own internal bus

---

## Related Files

| File | Description |
|------|-------------|
| `ICBricks_firmware_v2.1(0x0).bin` | Stock ESP32 firmware (flash at 0x0) |
| `ICBricks_Master1.0_V3.3.4T2.bin` | ICMaster alternate firmware version |
| `tools/flash_icrobot.sh` | Flash script (adapt `--chip` for ESP32) |

---

## Disclaimer

This documentation was produced by reverse-engineering and community research. It is not officially supported by School for Schools (s4s). Use at your own risk.
