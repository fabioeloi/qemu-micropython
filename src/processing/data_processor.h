#ifndef DATA_PROCESSOR_H
#define DATA_PROCESSOR_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    SENSOR_STATUS_OK,
    SENSOR_STATUS_ERROR_INIT,
    SENSOR_STATUS_ERROR_READ,
    SENSOR_STATUS_ERROR_SELF_TEST
} sensor_system_status_t;

// Initializes the sensor system and returns its status
sensor_system_status_t initialize_sensor_system(void);

// Reads sensor data, processes it, and stores it in the provided buffer.
// Returns true on success, false on failure.
// Buffer should be large enough for formatted string.
bool process_and_format_sensor_data(char* buffer, size_t buffer_size);

#endif // DATA_PROCESSOR_H
