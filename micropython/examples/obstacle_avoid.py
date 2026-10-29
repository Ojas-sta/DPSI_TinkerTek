"""
ICRobot MicroPython Example — Ultrasonic Obstacle Avoidance
============================================================
The robot continuously drives forward, measures the distance
to obstacles with the ultrasonic sensor, and turns away when
something gets too close.

Hardware: ICRobot (ESP32-S3 + s4s Mainboard + Ultrasonic I2C 0x57)
Library:  icrobot_open.py (must be on the device)

Behaviour
---------
  • Distance > SAFE_DIST_CM     → drive forward
  • WARN_DIST_CM < d ≤ SAFE     → slow down
  • Distance ≤ WARN_DIST_CM     → stop, back up, turn, continue

Press Ctrl+C to stop.

Author: ICRobot Open-Source Contributors
License: MIT
"""

import time
from icrobot_open import ICRobot

# ── Tuning constants ──────────────────────────────────────────────────────────
SAFE_DIST_CM   = 30    # cm — free to drive at full speed
WARN_DIST_CM   = 15    # cm — obstacle detected, must avoid
SPEED_NORMAL   = 70    # motor speed when clear
SPEED_SLOW     = 40    # motor speed when in warning zone
BACKUP_SEC     = 0.5   # how long to reverse when blocked
TURN_SEC       = 0.6   # how long to turn when blocked
POLL_MS        = 100   # sensor poll interval in milliseconds

# ── Initialise ────────────────────────────────────────────────────────────────
robot = ICRobot(sda_pin=42, scl_pin=41)

print("ICRobot Obstacle Avoidance — Press Ctrl+C to stop")
print(f"Battery: {robot.get_battery_pct()}%")
print(f"Safe distance: {SAFE_DIST_CM} cm  |  Avoid distance: {WARN_DIST_CM} cm")

robot.set_rgb(0, 200, 0, brightness=100)   # green = running
time.sleep(0.5)


# ── Main loop ─────────────────────────────────────────────────────────────────
try:
    while True:
        dist = robot.get_distance_cm()

        if dist == 0:
            # Sensor error or out-of-range — treat as clear
            robot.move('forward', speed=SPEED_SLOW)
            time.sleep_ms(POLL_MS)
            continue

        if dist > SAFE_DIST_CM:
            # Clear ahead — drive forward at normal speed
            robot.set_rgb(0, 200, 0, brightness=80)   # green
            robot.move('forward', speed=SPEED_NORMAL)

        elif dist > WARN_DIST_CM:
            # Getting close — slow down
            robot.set_rgb(255, 165, 0, brightness=100)  # orange
            robot.move('forward', speed=SPEED_SLOW)

        else:
            # Too close — avoid!
            robot.set_rgb(255, 0, 0, brightness=150)   # red = obstacle!
            print(f"  Obstacle at {dist} cm — avoiding!")

            # Stop
            robot.stop()
            time.sleep(0.2)

            # Back up
            robot.move('backward', duration_sec=BACKUP_SEC, speed=SPEED_NORMAL)
            time.sleep(0.1)

            # Turn right to avoid obstacle
            robot.move('right', duration_sec=TURN_SEC, speed=SPEED_NORMAL)
            time.sleep(0.1)

            robot.set_rgb(0, 200, 0, brightness=80)    # back to green

        time.sleep_ms(POLL_MS)

except KeyboardInterrupt:
    print("\nStopped by user.")
    robot.stop()
    robot.set_rgb(0, 0, 0, brightness=0)
    print("Done!")
