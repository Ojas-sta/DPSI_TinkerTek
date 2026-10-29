/**
 * @file    obstacle_avoid.ino
 * @brief   ICRobot Arduino Example — Ultrasonic Obstacle Avoidance
 *
 * The robot continuously drives forward, reading the ultrasonic
 * distance sensor (I2C 0x57). When an obstacle is detected within
 * the warning zone, the robot backs up and turns to avoid it.
 *
 * Hardware: ICRobot (s4s Mainboard at I2C 0x0F, Ultrasonic at 0x57)
 * Controller: Arduino Uno R4 WiFi
 *
 * Motor Pair Action Codes:
 *   0 = stop
 *   1 = forward  (speed mode)
 *   2 = backward (speed mode)
 *   3 = turn left
 *   4 = turn right
 *
 * Author: ICRobot Open-Source Contributors
 * License: MIT
 */

#include <Wire.h>
#include "s4s_mainBoard.h"

// Global mainboard instance
s4s_mainBoard hw_main_board;

// ── Tuning constants ──────────────────────────────────────────────────────────
const uint16_t SAFE_DIST_CM  = 30;   // cm — drive freely above this
const uint16_t WARN_DIST_CM  = 15;   // cm — obstacle, must avoid
const uint16_t SPEED_NORMAL  = 70;   // motor speed when clear (0–100)
const uint16_t SPEED_SLOW    = 40;   // motor speed when warning zone
const uint16_t BACKUP_MS     = 500;  // ms — reverse duration on block
const uint16_t TURN_MS       = 600;  // ms — turn duration on block
const uint16_t POLL_MS       = 100;  // ms — sensor poll interval

// ── Setup ─────────────────────────────────────────────────────────────────────

void setup() {
    Serial.begin(115200);
    Serial.println("ICRobot Obstacle Avoidance");
    Serial.print("Safe: "); Serial.print(SAFE_DIST_CM);
    Serial.print(" cm  |  Avoid: "); Serial.print(WARN_DIST_CM); Serial.println(" cm");

    hw_main_board.begin();
    hw_main_board.encoder_motor_pair_set_group(0, 1);
    hw_main_board.encoder_motor_pair_set_dynamic_speed(SPEED_NORMAL, SPEED_NORMAL);

    // Signal ready with RGB LED (green)
    hw_main_board.ambient_light_set_state(100, 0, 200, 0);
    delay(500);
}

// ── Loop ──────────────────────────────────────────────────────────────────────

void loop() {
    uint16_t dist = hw_main_board.ultr_get_distance();

    if (dist == 0) {
        // Sensor out of range or error — treat as clear, slow down
        hw_main_board.encoder_motor_pair_set_dynamic_speed(SPEED_SLOW, SPEED_SLOW);
        hw_main_board.encoder_motor_pair_set_action(1);   // forward
        delay(POLL_MS);
        return;
    }

    if (dist > SAFE_DIST_CM) {
        // Clear ahead — full speed forward, green LED
        hw_main_board.ambient_light_set_state(80, 0, 200, 0);
        hw_main_board.encoder_motor_pair_set_dynamic_speed(SPEED_NORMAL, SPEED_NORMAL);
        hw_main_board.encoder_motor_pair_set_action(1);

    } else if (dist > WARN_DIST_CM) {
        // Warning zone — slow down, orange LED
        hw_main_board.ambient_light_set_state(100, 255, 140, 0);
        hw_main_board.encoder_motor_pair_set_dynamic_speed(SPEED_SLOW, SPEED_SLOW);
        hw_main_board.encoder_motor_pair_set_action(1);

    } else {
        // Too close — avoid! Red LED
        Serial.print("Obstacle at "); Serial.print(dist); Serial.println(" cm — avoiding!");
        hw_main_board.ambient_light_set_state(150, 255, 0, 0);

        // Stop
        hw_main_board.encoder_motor_pair_set_action(0);
        delay(200);

        // Back up
        hw_main_board.encoder_motor_pair_set_dynamic_speed(SPEED_NORMAL, SPEED_NORMAL);
        hw_main_board.encoder_motor_pair_set_action(2);   // backward
        delay(BACKUP_MS);

        // Turn right
        hw_main_board.encoder_motor_pair_set_action(4);   // turn right
        delay(TURN_MS);

        // Return to forward
        hw_main_board.ambient_light_set_state(80, 0, 200, 0);
        hw_main_board.encoder_motor_pair_set_action(1);
    }

    delay(POLL_MS);
}
