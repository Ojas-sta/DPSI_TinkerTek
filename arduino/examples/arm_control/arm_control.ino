/**
 * @file    arm_control.ino
 * @brief   ICRobot Arduino Example — Servo Arm Control (Pick and Place)
 *
 * Demonstrates controlling the 2-axis servo arm on the ICRobot
 * using the s4s_mainBoard library.
 *
 * Hardware: ICRobot (s4s Mainboard at I2C 0x0F)
 * Controller: Arduino Uno R4 WiFi
 *
 * Servo IDs (via servo_set_angle / servo_release):
 *   Servo ID 0 — Arm axis 1 (base / elevation)  — register 0x1E
 *   Servo ID 1 — Arm axis 2 (gripper)           — register 0x1F
 *
 * Angle range: 0–180 degrees for each servo.
 *
 * Pick-and-Place Sequence (repeats 3 times):
 *   1. Home position (both 90°)
 *   2. Open gripper (servo 1 = 150°)
 *   3. Lower arm (servo 0 = 30°)
 *   4. Close gripper to pick (servo 1 = 40°)
 *   5. Raise arm (servo 0 = 90°)
 *   6. Open gripper to place (servo 1 = 150°)
 *   7. Return to home
 *   8. Release servos (power save)
 *
 * Author: ICRobot Open-Source Contributors
 * License: MIT
 */

#include <Wire.h>
#include "s4s_mainBoard.h"

// Global mainboard instance
s4s_mainBoard hw_main_board;

// Arm position constants (degrees)
const uint8_t HOME_AXIS1     = 90;    // arm horizontal
const uint8_t HOME_AXIS2     = 90;    // gripper half-open
const uint8_t LOWER_AXIS1    = 30;    // arm lowered for picking
const uint8_t GRIPPER_OPEN   = 150;   // gripper fully open
const uint8_t GRIPPER_CLOSED = 40;    // gripper closed (gripping)

// How long to wait after each servo command (ms)
const int SERVO_DELAY_MS = 600;

// Number of pick-and-place cycles
const int CYCLES = 3;

// ── Helper functions ────────────────────────────────────────────────────────

/** Move arm to home position */
void armHome() {
    hw_main_board.servo_set_angle(0, HOME_AXIS1);
    hw_main_board.servo_set_angle(1, HOME_AXIS2);
    delay(SERVO_DELAY_MS);
}

/** Execute a pick sequence */
void pick() {
    Serial.println("  Opening gripper...");
    hw_main_board.servo_set_angle(1, GRIPPER_OPEN);
    delay(SERVO_DELAY_MS);

    Serial.println("  Lowering arm...");
    hw_main_board.servo_set_angle(0, LOWER_AXIS1);
    delay(SERVO_DELAY_MS);

    Serial.println("  Closing gripper (pick)...");
    hw_main_board.servo_set_angle(1, GRIPPER_CLOSED);
    delay(SERVO_DELAY_MS);

    Serial.println("  Raising arm...");
    hw_main_board.servo_set_angle(0, HOME_AXIS1);
    delay(SERVO_DELAY_MS);
}

/** Execute a place sequence (open gripper) */
void place() {
    Serial.println("  Opening gripper (place)...");
    hw_main_board.servo_set_angle(1, GRIPPER_OPEN);
    delay(SERVO_DELAY_MS);
}

// ── Setup ───────────────────────────────────────────────────────────────────

void setup() {
    Serial.begin(115200);
    Serial.println("ICRobot Arm Control Example");

    hw_main_board.begin();

    // Start at home position
    armHome();
    delay(500);

    for (int cycle = 1; cycle <= CYCLES; cycle++) {
        Serial.print("\n── Cycle ");
        Serial.print(cycle);
        Serial.print("/");
        Serial.println(CYCLES);

        pick();
        place();
        armHome();
        delay(300);
    }

    // De-energize servos after task completes
    Serial.println("\nTask complete — releasing servos.");
    hw_main_board.servo_release(0);
    hw_main_board.servo_release(1);
}

void loop() {
    // Nothing — task runs once in setup()
}
