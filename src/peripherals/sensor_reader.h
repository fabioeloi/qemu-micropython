#ifndef SENSOR_READER_H
#define SENSOR_READER_H

#include <stdbool.h>
#include <stdint.h>

// Example sensor reading functions
// In a real scenario, these might interact with I2C, SPI, ADC etc.

bool sensor_init(void);
int16_t sensor_read_temperature_degrees_c(void); // Returns temperature in degrees C * 10 (e.g., 255 for 25.5 C)
uint16_t sensor_read_humidity_percent_rh(void); // Returns humidity in %RH * 10 (e.g., 455 for 45.5 %RH)
bool sensor_self_test(uint8_t* result_code);

#endif // SENSOR_READER_H
