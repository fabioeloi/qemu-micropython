#include "processing/data_processor.h"
#include "peripherals/sensor_reader.h" // Dependency to be mocked
#include <stdio.h> // For snprintf

sensor_system_status_t initialize_sensor_system(void) {
    if (!sensor_init()) {
        return SENSOR_STATUS_ERROR_INIT;
    }
    uint8_t self_test_result;
    if (!sensor_self_test(&self_test_result) || self_test_result != 0x00) {
        return SENSOR_STATUS_ERROR_SELF_TEST;
    }
    return SENSOR_STATUS_OK;
}

bool process_and_format_sensor_data(char* buffer, size_t buffer_size) {
    if (buffer == NULL || buffer_size == 0) {
        return false;
    }

    int16_t temp_raw = sensor_read_temperature_degrees_c();
    uint16_t hum_raw = sensor_read_humidity_percent_rh();

    // Example: Simple check for "error" values if sensor could return them
    // (though our current stub sensor_reader doesn't, mocks can simulate this)
    // if (temp_raw == INT16_MAX || hum_raw == UINT16_MAX) {
    //     return SENSOR_STATUS_ERROR_READ; // Need to adapt return type or error handling
    // }
    // For this example, assume reads are always "valid" numbers from sensor_reader functions

    float temperature = (float)temp_raw / 10.0f;
    float humidity = (float)hum_raw / 10.0f;

    // Format the data into the buffer
    // Example format: "T:25.5C, H:45.0%"
    int written = snprintf(buffer, buffer_size, "T:%.1fC, H:%.1f%%", temperature, humidity);

    if (written < 0 || (size_t)written >= buffer_size) {
        // Formatting error or buffer too small
        return false;
    }

    return true;
}
