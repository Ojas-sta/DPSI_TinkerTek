/**
 * @file    basic_movement.ino
 * @brief   ICRobot Arduino Example — Basic Movement
 *
 * Demonstrates forward driving, turning, and stopping using
 * the s4s_mainBoard library on an Arduino Uno R4 WiFi.
 *
 * Hardware: ICRobot (s4s Mainboard at I2C 0x0F)
 * Controller: Arduino Uno R4 WiFi
 *
 * Sequence:
 *   1. Drive forward for 2 seconds
 *   2. Turn left for ~600 ms
 *   3. Drive forward for 2 more seconds
 *   4. Stop
 *
 * Motor Pair Action Codes (encoder_motor_pair_set_action):
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

// Motor speed (0–100)
const uint16_t SPEED = 70;

void setup() {
    Serial.begin(115200);
    Serial.println("ICRobot Basic Movement Example");

    // Initialise I2C and the mainboard
    hw_main_board.begin();

    // Configure motor pair: motor 0 = left, motor 1 = right
    hw_main_board.encoder_motor_pair_set_group(0, 1);

    // Set speed for both wheels
    hw_main_board.encoder_motor_pair_set_dynamic_speed(SPEED, SPEED);

    // --- Step 1: Forward 2 seconds ---
    Serial.println("Forward...");
    hw_main_board.encoder_motor_pair_set_action(1);   // 1 = forward
    delay(2000);

    // --- Step 2: Turn left ---
    Serial.println("Turning left...");
    hw_main_board.encoder_motor_pair_set_action(3);   // 3 = turn left
    delay(600);

    // --- Step 3: Forward 2 more seconds ---
    Serial.println("Forward again...");
    hw_main_board.encoder_motor_pair_set_action(1);
    delay(2000);

    // --- Step 4: Stop ---
    Serial.println("Stop.");
    hw_main_board.encoder_motor_pair_set_action(0);   // 0 = stop
}

void loop() {
    // Nothing — all movement happens in setup() for this example
}
