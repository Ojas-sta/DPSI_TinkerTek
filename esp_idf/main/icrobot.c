/**
 * @file icrobot.c
 * @brief Open-Source ESP-IDF Driver Implementation for ICRobot
 */

#include "icrobot.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "ICROBOT";

#define I2C_TIMEOUT_MS  1000

// Helper function to write to an I2C sub-register
static esp_err_t write_reg(uint8_t dev_addr, uint8_t reg, const uint8_t *data, size_t len)
{
    uint8_t buffer[len + 1];
    buffer[0] = reg;
    if (len > 0 && data != NULL) {
        memcpy(&buffer[1], data, len);
    }
    return i2c_master_write_to_device(ICROBOT_I2C_PORT, dev_addr, buffer, len + 1, pdMS_TO_TICKS(I2C_TIMEOUT_MS));
}

// Helper function to read from an I2C sub-register
static esp_err_t read_reg(uint8_t dev_addr, uint8_t reg, uint8_t *data, size_t len)
{
    return i2c_master_write_read_device(ICROBOT_I2C_PORT, dev_addr, &reg, 1, data, len, pdMS_TO_TICKS(I2C_TIMEOUT_MS));
}

esp_err_t icrobot_init(void)
{
    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = ICROBOT_I2C_SDA_PIN,
        .scl_io_num = ICROBOT_I2C_SCL_PIN,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = ICROBOT_I2C_FREQ_HZ,
    };

    esp_err_t ret = i2c_param_config(ICROBOT_I2C_PORT, &conf);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "I2C param config failed");
        return ret;
    }

    ret = i2c_driver_install(ICROBOT_I2C_PORT, conf.mode, 0, 0, 0);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "I2C driver install failed");
        return ret;
    }

    ESP_LOGI(TAG, "I2C initialized on SDA=GPIO%d, SCL=GPIO%d", ICROBOT_I2C_SDA_PIN, ICROBOT_I2C_SCL_PIN);

    // Pair Left Motor (ID 0) and Right Motor (ID 1)
    uint8_t pair_data[2] = {0, 1};
    ret = write_reg(ICROBOT_MAINBOARD_ADDR, REG_MOTOR_PAIR_GROUP, pair_data, 2);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Mainboard 0x0F not responding, check power/connections");
    } else {
        ESP_LOGI(TAG, "ICRobot Mainboard connected successfully at 0x0F");
    }

    // Default speed 50%
    icrobot_set_speed(50, 50);

    return ESP_OK;
}

esp_err_t icrobot_set_arm(uint8_t axis1_deg, uint8_t axis2_deg)
{
    if (axis1_deg > 180) axis1_deg = 180;
    if (axis2_deg > 180) axis2_deg = 180;

    esp_err_t ret1 = write_reg(ICROBOT_MAINBOARD_ADDR, REG_SERVO_BASE + 0, &axis1_deg, 1);
    esp_err_t ret2 = write_reg(ICROBOT_MAINBOARD_ADDR, REG_SERVO_BASE + 1, &axis2_deg, 1);

    return (ret1 == ESP_OK && ret2 == ESP_OK) ? ESP_OK : ESP_FAIL;
}

esp_err_t icrobot_release_arm(void)
{
    uint8_t zero = 0x00;
    write_reg(ICROBOT_MAINBOARD_ADDR, REG_SERVO_RELEASE_BASE + 0, &zero, 1);
    write_reg(ICROBOT_MAINBOARD_ADDR, REG_SERVO_RELEASE_BASE + 1, &zero, 1);
    return ESP_OK;
}

esp_err_t icrobot_set_servo_speed(uint8_t servo_id, int8_t speed)
{
    if (servo_id > 1) return ESP_ERR_INVALID_ARG;
    if (speed < -100) speed = -100;
    if (speed > 100) speed = 100;

    uint8_t val = (uint8_t)speed;
    return write_reg(ICROBOT_MAINBOARD_ADDR, REG_SERVO_SPEED_BASE + servo_id, &val, 1);
}

esp_err_t icrobot_set_speed(uint16_t left_speed, uint16_t right_speed)
{
    if (left_speed > 100) left_speed = 100;
    if (right_speed > 100) right_speed = 100;

    uint8_t speed_buf[4] = {
        (uint8_t)((left_speed >> 8) & 0xFF),
        (uint8_t)(left_speed & 0xFF),
        (uint8_t)((right_speed >> 8) & 0xFF),
        (uint8_t)(right_speed & 0xFF)
    };
    return write_reg(ICROBOT_MAINBOARD_ADDR, REG_MOTOR_PAIR_SPEED, speed_buf, 4);
}

esp_err_t icrobot_start_move(icrobot_direction_t dir)
{
    uint8_t action = (uint8_t)dir;
    return write_reg(ICROBOT_MAINBOARD_ADDR, REG_MOTOR_PAIR_ACTION, &action, 1);
}

esp_err_t icrobot_stop(void)
{
    return icrobot_start_move(ICROBOT_MOVE_STOP);
}

esp_err_t icrobot_wait_motor_done(uint32_t timeout_ms)
{
    uint32_t elapsed = 0;
    vTaskDelay(pdMS_TO_TICKS(100));

    while (elapsed < timeout_ms) {
        uint8_t status = 0;
        esp_err_t ret = read_reg(ICROBOT_MAINBOARD_ADDR, REG_MOTOR_PAIR_STATUS, &status, 1);
        if (ret == ESP_OK && status == 0) {
            return ESP_OK;
        }
        vTaskDelay(pdMS_TO_TICKS(50));
        elapsed += 50;
    }
    return ESP_ERR_TIMEOUT;
}

esp_err_t icrobot_move_ms(icrobot_direction_t dir, uint16_t duration_ms)
{
    if (dir == ICROBOT_MOVE_STOP) {
        return icrobot_stop();
    }

    uint8_t time_buf[2] = {
        (uint8_t)((duration_ms >> 8) & 0xFF),
        (uint8_t)(duration_ms & 0xFF)
    };
    write_reg(ICROBOT_MAINBOARD_ADDR, REG_MOTOR_PAIR_TIME, time_buf, 2);

    // Timed action offset in firmware: direction + 5 (state=0)
    uint8_t action = dir + 5;
    write_reg(ICROBOT_MAINBOARD_ADDR, REG_MOTOR_PAIR_ACTION, &action, 1);

    return icrobot_wait_motor_done(duration_ms + 1000);
}

esp_err_t icrobot_move_cm(icrobot_direction_t dir, uint16_t distance_cm)
{
    if (dir == ICROBOT_MOVE_STOP) {
        return icrobot_stop();
    }

    uint8_t dist_buf[4] = {
        (uint8_t)((distance_cm >> 8) & 0xFF),
        (uint8_t)(distance_cm & 0xFF),
        (uint8_t)((distance_cm >> 8) & 0xFF),
        (uint8_t)(distance_cm & 0xFF)
    };
    write_reg(ICROBOT_MAINBOARD_ADDR, REG_MOTOR_PAIR_DISTANCE, dist_buf, 4);

    // Distance action offset in firmware: direction + 5 + (2 * 4) = direction + 13
    uint8_t action = dir + 13;
    write_reg(ICROBOT_MAINBOARD_ADDR, REG_MOTOR_PAIR_ACTION, &action, 1);

    return icrobot_wait_motor_done(15000); // 15 second safety timeout
}

esp_err_t icrobot_get_battery(uint8_t *battery_pct)
{
    if (battery_pct == NULL) return ESP_ERR_INVALID_ARG;
    return read_reg(ICROBOT_MAINBOARD_ADDR, REG_POWER_BATTERY, battery_pct, 1);
}

esp_err_t icrobot_is_charging(bool *is_charging)
{
    if (is_charging == NULL) return ESP_ERR_INVALID_ARG;
    uint8_t val = 0;
    esp_err_t ret = read_reg(ICROBOT_MAINBOARD_ADDR, REG_POWER_CHARGING, &val, 1);
    *is_charging = (val == 1);
    return ret;
}

esp_err_t icrobot_set_led(uint8_t r, uint8_t g, uint8_t b, uint8_t brightness)
{
    write_reg(ICROBOT_MAINBOARD_ADDR, REG_AMBIENT_LIGHT_BRI, &brightness, 1);
    uint8_t rgb[3] = {r, g, b};
    return write_reg(ICROBOT_MAINBOARD_ADDR, REG_AMBIENT_LIGHT_RGB, rgb, 3);
}
