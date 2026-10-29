/**
 * @file icrobot.h
 * @brief Open-Source ESP-IDF Driver for School For Schools (s4s) ICRobot
 * @note Target Chip: ESP32-S3
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"
#include "driver/i2c.h"

#ifdef __cplusplus
extern "C" {
#endif

// ==================== Hardware Pin Configuration ====================
#define ICROBOT_I2C_PORT          I2C_NUM_0
#define ICROBOT_I2C_SDA_PIN       GPIO_NUM_42
#define ICROBOT_I2C_SCL_PIN       GPIO_NUM_41
#define ICROBOT_I2C_FREQ_HZ       100000

// ==================== I2C Slave Addresses ====================
#define ICROBOT_MAINBOARD_ADDR    0x0F
#define ICROBOT_ULTRASONIC_ADDR   0x57
#define ICROBOT_IMU_ADDR          0x6B
#define ICROBOT_K210_ADDR         0x24

// ==================== Register Map (Mainboard 0x0F) ====================
#define REG_POWER_BATTERY         0x00
#define REG_POWER_CHARGING        0x02
#define REG_AMBIENT_LIGHT_BRI     0x0A
#define REG_AMBIENT_LIGHT_RGB     0x0B
#define REG_RTC                   0x14
#define REG_SERVO_BASE            0x1E
#define REG_SERVO_SPEED_BASE      0x20
#define REG_SERVO_RELEASE_BASE    0x22
#define REG_MOTOR_PAIR_ACTION     0xC8
#define REG_MOTOR_PAIR_GROUP      0xC9
#define REG_MOTOR_PAIR_SPEED      0xCA
#define REG_MOTOR_PAIR_TIME       0xCB
#define REG_MOTOR_PAIR_ROTATIONS  0xCC
#define REG_MOTOR_PAIR_DISTANCE   0xCD
#define REG_MOTOR_PAIR_STATUS     0xCE

// ==================== Movement Action Constants ====================
typedef enum {
    ICROBOT_MOVE_STOP     = 0,
    ICROBOT_MOVE_FORWARD  = 1,
    ICROBOT_MOVE_BACKWARD = 2,
    ICROBOT_MOVE_LEFT     = 3,
    ICROBOT_MOVE_RIGHT    = 4
} icrobot_direction_t;

// ==================== Core API Functions ====================

/**
 * @brief Initialize the ESP32-S3 I2C hardware bus for the ICRobot
 * @return ESP_OK on success
 */
esp_err_t icrobot_init(void);

/**
 * @brief Set the 2-axis arm angles
 * @param axis1_deg Base / shoulder servo angle (0 to 180 degrees)
 * @param axis2_deg Elbow / gripper servo angle (0 to 180 degrees)
 * @return ESP_OK on success
 */
esp_err_t icrobot_set_arm(uint8_t axis1_deg, uint8_t axis2_deg);

/**
 * @brief De-energize both arm servos to prevent overheating and conserve power
 * @return ESP_OK on success
 */
esp_err_t icrobot_release_arm(void);

/**
 * @brief Set continuous servo speed for an arm axis
 * @param servo_id 0 for axis 1, 1 for axis 2
 * @param speed -100 to 100
 * @return ESP_OK on success
 */
esp_err_t icrobot_set_servo_speed(uint8_t servo_id, int8_t speed);

/**
 * @brief Set individual speeds for left and right wheels
 * @param left_speed 0 to 100
 * @param right_speed 0 to 100
 * @return ESP_OK on success
 */
esp_err_t icrobot_set_speed(uint16_t left_speed, uint16_t right_speed);

/**
 * @brief Immediately start moving in a direction
 * @param dir ICROBOT_MOVE_FORWARD, BACKWARD, LEFT, RIGHT, or STOP
 * @return ESP_OK on success
 */
esp_err_t icrobot_start_move(icrobot_direction_t dir);

/**
 * @brief Move in a direction for a specified duration in milliseconds (blocking)
 * @param dir Movement direction
 * @param duration_ms Duration in milliseconds
 * @return ESP_OK on success
 */
esp_err_t icrobot_move_ms(icrobot_direction_t dir, uint16_t duration_ms);

/**
 * @brief Move in a direction for a specified distance in centimeters (blocking)
 * @param dir Movement direction
 * @param distance_cm Travel distance in centimeters
 * @return ESP_OK on success
 */
esp_err_t icrobot_move_cm(icrobot_direction_t dir, uint16_t distance_cm);

/**
 * @brief Emergency stop all drive motors
 * @return ESP_OK on success
 */
esp_err_t icrobot_stop(void);

/**
 * @brief Read remaining battery percentage
 * @param[out] battery_pct Output pointer (0 - 100%)
 * @return ESP_OK on success
 */
esp_err_t icrobot_get_battery(uint8_t *battery_pct);

/**
 * @brief Read charging status
 * @param[out] is_charging true if charging cable connected, false otherwise
 * @return ESP_OK on success
 */
esp_err_t icrobot_is_charging(bool *is_charging);

/**
 * @brief Set the onboard ambient RGB LED color and brightness
 * @param r Red component (0 - 255)
 * @param g Green component (0 - 255)
 * @param b Blue component (0 - 255)
 * @param brightness Brightness level (0 - 255)
 * @return ESP_OK on success
 */
esp_err_t icrobot_set_led(uint8_t r, uint8_t g, uint8_t b, uint8_t brightness);

/**
 * @brief Poll until current motor action is complete
 * @param timeout_ms Timeout in milliseconds
 * @return ESP_OK when idle, ESP_ERR_TIMEOUT if timed out
 */
esp_err_t icrobot_wait_motor_done(uint32_t timeout_ms);

#ifdef __cplusplus
}
#endif
