/**
 * @file main.c
 * @brief Standalone ESP-IDF Application for ICRobot (ESP32-S3)
 */

#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "icrobot.h"

static const char *TAG = "APP_MAIN";

void robot_behavior_task(void *pvParameters)
{
    ESP_LOGI(TAG, "Starting ICRobot behavior loop...");

    // Check battery level
    uint8_t battery = 0;
    if (icrobot_get_battery(&battery) == ESP_OK) {
        ESP_LOGI(TAG, "🔋 Battery Level: %d%%", battery);
    }

    // Set ambient light to Green
    icrobot_set_led(0, 255, 0, 50);

    // Initial 2-axis arm position (90° base, 45° gripper)
    ESP_LOGI(TAG, "🦾 Positioning 2-axis arm...");
    icrobot_set_arm(90, 45);
    vTaskDelay(pdMS_TO_TICKS(1000));

    // Drive forward 20 cm
    ESP_LOGI(TAG, "🚗 Driving forward 20 cm...");
    icrobot_set_speed(60, 60);
    icrobot_move_cm(ICROBOT_MOVE_FORWARD, 20);
    vTaskDelay(pdMS_TO_TICKS(500));

    // Pick-and-place arm movement
    ESP_LOGI(TAG, "🦾 Lowering arm and clamping...");
    icrobot_set_arm(140, 90); // Lower
    vTaskDelay(pdMS_TO_TICKS(800));
    icrobot_set_arm(140, 20); // Clamp
    vTaskDelay(pdMS_TO_TICKS(500));
    icrobot_set_arm(70, 20);  // Lift object
    vTaskDelay(pdMS_TO_TICKS(1000));

    // Turn right for 500 ms
    ESP_LOGI(TAG, "🔄 Turning right...");
    icrobot_move_ms(ICROBOT_MOVE_RIGHT, 500);
    vTaskDelay(pdMS_TO_TICKS(500));

    // Release arm to save servo power
    ESP_LOGI(TAG, "💤 Releasing arm servos...");
    icrobot_release_arm();

    // Blue breathing light loop
    while (1) {
        icrobot_set_led(0, 0, 255, 30);
        vTaskDelay(pdMS_TO_TICKS(1000));
        icrobot_set_led(0, 200, 255, 10);
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

void app_main(void)
{
    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "  DPSI_TinkerTek Open-Source Firmware   ");
    ESP_LOGI(TAG, "  Running on ESP32-S3 (ESP-IDF v5)      ");
    ESP_LOGI(TAG, "========================================");

    // Initialize robot I2C bus and motor controller
    ESP_ERROR_CHECK(icrobot_init());

    // Pin robot task to Core 1
    xTaskCreatePinnedToCore(
        robot_behavior_task,
        "robot_behavior",
        4096,
        NULL,
        5,
        NULL,
        1
    );
}
