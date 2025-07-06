#include "peripherals/sensor_reader.h" // Assuming -I../../src makes peripherals/sensor_reader.h available

// This is a stub implementation.
// When testing modules that USE this, sensor_reader.h will be mocked by CMock.
// This .c file would not be linked into such tests.
// It's provided for completeness of the module itself if it were to be used directly or tested itself.

bool sensor_init(void) {
    // Placeholder: Simulate sensor initialization
    // In a real scenario, this would configure I2C/SPI, check sensor ID, etc.
    return true; // Assume success
}

int16_t sensor_read_temperature_degrees_c(void) {
    // Placeholder: Simulate reading temperature
    // Real implementation would read from a hardware sensor.
    return 250; // Default value: 25.0 C
}

uint16_t sensor_read_humidity_percent_rh(void) {
    // Placeholder: Simulate reading humidity
    return 500; // Default value: 50.0 %RH
}

bool sensor_self_test(uint8_t* result_code) {
    // Placeholder: Simulate sensor self-test
    if (result_code) {
        *result_code = 0x00; // Success
    }
    return true;
}
