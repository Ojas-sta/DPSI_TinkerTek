# DPSI_TinkerTek Project Roadmap

## Phase 1: Reverse Engineering & Foundation (Complete) ✅
- [x] Extract and back up factory firmware images (ESP32-S3 16MB, ICBricks, micro:bit)
- [x] Document I2C register map for `0x0F` (Motors, 2-Axis Arm, Battery, Voice, RTC)
- [x] Document Arduino Uno R4 WiFi role (Renesas RA4M1 main MCU + ESP32-S3 WiFi bridge)
- [x] Create open-source MicroPython library (`icrobot_open.py`)
- [x] Create standalone Arduino examples (PlatformIO & Arduino IDE ready)
- [x] Implement Agentic OS kernel and specialist agent registry

## Phase 2: Community & Extension (In Progress) ⏳
- [ ] Add inverse kinematics helper for the 2-axis arm (calculate angles for (x, y) coordinates)
- [ ] Develop WebREPL / WebBluetooth browser controller
- [ ] Create 3D printable chassis and arm replacement models
- [ ] Add ROS2 micro-XRCE-DDS bridge for advanced robotics research
