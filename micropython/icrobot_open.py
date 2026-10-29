"""
ICRobot Open-Source MicroPython Library
========================================
Hardware: ESP32-S3 + s4s Mainboard Controller (I2C addr 0x0F)

Peripheral Map
--------------
2 Encoder Wheels  - I2C 0x0F registers 0xC8-0xCC  (motor pair control)
2-Axis Servo Arm  - I2C 0x0F registers 0x1E-0x23
Ultrasonic Sensor - I2C 0x57
RGB LEDs          - I2C 0x0F registers 0x0A
Battery Monitor   - I2C 0x0F registers 0x00-0x04
Gyro / IMU        - I2C 0x6F (LSM6DS3)

Register Reference (Mainboard 0x0F)
-------------------------------------
| Register | Offset | Description                     |
|----------|--------|---------------------------------|
| 0x00     | +0     | Battery level (0–100%)          |
| 0x00     | +1     | External battery voltage (/10)  |
| 0x00     | +2     | Charging status (1=yes)         |
| 0x00     | +3     | Fully charged (1=yes)           |
| 0x00     | +4..6  | Firmware version [maj,min,pat]  |
| 0x0A     | +0     | RGB brightness (0–255)          |
| 0x0A     | +1..3  | RGB colour [R, G, B]            |
| 0x1E     | +0     | Servo 0 angle (0–180°)          |
| 0x1E     | +1     | Servo 1 angle (0–180°)          |
| 0x1E     | +2     | Cont. servo 0 speed (-100–100)  |
| 0x1E     | +3     | Cont. servo 1 speed (-100–100)  |
| 0x1E     | +4     | Servo 0 release (write 0x00)    |
| 0x1E     | +5     | Servo 1 release (write 0x00)    |
| 0xC8     | +0     | Motor pair action code          |
| 0xC8     | +1..2  | Motor pair group [L_id, R_id]   |
| 0xC8     | +2..5  | Motor pair speed [Lhi,Llo,Rhi,Rlo] |
| 0xC8     | +3..4  | Motor pair run time (ms, uint16)|
| 0xC8     | +5..6  | Motor pair distance (cm, uint16)|

Motor Pair Action Codes
-----------------------
  0  = stop
  1  = forward  (speed mode)
  2  = backward (speed mode)
  3  = turn left
  4  = turn right
  5  = forward  (timed)
  6  = backward (timed)
  ...
  13 = forward  (distance/cm)
  14 = backward (distance/cm)
  15 = turn left (distance)
  16 = turn right (distance)

Author: ICRobot Open-Source Contributors
License: MIT
"""

import time
from machine import I2C, Pin

# ---------------------------------------------------------------------------
# I2C Device Addresses
# ---------------------------------------------------------------------------
_MAINBOARD_ADDR = 0x0F   # s4s Mainboard controller
_ULTR_ADDR      = 0x57   # Ultrasonic distance sensor
_GYRO_ADDR      = 0x6F   # LSM6DS3 IMU (also shared with line sensor)

# ---------------------------------------------------------------------------
# Mainboard Register Base Addresses
# ---------------------------------------------------------------------------
_REG_CHARGING       = 0x00   # Battery / charging management
_REG_AMBIENT_LIGHT  = 0x0A   # RGB LED control
_REG_SERVO          = 0x1E   # Servo angle / speed / release
_REG_MOTOR_PAIR     = 0xC8   # Encoder motor pair control

# ---------------------------------------------------------------------------
# Motor Pair Action Codes
# ---------------------------------------------------------------------------
ACTION_STOP          = 0
ACTION_FWD_SPEED     = 1
ACTION_BWD_SPEED     = 2
ACTION_LEFT_SPEED    = 3
ACTION_RIGHT_SPEED   = 4
ACTION_FWD_TIME      = 5
ACTION_BWD_TIME      = 6
ACTION_LEFT_TIME     = 7
ACTION_RIGHT_TIME    = 8
ACTION_FWD_CM        = 13
ACTION_BWD_CM        = 14
ACTION_LEFT_CM       = 15
ACTION_RIGHT_CM      = 16


class ICRobot:
    """
    High-level driver for the ICRobot wheeled robot platform.

    This class wraps all I2C communication with the s4s Mainboard (0x0F)
    and the onboard ultrasonic sensor (0x57) into easy-to-use methods.

    Hardware: ESP32-S3 with s4s Mainboard
    Default I2C pins: SDA=42, SCL=41 (on ESP32-S3 ICRobot mainboard)

    Example
    -------
    >>> from icrobot_open import ICRobot
    >>> robot = ICRobot()       # uses default pins 42/41
    >>> robot.move('forward', duration_sec=2)
    >>> robot.set_arm(90, 45)
    >>> print(robot.get_distance_cm())
    >>> robot.stop()
    """

    # Default I2C pins for the ICRobot ESP32-S3 mainboard
    DEFAULT_SDA = 42
    DEFAULT_SCL = 41

    # Default I2C frequency
    I2C_FREQ = 400_000

    # Left motor ID, right motor ID (as wired on ICRobot)
    LEFT_MOTOR_ID  = 0
    RIGHT_MOTOR_ID = 1

    def __init__(self, sda_pin: int = DEFAULT_SDA, scl_pin: int = DEFAULT_SCL):
        """
        Initialise the ICRobot I2C interface.

        Parameters
        ----------
        sda_pin : int
            GPIO pin number for I2C SDA. Default 42.
        scl_pin : int
            GPIO pin number for I2C SCL. Default 41.

        Raises
        ------
        OSError
            If the I2C bus cannot be initialised.
        """
        self._i2c = I2C(0, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=self.I2C_FREQ)
        self._ultr_last_cm = 0
        self._ultr_last_tick = 0

        # Set motor pair to use motor IDs 0 (left) and 1 (right)
        self._set_motor_pair_group(self.LEFT_MOTOR_ID, self.RIGHT_MOTOR_ID)

    # -----------------------------------------------------------------------
    # Low-level I2C helpers
    # -----------------------------------------------------------------------

    def _write_reg(self, addr: int, reg: int, data: bytes) -> None:
        """Write bytes to a register on an I2C device."""
        self._i2c.writeto_mem(addr, reg, data)

    def _read_reg(self, addr: int, reg: int, n: int) -> bytes:
        """Read n bytes from a register on an I2C device."""
        return self._i2c.readfrom_mem(addr, reg, n)

    def _write_raw(self, addr: int, data: bytes) -> None:
        """Write raw bytes to an I2C device (no register prefix)."""
        self._i2c.writeto(addr, data)

    def _read_raw(self, addr: int, n: int) -> bytes:
        """Read raw bytes from an I2C device."""
        return self._i2c.readfrom(addr, n)

    # -----------------------------------------------------------------------
    # Motor helpers
    # -----------------------------------------------------------------------

    def _set_motor_pair_group(self, left_id: int, right_id: int) -> None:
        """Configure which motor IDs are the left and right wheels."""
        self._write_reg(_MAINBOARD_ADDR, _REG_MOTOR_PAIR + 1, bytes([left_id, right_id]))

    def _set_motor_pair_speed(self, left_speed: int, right_speed: int) -> None:
        """
        Set the dynamic speed for the motor pair.

        Parameters
        ----------
        left_speed : int
            Left motor speed, 0–100.
        right_speed : int
            Right motor speed, 0–100.
        """
        l = max(0, min(100, abs(left_speed)))
        r = max(0, min(100, abs(right_speed)))
        data = bytes([
            (l >> 8) & 0xFF, l & 0xFF,
            (r >> 8) & 0xFF, r & 0xFF,
        ])
        self._write_reg(_MAINBOARD_ADDR, _REG_MOTOR_PAIR + 2, data)

    def _set_motor_pair_action(self, action: int) -> None:
        """Send a motor pair action command."""
        self._write_reg(_MAINBOARD_ADDR, _REG_MOTOR_PAIR + 0, bytes([action]))

    def _set_motor_pair_time_ms(self, ms: int) -> None:
        """Set the motor pair run duration in milliseconds."""
        data = bytes([(ms >> 8) & 0xFF, ms & 0xFF])
        self._write_reg(_MAINBOARD_ADDR, _REG_MOTOR_PAIR + 3, data)

    def _set_motor_pair_distance_cm(self, cm: int) -> None:
        """Set the motor pair run distance in centimeters."""
        data = bytes([(cm >> 8) & 0xFF, cm & 0xFF,
                      (cm >> 8) & 0xFF, cm & 0xFF])
        self._write_reg(_MAINBOARD_ADDR, _REG_MOTOR_PAIR + 5, data)

    # -----------------------------------------------------------------------
    # Public API — Movement
    # -----------------------------------------------------------------------

    def drive(self, left_speed: int, right_speed: int) -> None:
        """
        Drive the robot with independent left/right motor speeds.

        Parameters
        ----------
        left_speed : int
            Speed for the left motor. Range: -100 (reverse) to 100 (forward).
        right_speed : int
            Speed for the right motor. Range: -100 (reverse) to 100 (forward).

        Example
        -------
        >>> robot.drive(80, 80)    # full forward
        >>> robot.drive(-50, 50)   # spin left on the spot
        >>> robot.drive(0, 0)      # stop
        """
        # Determine action from sign of speeds
        if left_speed == 0 and right_speed == 0:
            self._set_motor_pair_action(ACTION_STOP)
            return

        # For simplicity: set speed magnitudes then action
        l_abs = abs(left_speed)
        r_abs = abs(right_speed)
        self._set_motor_pair_speed(l_abs, r_abs)

        if left_speed >= 0 and right_speed >= 0:
            action = ACTION_FWD_SPEED
        elif left_speed <= 0 and right_speed <= 0:
            action = ACTION_BWD_SPEED
        elif left_speed <= 0 and right_speed >= 0:
            action = ACTION_LEFT_SPEED
        else:
            action = ACTION_RIGHT_SPEED

        self._set_motor_pair_action(action)

    def move(self, direction: str, duration_sec: float = None, speed: int = 70) -> None:
        """
        Move the robot in a named direction, optionally for a fixed duration.

        Parameters
        ----------
        direction : str
            One of: 'forward', 'backward', 'left', 'right', 'stop'.
        duration_sec : float, optional
            How long to move, in seconds. If None, the robot moves continuously
            until another command is sent.
        speed : int
            Motor speed percentage (0–100). Default 70.

        Example
        -------
        >>> robot.move('forward', duration_sec=2)
        >>> robot.move('left', duration_sec=0.5)
        >>> robot.move('stop')
        """
        direction = direction.lower().strip()

        action_map = {
            'forward':  ACTION_FWD_SPEED,
            'backward': ACTION_BWD_SPEED,
            'left':     ACTION_LEFT_SPEED,
            'right':    ACTION_RIGHT_SPEED,
            'stop':     ACTION_STOP,
        }

        if direction not in action_map:
            raise ValueError(f"Unknown direction '{direction}'. Use: {list(action_map.keys())}")

        if direction != 'stop':
            self._set_motor_pair_speed(speed, speed)

        self._set_motor_pair_action(action_map[direction])

        if duration_sec is not None and direction != 'stop':
            time.sleep(duration_sec)
            self._set_motor_pair_action(ACTION_STOP)

    def move_cm(self, direction: str, centimeters: int, speed: int = 70) -> None:
        """
        Move the robot a specific distance in centimeters using encoder feedback.

        Parameters
        ----------
        direction : str
            One of: 'forward', 'backward', 'left', 'right'.
        centimeters : int
            Distance to travel in centimeters (must be positive).
        speed : int
            Motor speed percentage (0–100). Default 70.

        Example
        -------
        >>> robot.move_cm('forward', 30)   # move 30 cm forward
        >>> robot.move_cm('backward', 15)
        """
        if centimeters <= 0:
            raise ValueError("centimeters must be a positive integer")

        direction = direction.lower().strip()
        action_map = {
            'forward':  ACTION_FWD_CM,
            'backward': ACTION_BWD_CM,
            'left':     ACTION_LEFT_CM,
            'right':    ACTION_RIGHT_CM,
        }

        if direction not in action_map:
            raise ValueError(f"direction must be one of: {list(action_map.keys())}")

        self._set_motor_pair_speed(speed, speed)
        self._set_motor_pair_distance_cm(centimeters)
        self._set_motor_pair_action(action_map[direction])

    # -----------------------------------------------------------------------
    # Public API — Arm / Servos
    # -----------------------------------------------------------------------

    def set_arm(self, axis1_angle: int, axis2_angle: int) -> None:
        """
        Set the 2-axis servo arm to the given angles.

        Parameters
        ----------
        axis1_angle : int
            Angle for servo 0 (base / elevation). Range: 0–180 degrees.
        axis2_angle : int
            Angle for servo 1 (gripper). Range: 0–180 degrees.

        Example
        -------
        >>> robot.set_arm(90, 90)    # both axes to 90°
        >>> robot.set_arm(45, 130)   # base down, gripper open
        """
        a1 = max(0, min(180, axis1_angle))
        a2 = max(0, min(180, axis2_angle))
        # Servo 0 at register 0x1E, Servo 1 at register 0x1F
        self._write_reg(_MAINBOARD_ADDR, _REG_SERVO + 0, bytes([a1]))
        self._write_reg(_MAINBOARD_ADDR, _REG_SERVO + 1, bytes([a2]))

    def release_arm(self) -> None:
        """
        De-energize both arm servos, allowing them to move freely.

        This reduces servo heat and power draw when the arm does not need
        to hold a position.

        Example
        -------
        >>> robot.release_arm()
        """
        # Servo 0 release at 0x22 (0x1E + 4), Servo 1 release at 0x23 (0x1E + 5)
        self._write_reg(_MAINBOARD_ADDR, _REG_SERVO + 4, bytes([0x00]))
        self._write_reg(_MAINBOARD_ADDR, _REG_SERVO + 5, bytes([0x00]))

    # -----------------------------------------------------------------------
    # Public API — Ultrasonic Sensor
    # -----------------------------------------------------------------------

    def get_distance_cm(self) -> int:
        """
        Read the ultrasonic distance sensor.

        Returns the distance to the nearest obstacle in centimeters.
        Consecutive calls within 50 ms return the cached value (hardware
        limitation — the sensor needs time between measurements).

        Returns
        -------
        int
            Distance in centimeters. Returns last cached value if called
            within 50 ms of the previous read.

        Example
        -------
        >>> dist = robot.get_distance_cm()
        >>> print(f"Obstacle at {dist} cm")
        """
        now = time.ticks_ms()
        if time.ticks_diff(now, self._ultr_last_tick) < 50:
            return self._ultr_last_cm

        self._ultr_last_tick = now
        try:
            data = self._read_reg(_ULTR_ADDR, 0x01, 3)
            # Raw value is in units of 0.1 mm: reconstruct as 24-bit big-endian
            raw = (data[0] << 16) | (data[1] << 8) | data[0]
            self._ultr_last_cm = raw // 10000
        except OSError:
            pass  # Keep last value on I2C error

        return self._ultr_last_cm

    # -----------------------------------------------------------------------
    # Public API — RGB LEDs
    # -----------------------------------------------------------------------

    def set_rgb(self, r: int, g: int, b: int, brightness: int = 125) -> None:
        """
        Set the onboard RGB ambient LED colour and brightness.

        Parameters
        ----------
        r : int
            Red channel, 0–255.
        g : int
            Green channel, 0–255.
        b : int
            Blue channel, 0–255.
        brightness : int
            Overall brightness, 0–255. Default 125 (half brightness).

        Example
        -------
        >>> robot.set_rgb(255, 0, 0)             # red
        >>> robot.set_rgb(0, 255, 0, brightness=200)  # bright green
        >>> robot.set_rgb(0, 0, 0, brightness=0)      # off
        """
        bri = max(0, min(255, brightness))
        self._write_reg(_MAINBOARD_ADDR, _REG_AMBIENT_LIGHT + 0, bytes([bri]))
        self._write_reg(_MAINBOARD_ADDR, _REG_AMBIENT_LIGHT + 1,
                        bytes([max(0, min(255, r)),
                               max(0, min(255, g)),
                               max(0, min(255, b))]))

    # -----------------------------------------------------------------------
    # Public API — Battery
    # -----------------------------------------------------------------------

    def get_battery_pct(self) -> int:
        """
        Read the internal battery level as a percentage.

        Returns
        -------
        int
            Battery percentage, 0–100. Returns -1 on I2C error.

        Example
        -------
        >>> batt = robot.get_battery_pct()
        >>> print(f"Battery: {batt}%")
        """
        try:
            data = self._read_reg(_MAINBOARD_ADDR, _REG_CHARGING + 0, 1)
            return data[0]
        except OSError:
            return -1

    def is_charging(self) -> bool:
        """
        Check if the robot is currently charging.

        Returns
        -------
        bool
            True if charging, False otherwise.
        """
        try:
            data = self._read_reg(_MAINBOARD_ADDR, _REG_CHARGING + 2, 1)
            return bool(data[0])
        except OSError:
            return False

    # -----------------------------------------------------------------------
    # Public API — Emergency Stop
    # -----------------------------------------------------------------------

    def stop(self) -> None:
        """
        Emergency stop — immediately halt all motors and release servos.

        Also turns off RGB LEDs.

        Example
        -------
        >>> robot.stop()
        """
        try:
            self._set_motor_pair_action(ACTION_STOP)
        except OSError:
            pass
        try:
            self.release_arm()
        except OSError:
            pass
        try:
            self.set_rgb(0, 0, 0, brightness=0)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Usage example
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    import time

    print("ICRobot Open-Source Library — Demo")
    robot = ICRobot(sda_pin=42, scl_pin=41)

    # Battery check
    batt = robot.get_battery_pct()
    print(f"Battery: {batt}%  Charging: {robot.is_charging()}")

    # RGB LED demo
    robot.set_rgb(0, 100, 255, brightness=150)   # Blue-ish
    time.sleep(1)
    robot.set_rgb(0, 0, 0, brightness=0)

    # Arm demo
    robot.set_arm(90, 90)    # Centre position
    time.sleep(0.5)
    robot.set_arm(45, 150)   # Lower axis 1, open axis 2
    time.sleep(0.5)
    robot.set_arm(90, 30)    # Return axis 1, close axis 2
    time.sleep(0.5)
    robot.release_arm()

    # Distance sensor demo
    dist = robot.get_distance_cm()
    print(f"Obstacle distance: {dist} cm")

    # Movement demo
    if dist > 20:
        robot.move('forward', duration_sec=2)
        robot.move('left', duration_sec=0.5)
        robot.move('forward', duration_sec=1)

    robot.stop()
    print("Demo complete.")
