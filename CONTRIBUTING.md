# Contributing to ICRobot & ICBricks Open-Source Project

Thank you for your interest in contributing to the open-source ICRobot and ICBricks ecosystem! This project aims to bring complete hardware freedom, open firmware, and modern programming tools to students, educators, and makers using School For Schools (s4s) educational robotics.

---

## 🛠️ Required Hardware for Testing

To test contributions on physical hardware, having any of the following is helpful:
- **ICRobot** (ESP32-S3 mainboard + 2-axis arm + dual encoder wheels + ultrasonic sensor)
- **ICBricks / ICMaster Hub** (ESP32 Bluetooth Low Energy controller)
- **Arduino Uno R4 WiFi** (Renesas RA4M1 + ESP32-S3 coprocessor)
- Standard USB-to-UART cable (CH340 / CP2102)

---

## 💻 Development Workflow

### MicroPython Development
1. Flash official MicroPython or the dumped firmware onto the ESP32-S3.
2. Use `mpremote`, `rshell`, or Thonny IDE to test your scripts against `micropython/icrobot_open.py`.
3. Follow **PEP 8** style guidelines for all Python code.

### Arduino / C++ Development
1. Install [PlatformIO](https://platformio.org/) (via VS Code or CLI).
2. Open the `arduino/` folder in PlatformIO.
3. Target `[env:uno_r4_wifi]` or custom ESP32 board definitions.
4. Maintain concise, well-documented C++ code with descriptive variable and register names.

---

## 📋 Submitting a Pull Request (PR)

1. **Fork** the repository and create your feature branch:
   ```bash
   git checkout -b feature/awesome-new-capability
   ```
2. **Test** your changes on real hardware or ensure scripts pass syntax checking:
   ```bash
   python3 -m py_compile micropython/icrobot_open.py
   ```
3. **Commit** your changes with clear, descriptive commit messages:
   ```bash
   git commit -m "feat(arm): add smooth interpolated trajectory control for 2-axis arm"
   ```
4. **Push** to your fork and submit a Pull Request against `main`.

---

## 🤝 Community & Support

- Report issues and request features via **GitHub Issues**.
- Share your school projects, 3D printed arm modifications, and custom sensor additions!
