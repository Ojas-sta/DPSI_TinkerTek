# /flash

Execute firmware flashing workflow for connected robotics hardware:

1. Detect connected serial port: `ls /dev/cu.usbserial* /dev/ttyUSB*`
2. Identify target device (ESP32-S3 for ICRobot, ESP32 for ICBricks)
3. Run `tools/flash_icrobot.sh <PORT>`
4. Confirm flash verification and report completion
