"""
ICRobot MicroPython Example — Basic Movement
=============================================
Demonstrates forward driving, turning, and stopping using
the ICRobot open-source library.

Hardware: ICRobot (ESP32-S3 + s4s Mainboard)
Library:  icrobot_open.py (must be on the device)

Sequence:
  1. Move forward for 2 seconds
  2. Turn left for ~0.6 seconds
  3. Move forward for 2 more seconds
  4. Stop

Author: ICRobot Open-Source Contributors
License: MIT
"""

import time
from icrobot_open import ICRobot

# ── Initialise ──────────────────────────────────────────────────────────────
robot = ICRobot(sda_pin=42, scl_pin=41)

print("ICRobot Basic Movement Example")
print(f"Battery: {robot.get_battery_pct()}%")

# Flash green to signal ready
robot.set_rgb(0, 255, 0, brightness=100)
time.sleep(0.5)
robot.set_rgb(0, 0, 0, brightness=0)

# ── Sequence ─────────────────────────────────────────────────────────────────

# Step 1: Forward 2 seconds
print("Moving forward...")
robot.move('forward', duration_sec=2, speed=70)

time.sleep(0.3)  # brief pause between moves

# Step 2: Turn left for ~0.6 seconds (adjust timing for your surface)
print("Turning left...")
robot.move('left', duration_sec=0.6, speed=60)

time.sleep(0.3)

# Step 3: Forward 2 more seconds
print("Moving forward again...")
robot.move('forward', duration_sec=2, speed=70)

# Step 4: Stop
print("Stopping.")
robot.stop()

# Flash blue to signal done
robot.set_rgb(0, 0, 255, brightness=100)
time.sleep(1)
robot.set_rgb(0, 0, 0, brightness=0)

print("Done!")
