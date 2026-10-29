# /test-robot

Run diagnostic hardware test suite:

1. Connect to MicroPython REPL via serial port
2. Test I2C probe on `0x0F` (Mainboard), `0x57` (Ultrasonic), `0x3C` (OLED)
3. Check battery voltage and charging flag
4. Exercise 2-axis arm (Axis 1: 90°, Axis 2: 45°) and release
5. Execute short forward wheel tick (100ms)
6. Output PASS/FAIL hardware diagnostic report
