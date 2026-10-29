idf_component_register(SRCS "main.c" "icrobot.c"
                    INCLUDE_DIRS "."
                    REQUIRES driver esp_driver_i2c)
