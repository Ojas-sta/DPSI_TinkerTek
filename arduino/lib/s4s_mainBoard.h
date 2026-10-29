/**
 * @file    s4s_mainBoard.h
 * @brief   s4s Mainboard Arduino Library — Header
 *
 * ============================================================
 * ICRobot Open-Source — s4s Mainboard Driver
 * ============================================================
 * This header defines the `s4s_mainBoard` class that provides
 * a high-level C++ API for the s4s proprietary mainboard used
 * in the ICRobot school robotics platform.
 *
 * The mainboard is an I2C peripheral sitting at address 0x0F.
 * It manages all robot actuators and sensors:
 *
 *   - Charging / Power management   (reg 0x00)
 *   - Ambient RGB LEDs              (reg 0x0A)
 *   - Real-Time Clock (RTC)         (reg 0x14)
 *   - Servo motors (2-axis arm)     (reg 0x1E)
 *   - Voice recognition module      (reg 0x28)
 *   - Encoder motor 0 (left wheel)  (reg 0x50)
 *   - Encoder motor 1 (right wheel) (reg 0x6E)
 *   - Encoder motor 2               (reg 0x8C)
 *   - Encoder motor 3               (reg 0xAA)
 *   - Encoder motor pair control    (reg 0xC8)
 *   - Ultrasonic sensor             (I2C addr 0x57)
 *   - Grayscale line sensor         (I2C addr 0x6F)
 *
 * Supported controller boards:
 *   - Arduino Uno R4 WiFi (Renesas RA4M1)  ← primary target
 *   - ESP32 / ESP32-S3 (Wire.begin(42,41) on SDA/SCL)
 *   - AVR-based boards (standard Wire.begin())
 *
 * Original source: School for Schools (s4s) — TinkerTek platform
 * Open-source adaptation: ICRobot Open-Source Contributors
 * License: MIT
 * ============================================================
 */

#pragma once

#include "Arduino.h"
#include "Wire.h"

#if defined(__AVR__) || defined(ARDUINO_ARCH_AVR)
// The AVR platform (such as Arduino Nano) does not support std::string
#else
// Other platforms (such as ESP32, STM32) may be supported
#include <string>
#endif

/**
 * Supported hardware subsystems on the s4s Mainboard:
 * - Charging management
 * - Ambient light
 * - RTC
 * - Servo
 * - Gyroscope
 * - Voice module
 * - Encoder motor 0 (built-in motor)
 * - Encoder motor 1 (built-in motor)
 * - Encoder motor 2
 * - Encoder motor 3
 */


class s4s_mainBoard
{
public:
    s4s_mainBoard();
     ~ s4s_mainBoard();
public:
    enum COLOR_TYPE
    {
        COLOR_NONE=0,
        COLOR_RED,
        COLOR_GREEN,
        COLOR_BLUE,
        COLOR_YELLOW,
        COLOR_PURPLE = COLOR_YELLOW + 2,
    };
public:
    void begin(TwoWire *wire) { _wire=wire;}
    void begin(void)
    {
#if defined(__AVR__) || defined(ARDUINO_ARCH_AVR) || defined(ARDUINO_ARCH_RENESAS)
        Wire.begin();
#else
        Wire.begin(42, 41);
        Wire1.begin(1, 2);
        _wire2 = &Wire1;
#endif
        _wire = &Wire;
    }

    /**
     * @description: Get the internal battery level
     * @param level 0 ~ 100
     * @return int 0: success, other: fail
     */    
    int power_get_internal_battery_level(uint8_t * level);
    /**
     * @description: Get the external battery voltage
     * @param voltage Battery voltage
     * @return int 0: success, other: fail
     */    
    int power_get_external_battery_voltage(float * voltage);
    /**
     * @description: Get the charging status
     * @param isCharging 1: charging; 0: not charging
     * @return int 0: success, other: fail
     */    
    int power_is_charging(uint8_t * isCharging);
    /**
     * @description: Get the charging status
     * @param isFullyCharged 1: fully charged; 0: not fully charged
     * @return int 0: success, other: fail
     */
    int power_is_fully_charged(uint8_t * isFullyCharged);
    /**
     * @description: Get main board version
     * @param version Version array [major, minor, patch]
     * @return int 0: success, other: fail
     */    
    int version_get(uint8_t version[3]);
    /**
    * @description: Set the ambient light status
    * @param light Brightness 0 ~ 255; -1 means do not change
    * @param color Color array [r, g, b] 0 ~ 255; NULL means do not change
    * @return int 0: success, other: fail
    */
    int ambient_light_set_state(int light, uint8_t color[3]);
    int ambient_light_set_state(int light, uint8_t r, uint8_t g, uint8_t b);

    /**
    * @description: Set RTC time
    * @param year Year 0 ~ 99
    * @param month Month 1 ~ 12
    * @param day Day 1 ~ 31
    * @return int 0: success, other: fail
    */
    int rtc_set_date(uint8_t year, uint8_t month, uint8_t day);
    int rtc_set_time(uint8_t hour, uint8_t minute, uint8_t second);
    int rtc_get_data(uint8_t * year, uint8_t * month, uint8_t * day, uint8_t * week);
    int rtc_get_time(uint8_t * hour, uint8_t * minute, uint8_t * second);

    /**
    * @description: Set the servo angle
    * @param id Servo ID 0 ~ 1
    * @param angle Angle 0 ~ 180
    * @return int 0: success, other: fail
    */
    int servo_set_angle(uint8_t id, uint8_t angle);

    /**
    * @description: Set the continuous servo angle
    * @param id    Servo ID 0 ~ 1
    * @param speed speed -100 ~ 180
    */
    int continuous_servo_set_speed(uint8_t id, int8_t speed);

    /**
     * @description: Release the servo
     * @param id Servo ID 0 ~ 1
     * @return int 0: success, other: fail
     */    
    int servo_release(uint8_t id);

    /**
     * @description: Get voice commands
     * @return int 0: success, other: fail
     */    
    int voice_get_state(uint8_t * state);
    /**
     * @description: Reset voice commands
     * @return int 0: success, other: fail
     */    
    int voice_reset_state(void);
    /**
     * @description: Get voice version
     * @return 0: success, other: fail
     */    
    int voice_get_version(uint8_t version[3]);


    /**
     * @description: Get the rotational angle of the encoded motor
     * @param id  Encoder motor ID 0 ~ 3
     * @param angle Rotational angle
     * @return int 0: success, other: fail
     */    
    int encoder_motor_get_angle(uint8_t id, int32_t * angle);
    /**
     * @description: Get the rpm speed of the encoded motor
     * @param id  Encoder motor ID 0 ~ 3
     * @param speed Speed
     * @return int 0: success, other: fail
     */    
    int encoder_motor_get_rpm_speed(uint8_t id, int16_t * speed);

    /**
     * @description: Get the dynamic speed of the encoded motor
     * @param id  Encoder motor ID 0 ~ 3
     * @param speed Speed
     * @return int 0: success, other: fail
     */   
    int encoder_motor_get_dynamic_speed(uint8_t id, int16_t * speed);
    /**
     * @description: Get the current power of the encoded motor
     * @param id  Encoder motor ID 0 ~ 3
     * @param power Current power
     * @return int 0: success, other: fail
     */    
    int encoder_motor_get_power(uint8_t id, uint16_t * power);
    /**
     * @description: Reset the rotation angle of the encoder motor
     * @param id  Encoder motor ID 0 ~ 3
     * @return int 0: success, other: fail
     */    
    int encoder_motor_reset_angle(uint8_t id);
    /**
     * @description: Set the motion commands for the encoded motor
     * @param id  Encoder motor ID 0 ~ 3
     * @param action Command
     *  @note 
     *      0:stop
     *      rpmSpeed     : 1:forward  2:backward
     *      dynamicSpeed : 3:forward  4:backward
     *      power        : 5:forward  6:backward
     *      ring         : 7:forward  8:backward
     *      angle        : 9:forward  10:backward
     *      second       : 11:forward 12:backward
     *      centimeter   : 13:forward 14:backward
     * @return int 0: success, other: fail
     */    
    int encoder_motor_set_action(uint8_t id, uint8_t action);
    /**
     * @description: Set the motion rpm speed of the encoder motor
     * @param id  Encoder motor ID 0 ~ 3
     * @param speed Speed 0 ~ (100 ~ 180)
     * @return int 0: success, other: fail
     */    
    int encoder_motor_set_rpm_speed(uint8_t id, uint16_t speed);
    /**
     * @description: Set the motion dynamic speed of the encoder motor
     * @param id  Encoder motor ID 0 ~ 3
     * @param speed Speed 0 ~100
     * @return int 0: success, other: fail
     */
    int encoder_motor_set_dynamic_speed(uint8_t id, uint16_t speed);
    /**
     * @description: Set the power of the encoder motor
     * @param id  Encoder motor ID 0 ~ 3
     * @param power Power 0 ~ 100
     * @return int 0: success, other: fail
     */ 
    int encoder_motor_set_power(uint8_t id, uint8_t power);
    /**
     * @description: Set the ring of the encoder motor
     * @param id  Encoder motor ID 0 ~ 3
     * @param ring Ring 0 ~ 65535
     * @return int 0: success, other: fail
     */  
    int encoder_motor_set_ring(uint8_t id, uint16_t ring);
    /**
     * @description: Set the relative angle for the encoder motor operation
     * @param id  Encoder motor ID 0 ~ 3
     * @param relativeAngle Relative angle
     * @return int 0: success, other: fail
     */    
    int encoder_motor_set_relative_angle(uint8_t id, uint16_t relativeAngle);
    /**
     * @description: Set the running duration of the encoder motor
     * @param id  Encoder motor ID 0 ~ 3
     * @param runTime Running duration, The unit is seconds
     * @return int 0: success, other: fail
     */
    int encoder_motor_set_time(uint8_t id, uint16_t runTime);
    /**
     * @description: Set the operating distance of the encoder motor
     * @param id  Encoder motor ID 0 ~ 3
     * @param centimeter Running distance
     * @return int 0: success, other: fail
     */
    int encoder_motor_set_centimeter(uint8_t id, uint16_t centimeter);
    /**
     * @description: Get the execution status of the command
     * @param id  Encoder motor ID 0 ~ 3
     * @param running 0:stop 1:running
     * @return int 0: success, other: fail
     */    
    int encoder_motor_get_action_runing(uint8_t id, uint8_t * running);
    /**
     * @description: Set the motion commands for the encoded motor
     * @param action Command
     * @note 
     *      0:stop
     *      speed     : 1 :forward 2:backward   3 :turn left 4:turn right
     *      second    : 5 :forward 6:backward   7 :turn left 8:turn right
     *      ring      : 9 :forward 10:backward  11:turn left 12:turn right
     *      centimeter: 13:forward 14:backward  15:turn left 16:turn right
     * @return int 0: success, other: fail
     */    
    int encoder_motor_pair_set_action(uint8_t action);
    /**
     * @description: Set the IDs for the left and right motor pairs
     * @param l_id Left motor ID 0 ~ 3
     * @param r_id Right motor ID 0 ~ 3
     * @return int 0: success, other: fail
     */    
    int encoder_motor_pair_set_group(uint8_t l_id, uint8_t r_id);
    /**
     * @description: Set the motor speed for the left and right motors
     * @param l_speed Left motor speed
     * @param r_speed Right motor speed
     * @return int 0: success, other: fail
     */    
    int encoder_motor_pair_set_dynamic_speed(uint16_t l_speed, uint16_t r_speed);
    /**
     * @description: Set motor for motion time
     * @param runTime Running time 0 ~ 65535, unit: ms
     * @return int 0: success, other: fail
     */    
    int encoder_motor_pair_set_time(uint16_t runTime);
    /**
     * @description: Set the number of running laps
     * @param ring 
     * @return int 0: success, other: fail
     */  
    int encoder_motor_pair_set_ring(uint16_t ring);
    /**
     * @description: Set running distance
     * @param centimeters  unit: cm
     * @return int 0: success, other: fail
     */  
    int encoder_motor_pair_set_centimeter(uint16_t centimeters);
    /**
     * @description: Get the execution status of the command
     * @param running 0:stop 1:running
     * @return int 0: success, other: fail
     */    
    int encoder_motor_pair_get_action_runing(uint8_t * running);

    /**
     * @description: Get the distance of the ultrasonic wave
     * @return The unit is centimeters
     */    
    uint16_t ultr_get_distance(void);
    void ultr_set_color(uint8_t light, uint8_t color[3]);
    void ultr_set_color(uint8_t light, uint8_t r, uint8_t g, uint8_t b);

    void gray_grayStudy(void);
    void gray_binaryStudy(void);
    void gray_colorStudy(enum COLOR_TYPE colorType);
    void gray_clearColor(void);
    void gray_getGrayData(uint8_t data[4]);
    void gray_getColorData(uint8_t data[4]);
    void gray_getBlack(uint8_t data[4]);
    void gray_getPhotosensitive(uint8_t data[4]);

    const uint8_t MAINBOARD_ADDR = 0x0F;  ///< I2C address of the s4s mainboard
    const uint8_t ULTR_ADDR = 0x57;       ///< I2C address of the ultrasonic sensor
    const uint8_t GYRO_ADDR = 0x6F;       ///< I2C address of the gyroscope / line sensor

protected:
    virtual int writeData(uint8_t dev_addr, uint8_t *data, uint16_t len);
    virtual int readData(uint8_t dev_addr, uint8_t *data, uint16_t len);
    virtual int writeReg(uint8_t dev_addr, uint8_t reg, uint8_t *data, uint16_t len);
    virtual int readReg(uint8_t dev_addr, uint8_t reg, uint8_t *data, uint16_t len);
    virtual int isOnline(uint8_t dev_addr);

private:
    TwoWire *_wire  = NULL;   ///< Primary I2C bus (mainboard)
    TwoWire *_wire2 = NULL;   ///< Secondary I2C bus (ESP32 only)
    uint16_t ultr_last_distance = 0;          ///< Cached ultrasonic distance
    uint32_t ultr_getDistance_last_tick = 0;  ///< Timestamp of last distance read
    uint32_t ultr_setColor_last_tick = 0;     ///< Timestamp of last color set
};
