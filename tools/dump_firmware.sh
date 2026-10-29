#!/bin/bash
# =============================================================================
# dump_firmware.sh — Back Up ICRobot ESP32-S3 Flash
# =============================================================================
# Reads the full 16MB flash from an ICRobot and saves it to a timestamped
# backup file in the firmware/ directory.
#
# Usage:
#   ./tools/dump_firmware.sh [PORT]
#
# Arguments:
#   PORT  Serial port of the ICRobot (default: /dev/cu.usbserial-110)
#
# Requirements:
#   pip install esptool
#
# Example:
#   ./tools/dump_firmware.sh /dev/ttyUSB0
#
# ⚠️  IMPORTANT: Run this BEFORE flashing custom firmware so you can restore
#     the original if needed.
#
# Author: ICRobot Open-Source Contributors
# License: MIT
# =============================================================================

set -e

PORT=${1:-/dev/cu.usbserial-110}
OUTFILE="firmware/ICRobot_backup_$(date +%Y%m%d_%H%M%S).bin"

mkdir -p firmware

echo "=================================================="
echo "  ICRobot ESP32-S3 Firmware Backup"
echo "=================================================="
echo "  Port    : $PORT"
echo "  Output  : $OUTFILE"
echo "  Size    : 16 MB (full flash)"
echo "=================================================="
echo ""
echo "Starting dump — this may take 2–3 minutes at 115200 baud..."
echo ""

python3 -m esptool --chip esp32s3 --port "$PORT" --baud 115200 \
  read_flash 0x0 0x1000000 "$OUTFILE"

echo ""
echo "✅ Done: $OUTFILE"
echo "   Size: $(du -sh "$OUTFILE" | cut -f1)"
echo ""
echo "To restore this backup later:"
echo "  esptool.py --chip esp32s3 --port $PORT --baud 460800 write_flash -z 0x0 $OUTFILE"
