#!/bin/bash
# =============================================================================
# flash_icrobot.sh — Flash ICRobot ESP32-S3 Firmware
# =============================================================================
# Usage:
#   ./tools/flash_icrobot.sh [PORT]
#
# Arguments:
#   PORT  Serial port of the ICRobot (default: /dev/cu.usbserial-110)
#
# Requirements:
#   pip install esptool
#
# Example:
#   ./tools/flash_icrobot.sh /dev/ttyUSB0
#   ./tools/flash_icrobot.sh /dev/cu.usbserial-110
#
# Author: ICRobot Open-Source Contributors
# License: MIT
# =============================================================================

set -e

PORT=${1:-/dev/cu.usbserial-110}
FIRMWARE="firmware/ICRobot_firmware.bin"

# Validate firmware file exists
if [ ! -f "$FIRMWARE" ]; then
    echo "ERROR: Firmware file not found: $FIRMWARE"
    echo "Place your firmware binary at: $FIRMWARE"
    echo "Or download from the firmware/ directory of this repo."
    exit 1
fi

echo "=================================================="
echo "  ICRobot ESP32-S3 Firmware Flasher"
echo "=================================================="
echo "  Port     : $PORT"
echo "  Firmware : $FIRMWARE"
echo "  Chip     : ESP32-S3"
echo "  Baud     : 460800"
echo "=================================================="
echo ""
echo "Flashing in 3 seconds... Press Ctrl+C to abort."
sleep 3

esptool.py --chip esp32s3 --port "$PORT" --baud 460800 \
  write_flash -z 0x0 "$FIRMWARE"

echo ""
echo "✅ Flash complete! Reset the robot to boot the new firmware."
