# ADR 001: Reverse Engineering and Open-Sourcing School For Schools Robotics

- **Date**: 2026-10-29
- **Status**: Accepted
- **Author**: DPSI_TinkerTek Contributors

## Context
Educational robotics hardware supplied by "School For Schools" (s4s) for TinkerTek was locked inside a closed Electron application (`TinkerTek-alpha-V0.1.5`). The hardware consisted of an ESP32-S3 robot with 2 drive wheels, a 2-axis servo arm, ultrasonic distance sensing, an OLED screen, and an Arduino Uno R4 WiFi controller.

## Decision
1. Extract the clean 16MB factory firmware image (`s4s_esp32_v1.0.0.bin`) and ICBricks binaries.
2. Reverse-engineer the primary I2C register map on slave address `0x0F` (Servos: `0x1E-0x23`, Motors: `0xC8-0xCD`, Battery: `0x00`).
3. Build a standalone, dependency-free MicroPython class (`icrobot_open.py`) and standard Arduino C++ library (`s4s_mainBoard.h/cpp`).
4. Re-architect the workspace as an **Agentic OS** repository for sustainable multi-agent open-source maintenance.

## Consequences
- Students and educators can program the robot directly via standard Python/C++ with zero proprietary locks.
