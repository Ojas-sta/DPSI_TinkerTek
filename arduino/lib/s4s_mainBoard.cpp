/**
 * @file    s4s_mainBoard.cpp
 * @brief   s4s Mainboard Arduino Library — Implementation
 *
 * ============================================================
 * ICRobot Open-Source — s4s Mainboard Driver Implementation
 * ============================================================
 * Contains all I2C communication routines and register-level
 * implementations for the s4s Mainboard (I2C address 0x0F).
 *
 * Key register map (static constants defined below):
 *   CHARGING_REG           = 0x00  -- Battery / charging management
 *   AMBIENT_LIGHT_REG      = 0x0A  -- RGB ambient LED
 *   RTC_REG                = 0x14  -- Real-time clock
 *   SERVO_REG              = 0x1E  -- Servo motor control
 *   VOICE_REG              = 0x28  -- Voice recognition module
 *   ENCODER_MOTOR_REG[]    = {0x50, 0x6E, 0x8C, 0xAA}  -- Individual motors
 *   ENCODER_MOTOR_PAIR_REG = 0xC8  -- Motor pair (wheel drive) control
 *
 * Original source: School for Schools (s4s) — TinkerTek platform
 * Open-source adaptation: ICRobot Open-Source Contributors
 * License: MIT
 * ============================================================
 */

#include "s4s_mainBoard.h"
#include <string.h>


/*******************
 * static variable
 ******************/
/** Copy helper macro — safely copies data only if both pointers are valid */
#define POINTER_SPACE_COPY(type, dst, src, len) \
    do                                          \
    {                                           \
        if (NULL == dst || NULL == src)         \
            break;                              \
        memcpy(dst, src, len * sizeof(type));   \
    } while (0)

#define DATA_MAX(a, b) ((a) > (b) ? (a) : (b))
#define DATA_MIN(a, b) ((a) < (b) ? (a) : (b))

/** Charging / power management register base address */
static const uint8_t CHARGING_REG           = 0x00; // Charging Management 充电管理  [EN]: Battery charging management
/** RGB ambient LED register base address */
static const uint8_t AMBIENT_LIGHT_REG      = 0x0A; // Ambient light 氛围灯          [EN]: Ambient light (RGB LEDs)
/** Real-time clock register base address */
static const uint8_t RTC_REG                = 0x14; // RTC 
/** Servo motor register base address (covers servo 0 and 1) */
static const uint8_t SERVO_REG              = 0x1E; // Servo 舵机                    [EN]: Servo motor control
/** Voice recognition module register base address */
static const uint8_t VOICE_REG              = 0x28; // Voice Module 语音模块          [EN]: Voice recognition module
/** Individual encoder motor register bases (IDs 0–3) */
static const uint8_t ENCODER_MOTOR_REG[]    = {0x50, 0x6E, 0x8C, 0xAA}; // Encoder motor 编码电机  [EN]: Encoder motor registers (4 motors)
/** Encoder motor pair (left+right wheel drive) register base */
static const uint8_t ENCODER_MOTOR_PAIR_REG = 0xC8; // Encoder motor pair 编码电机对  [EN]: Motor pair control for differential drive


/*******************
 * static function
 ******************/

/** Write raw bytes to an I2C device (no register addressing) */
static int writeData(TwoWire *wire, uint8_t dev_addr, uint8_t *data, uint16_t len)
{
    if (NULL == wire)
        return -1;
    wire->beginTransmission(dev_addr);
    while (len--)
    {
        wire->write(*(data++));
    }
    wire->endTransmission(true);

    return 0;
}

/** Read raw bytes from an I2C device */
static int readData(TwoWire *wire, uint8_t dev_addr, uint8_t *data, uint16_t len)
{
    if (NULL == wire)
        return -1;
    wire->requestFrom((uint8_t)dev_addr, (uint8_t)len);
    while (wire->available())
    {
        *data = wire->read();
        data++;
    }
    return 0;
}

/** Write bytes to a specific register on an I2C device */
static int writeReg(TwoWire *wire, uint8_t dev_addr, uint8_t reg, uint8_t *data, uint16_t len)
{
    if (NULL == wire)
        return -1;
    wire->beginTransmission(dev_addr);
    wire->write(reg);
    while (len--)
    {
        wire->write(*(data++));
    }
    wire->endTransmission(true);

    return 0;
}

/** Read bytes from a specific register on an I2C device */
static int readReg(TwoWire *wire, uint8_t dev_addr, uint8_t reg, uint8_t *data, uint16_t len)
{
    if (NULL == wire)
        return -1;
    wire->beginTransmission(dev_addr);
    wire->write(reg);
    wire->endTransmission(false);

    wire->requestFrom((uint8_t)dev_addr, (uint8_t)len);
    while (wire->available())
    {
        *data = wire->read();
        data++;
    }

    return 0;
}

// 0:online, otherwise offline
/** Check if an I2C device is reachable. Returns 0 if online. */
static int isOnline(TwoWire *wire, uint8_t dev_addr)
{
    if (NULL == wire)
        return 0xFF;
    wire->beginTransmission(dev_addr);
    return wire->endTransmission(true);
}


/************************
 * class protected
 ************************/

/**
 * Route writeData to the correct I2C bus.
 * On ESP32: mainboard uses Wire (SDA=42, SCL=41);
 *           all other peripherals use Wire1.
 * On AVR/Renesas: always uses Wire.
 */
int s4s_mainBoard::writeData(uint8_t dev_addr, uint8_t *data, uint16_t len)
{
    TwoWire * wire = this->_wire;
    if (MAINBOARD_ADDR != dev_addr && NULL != _wire2)
    {
        wire = this->_wire2;
    }
    return ::writeData(wire, dev_addr, data, len);
}

int s4s_mainBoard::readData(uint8_t dev_addr, uint8_t *data, uint16_t len)
{
    TwoWire * wire = this->_wire;
    if (MAINBOARD_ADDR != dev_addr && NULL != _wire2)
    {
        wire = this->_wire2;
    }
    return ::readData(wire, dev_addr, data, len);
}

int s4s_mainBoard::writeReg(uint8_t dev_addr, uint8_t reg, uint8_t *data, uint16_t len)
{
    TwoWire * wire = this->_wire;
    if (MAINBOARD_ADDR != dev_addr && NULL != _wire2)
    {
        wire = this->_wire2;
    }
    return ::writeReg(wire, dev_addr, reg, data, len);
}

int s4s_mainBoard::readReg(uint8_t dev_addr, uint8_t reg, uint8_t *data, uint16_t len)
{
    TwoWire * wire = this->_wire;
    if (MAINBOARD_ADDR != dev_addr && NULL != _wire2)
    {
        wire = this->_wire2;
    }
    return ::readReg(wire, dev_addr, reg, data, len);
}

int s4s_mainBoard::isOnline(uint8_t dev_addr)
{
    TwoWire * wire = this->_wire;
    if (MAINBOARD_ADDR != dev_addr && NULL != _wire2)
    {
        wire = this->_wire2;
    }
    return ::isOnline(wire, dev_addr);
}


/************************
 * class public
 ************************/
s4s_mainBoard::s4s_mainBoard()
{

}

s4s_mainBoard::~s4s_mainBoard()
{

}

int s4s_mainBoard::power_get_internal_battery_level(uint8_t * level)
{
    int ret = 0;
    ret += this->readReg(MAINBOARD_ADDR, CHARGING_REG + 0, level, 1);
    return ret;
}

int s4s_mainBoard::power_get_external_battery_voltage(float * voltage)
{
    int ret = 0;
    uint8_t data = {0};
    ret += this->readReg(MAINBOARD_ADDR, CHARGING_REG + 1, &data, 1);
    *voltage = data / 10.0f;
    return ret;
}

int s4s_mainBoard::power_is_charging(uint8_t * isCharging)
{
    int ret = 0;
    ret += this->readReg(MAINBOARD_ADDR, CHARGING_REG + 2, isCharging, 1);
    return ret;
}

int s4s_mainBoard::power_is_fully_charged(uint8_t * isFullyCharged)
{
    int ret = 0;
    ret += this->readReg(MAINBOARD_ADDR, CHARGING_REG + 3, isFullyCharged, 1);
    return ret;
}

int s4s_mainBoard::version_get(uint8_t version[3])
{
    int ret = 0;
    ret += this->readReg(MAINBOARD_ADDR, CHARGING_REG + 4, version, 3);
    return ret;
}

int s4s_mainBoard::ambient_light_set_state(int light, uint8_t color[3])
{
    int ret = 0;
    if (light > 0)
    {
        uint8_t data = light > 255 ? 255 : light;
        ret += this->writeReg(MAINBOARD_ADDR, AMBIENT_LIGHT_REG + 0, &data, 1);
    }
    if (color)
    {
        ret += this->writeReg(MAINBOARD_ADDR, AMBIENT_LIGHT_REG + 1, color, 3);
    }
    return ret;
}

int s4s_mainBoard::ambient_light_set_state(int light, uint8_t r, uint8_t g, uint8_t b)
{
    uint8_t data[] = {r, g, b};
    return this->ambient_light_set_state(light, data);
}

int s4s_mainBoard::rtc_set_date(uint8_t year, uint8_t month, uint8_t day)
{
    int ret = 0;
    uint8_t data[] = {0/*week*/, month, day, year};
    ret += this->writeReg(MAINBOARD_ADDR, RTC_REG+1, data, 4);
    return ret;
}

int s4s_mainBoard::rtc_set_time(uint8_t hour, uint8_t minute, uint8_t second)
{
    int ret = 0;
    uint8_t data[] = {hour, minute, second};
    ret += this->writeReg(MAINBOARD_ADDR, RTC_REG+0, data, 3);
    return ret;
}

int s4s_mainBoard::rtc_get_data(uint8_t * year, uint8_t * month, uint8_t * day, uint8_t *week)
{
    int ret = 0;
    uint8_t data[4] = {0};
    ret += this->readReg(MAINBOARD_ADDR, RTC_REG+1, data, 4);
    POINTER_SPACE_COPY(uint8_t, week, &data[0], 1);
    POINTER_SPACE_COPY(uint8_t, month, &data[1], 1);
    POINTER_SPACE_COPY(uint8_t, day, &data[2], 1);
    POINTER_SPACE_COPY(uint8_t, year, &data[3], 1);
    return ret;
}

int s4s_mainBoard::rtc_get_time(uint8_t * hour, uint8_t * minute, uint8_t * second)
{
    int ret=0;
    uint8_t data[3] = {0};
    ret += this->readReg(MAINBOARD_ADDR, RTC_REG+0, data, 3);
    POINTER_SPACE_COPY(uint8_t, hour, &data[0], 1);
    POINTER_SPACE_COPY(uint8_t, minute, &data[1], 1);
    POINTER_SPACE_COPY(uint8_t, second, &data[2], 1);
    return ret;
}

int s4s_mainBoard::servo_set_angle(uint8_t id, uint8_t angle)
{
    if (id > 1) return -1;

    int ret = 0;
    uint8_t data[] = {angle};
    ret += this->writeReg(MAINBOARD_ADDR, SERVO_REG+id, data, 1);
    return ret;
}

int s4s_mainBoard::continuous_servo_set_speed(uint8_t id, int8_t speed)
{
    if (id > 1) return -1;

    int ret = 0;
    uint8_t data[] = {(uint8_t)speed};
    ret += this->writeReg(MAINBOARD_ADDR, SERVO_REG+2+id, data, 1);
    return ret;
}

int s4s_mainBoard::servo_release(uint8_t id)
{
    if (id > 1) return -1;

    int ret = 0;
    uint8_t data[] = {0};
    ret += this->writeReg(MAINBOARD_ADDR, SERVO_REG+4+id, data, 1);
    return ret;
}

int s4s_mainBoard::voice_get_state(uint8_t * state)
{
    if (NULL == state) return -1;

    int ret = 0;
    ret = this->readReg(MAINBOARD_ADDR, VOICE_REG, state, 1);
    return ret;
}

int s4s_mainBoard::voice_reset_state(void)
{
    int ret = 0;
    uint8_t data = {0};
    ret += this->writeReg(MAINBOARD_ADDR, VOICE_REG, &data, 1);
    return ret;
}

int s4s_mainBoard::voice_get_version(uint8_t version[3])
{
    if (NULL == version) return -1;

    int ret = 0;
    ret += this->readReg(MAINBOARD_ADDR, VOICE_REG+1, version, 3);
    return ret;
}

int s4s_mainBoard::encoder_motor_get_angle(uint8_t id, int32_t * angle)
{
    int ret = 0;
    uint8_t data[4] = {0};
    ret = this->readReg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[id] + 0, data, 4);
    if (angle)
    {
        *angle = (int32_t)(((uint32_t)data[0] << 24) | ((uint32_t)data[1] << 16) | ((uint32_t)data[2] << 8) | data[3]);
    }
    return ret;
}

int s4s_mainBoard::encoder_motor_get_rpm_speed(uint8_t id, int16_t * speed)
{
    int ret = 0;
    uint8_t data[2] = {0};
    ret = this->readReg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[id] + 1, data, 2);
    if (speed)
    {
        *speed = (int16_t)(((uint16_t)data[0] << 8) | data[1]);
    }
    return ret;
}

int s4s_mainBoard::encoder_motor_get_dynamic_speed(uint8_t id, int16_t * speed)
{
    int ret = 0;
    uint8_t data[2] = {0};
    ret = this->readReg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[id] + 2, data, 2);
    if (speed)
    {
        *speed = (int16_t)(((uint16_t)data[0] << 8) | data[1]);
    }
    return ret;
}

int s4s_mainBoard::encoder_motor_get_power(uint8_t id, uint16_t * power)
{
    int ret = 0;
    uint8_t data[2] = {0};
    ret = this->readReg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[id] + 3, data, 2);
    if (power)
    {
        *power = (uint16_t)(((uint16_t)data[0] << 8) | data[1]);
    }
    return ret;
}

int s4s_mainBoard::encoder_motor_reset_angle(uint8_t id)
{
    int ret = 0;
    uint8_t data[4] = {0};
    ret += this->writeReg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[id] + 0, data, 4);
    return ret;
}

int s4s_mainBoard::encoder_motor_set_action(uint8_t id, uint8_t action)
{
    int ret = 0;
    ret += this->writeReg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[id] + 4, &action, 1);
    return ret;
}

int s4s_mainBoard::encoder_motor_set_rpm_speed(uint8_t id, uint16_t speed)
{
    int ret = 0;
    uint8_t data[2] = {0};
    data[0] = (speed >> 8) & 0xFF;
    data[1] = speed & 0xFF;
    ret += this->writeReg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[id] + 5, data, 2);
    return ret;
}

int s4s_mainBoard::encoder_motor_set_dynamic_speed(uint8_t id, uint16_t speed)
{
    int ret = 0;
    uint8_t data[2] = {0};
    data[0] = (speed >> 8) & 0xFF;
    data[1] = speed & 0xFF;
    ret += this->writeReg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[id] + 6, data, 2);
    return ret;
}

int s4s_mainBoard::encoder_motor_set_power(uint8_t id, uint8_t power)
{
    int ret = 0;
    ret += this->writeReg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[id] + 7, &power, 1);
    return ret;
}

int s4s_mainBoard::encoder_motor_set_ring(uint8_t id, uint16_t ring)
{
    int ret = 0;
    uint8_t data[2];
    data[0] = (ring >> 8) & 0xFF;
    data[1] = ring & 0xFF;
    ret += this->writeReg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[id] + 8, data, 2);
    return ret;
}

int s4s_mainBoard::encoder_motor_set_relative_angle(uint8_t id, uint16_t relativeAngle)
{
    int ret = 0;
    uint8_t data[2];
    data[0] = (relativeAngle >> 8) & 0xFF;
    data[1] = relativeAngle & 0xFF;
    ret += this->writeReg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[id] + 9, data, 2);
    return ret;
}

int s4s_mainBoard::encoder_motor_set_time(uint8_t id, uint16_t runTime)
{
    int ret = 0;
    uint8_t data[2];
    data[0] = (runTime >> 8) & 0xFF;
    data[1] = runTime & 0xFF;
    ret += this->writeReg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[id] + 10, data, 2);
    return ret;
}

int s4s_mainBoard::encoder_motor_set_centimeter(uint8_t id, uint16_t centimeter)
{
    int ret = 0;
    uint8_t data[2];
    data[0] = (centimeter >> 8) & 0xFF;
    data[1] = centimeter & 0xFF;
    ret += this->writeReg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[id] + 11, data, 2);
    return ret;
}

int s4s_mainBoard::encoder_motor_get_action_runing(uint8_t id, uint8_t * running)
{
    int ret = 0;
    ret += this->readReg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[id] + 12, running, 1);
    return ret;
}

int s4s_mainBoard::encoder_motor_pair_set_action(uint8_t action)
{
    int ret = 0;
    ret += this->writeReg(MAINBOARD_ADDR, ENCODER_MOTOR_PAIR_REG + 0, &action, 1);
    return ret;
}

int s4s_mainBoard::encoder_motor_pair_set_group(uint8_t l_id, uint8_t r_id)
{
    int ret = 0;
    uint8_t data[2] = {0};
    data[0] = l_id;
    data[1] = r_id;
    ret += this->writeReg(MAINBOARD_ADDR, ENCODER_MOTOR_PAIR_REG + 1, data, 2);
    return ret;
}

int s4s_mainBoard::encoder_motor_pair_set_dynamic_speed(uint16_t l_speed, uint16_t r_speed)
{
    int ret = 0;
    uint8_t data[4] = {0};
    l_speed = DATA_MAX(0, DATA_MIN(100, l_speed));
    r_speed = DATA_MAX(0, DATA_MIN(100, r_speed));
    data[0] = (uint8_t)(l_speed >> 8) & 0xFF;
    data[1] = (uint8_t)(l_speed) & 0xFF;
    data[2] = (uint8_t)(r_speed >> 8) & 0xFF;
    data[3] = (uint8_t)(r_speed) & 0xFF;
    ret += this->writeReg(MAINBOARD_ADDR, ENCODER_MOTOR_PAIR_REG + 2, data, 4);
    return ret;
}

int s4s_mainBoard::encoder_motor_pair_set_time(uint16_t runTime)
{
    int ret = 0;
    uint8_t data[2] = {0};
    data[0] = (uint8_t)(runTime >> 8) & 0xFF;
    data[1] = (uint8_t)(runTime) & 0xFF;
    ret += this->writeReg(MAINBOARD_ADDR, ENCODER_MOTOR_PAIR_REG + 3, data, 2);
    return ret;
}

int s4s_mainBoard::encoder_motor_pair_set_ring(uint16_t ring)
{
    int ret = 0;
    uint8_t data[4] = {0};
    data[0] = (uint8_t)(ring >> 8) & 0xFF;
    data[1] = (uint8_t)(ring) & 0xFF;
    data[2] = (uint8_t)(ring >> 8) & 0xFF;
    data[3] = (uint8_t)(ring) & 0xFF;
    ret += this->writeReg(MAINBOARD_ADDR, ENCODER_MOTOR_PAIR_REG + 4, data, 4);
    return ret;
}

int s4s_mainBoard::encoder_motor_pair_set_centimeter(uint16_t centimeter)
{
    int ret = 0;
    uint8_t data[4] = {0};
    data[0] = (uint8_t)(centimeter >> 8) & 0xFF;
    data[1] = (uint8_t)(centimeter) & 0xFF;
    data[2] = (uint8_t)(centimeter >> 8) & 0xFF;
    data[3] = (uint8_t)(centimeter) & 0xFF;
    ret += this->writeReg(MAINBOARD_ADDR, ENCODER_MOTOR_PAIR_REG + 5, data, 4);
    return ret;
}

int s4s_mainBoard::encoder_motor_pair_get_action_runing(uint8_t * running)
{
    int ret = 0;
    ret += this->readReg(MAINBOARD_ADDR, ENCODER_MOTOR_PAIR_REG + 6, running, 1);
    return ret;
}

uint16_t s4s_mainBoard::ultr_get_distance(void)
{
    uint8_t data[3] = {0};
    uint32_t distance = 0;
    // The two IIC operations must be at least 50ms apart.
    if (millis() - this->ultr_getDistance_last_tick < 50)
    {
        return this->ultr_last_distance;
    }
    this->ultr_getDistance_last_tick = millis();

    this->readReg(ULTR_ADDR, 0x01, data, 3);
    distance =  ((uint32_t)data[0])<<16  | ((uint32_t)data[1])<<8 | ((uint32_t)data[0])<<0;
    this->ultr_last_distance = distance / 10000;
    return this->ultr_last_distance;
} 

void s4s_mainBoard::ultr_set_color(uint8_t light, uint8_t color[3])
{
    // The two IIC operations must be at least 50ms apart.
    if (millis() - this->ultr_setColor_last_tick < 50)
    {
        return;
    }
    this->ultr_setColor_last_tick = millis();

    uint8_t data[4] = {0};
    data[0] = light;
    data[1] = color[0];
    data[2] = color[1];
    data[3] = color[2];
    this->writeReg(ULTR_ADDR, 0x02, data, 4);
}

void s4s_mainBoard::ultr_set_color(uint8_t light, uint8_t r, uint8_t g, uint8_t b)
{
    uint8_t color[] = {r, g, b};
    this->ultr_set_color(light, color);
}


/**
 * Gray sensor (line sensor) helper functions.
 * Note: The gray sensor shares the I2C address 0x6F with the gyro on some boards.
 * These functions use raw writeData / readData (no register prefix).
 */

/** Calibrate gray sensor — capture current surface as reference gray level */
void s4s_mainBoard::gray_grayStudy(void)
{
    uint8_t data[1] = {4};
    this->writeData(GYRO_ADDR, data, sizeof(data));
    delay(100);
}

/** Calibrate gray sensor — capture binary (black/white) threshold */
void s4s_mainBoard::gray_binaryStudy(void)
{
    uint8_t data[1] = {5};
    this->writeData(GYRO_ADDR, data, sizeof(data));
    delay(100);
}

/** Calibrate gray sensor — capture a specific colour sample */
void s4s_mainBoard::gray_colorStudy(enum COLOR_TYPE colorType)
{
    uint8_t data[1] = { static_cast<uint8_t>(colorType + 6) };
    this->writeData(GYRO_ADDR, data, sizeof(data));
    delay(100);
}

/** Clear all stored colour calibration data */
void s4s_mainBoard::gray_clearColor(void)
{
    uint8_t data[1] = {6};
    this->writeData(GYRO_ADDR, data, sizeof(data));
    delay(100);
}

/** Read raw gray (reflectance) values from all 4 sensor channels */
void s4s_mainBoard::gray_getGrayData(uint8_t data[4])
{
    uint8_t _data[1] = {2};
    this->writeData(GYRO_ADDR, _data, sizeof(_data));
    this->readData(GYRO_ADDR, data, 4);
}

/** Read colour-classified data from all 4 sensor channels */
void s4s_mainBoard::gray_getColorData(uint8_t data[4])
{
    uint8_t _data[1] = {1};
    this->writeData(GYRO_ADDR, _data, sizeof(_data));
    this->readData(GYRO_ADDR, data, 4);
}

/** Read binary (black=1, white=0) data from all 4 sensor channels */
void s4s_mainBoard::gray_getBlack(uint8_t data[4])
{
    uint8_t _data[1] = {3};
    this->writeData(GYRO_ADDR, _data, sizeof(_data));
    this->readData(GYRO_ADDR, data, 4);
}

/** Read raw photosensitive (light intensity) values from all 4 channels */
void s4s_mainBoard::gray_getPhotosensitive(uint8_t data[4])
{
    uint8_t _data[1] = {15};
    this->writeData(GYRO_ADDR, _data, sizeof(_data));
    this->readData(GYRO_ADDR, data, 4);
}
