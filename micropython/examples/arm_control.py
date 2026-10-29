"""
ICRobot MicroPython Example — Arm Control (Pick and Place)
===========================================================
Demonstrates controlling the 2-axis servo arm on the ICRobot.

Hardware: ICRobot (ESP32-S3 + s4s Mainboard)
Library:  icrobot_open.py (must be on the device)

Servo IDs
---------
  Servo 0 (axis1): Base / elevation axis  — I2C register 0x1E
  Servo 1 (axis2): Gripper               — I2C register 0x1F

Angle Reference
---------------
  axis1: 0°=fully lowered, 90°=horizontal, 180°=fully raised
  axis2: 0°=gripper closed, 90°=half-open, 180°=fully open

Sequence (Pick-and-Place Loop):
  1. Home position (both 90°)
  2. Open gripper
  3. Lower arm over object
  4. Close gripper (pick)
  5. Raise arm
  6. Open gripper (place)
  7. Return to home
  8. Release servos (power saving)
  9. Repeat 3 times

Author: ICRobot Open-Source Contributors
License: MIT
"""

import time
from icrobot_open import ICRobot

# ── Config ───────────────────────────────────────────────────────────────────
ARM_HOME_AXIS1    = 90    # degrees — arm horizontal
ARM_HOME_AXIS2    = 90    # degrees — gripper half-open
ARM_LOWER_AXIS1   = 30    # degrees — arm lowered to pick position
GRIPPER_OPEN      = 150   # degrees — gripper open
GRIPPER_CLOSED    = 40    # degrees — gripper closed (gripping object)
MOVE_DELAY        = 0.6   # seconds — wait for servo to reach position
CYCLES            = 3     # number of pick-and-place cycles

# ── Initialise ───────────────────────────────────────────────────────────────
robot = ICRobot(sda_pin=42, scl_pin=41)

print("ICRobot Arm Control Example")
print(f"Battery: {robot.get_battery_pct()}%")


def arm_home():
    """Move arm to home (rest) position."""
    robot.set_arm(ARM_HOME_AXIS1, ARM_HOME_AXIS2)
    time.sleep(MOVE_DELAY)


def pick():
    """Lower arm and close gripper to pick up an object."""
    print("  Opening gripper...")
    robot.set_arm(ARM_HOME_AXIS1, GRIPPER_OPEN)
    time.sleep(MOVE_DELAY)

    print("  Lowering arm...")
    robot.set_arm(ARM_LOWER_AXIS1, GRIPPER_OPEN)
    time.sleep(MOVE_DELAY)

    print("  Closing gripper (pick)...")
    robot.set_arm(ARM_LOWER_AXIS1, GRIPPER_CLOSED)
    time.sleep(MOVE_DELAY)

    print("  Raising arm...")
    robot.set_arm(ARM_HOME_AXIS1, GRIPPER_CLOSED)
    time.sleep(MOVE_DELAY)


def place():
    """Open gripper to release/place the held object."""
    print("  Placing — opening gripper...")
    robot.set_arm(ARM_HOME_AXIS1, GRIPPER_OPEN)
    time.sleep(MOVE_DELAY)


# ── Main Loop ─────────────────────────────────────────────────────────────────
print("Starting pick-and-place loop...")
arm_home()
time.sleep(0.5)

for cycle in range(1, CYCLES + 1):
    print(f"\n── Cycle {cycle}/{CYCLES} ──")
    robot.set_rgb(255, 165, 0, brightness=80)   # orange = working

    pick()
    place()
    arm_home()

    robot.set_rgb(0, 255, 0, brightness=50)     # green = cycle done
    time.sleep(0.5)

# Power down servos after task
print("\nTask complete — releasing servos.")
robot.release_arm()
robot.set_rgb(0, 0, 0, brightness=0)
print("Done!")
