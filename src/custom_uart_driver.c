/*
 * Custom UART Driver for QEMU-MicroPython Integration
 *
 * This file implements a custom UART driver that extends the STM32F2XX USART functionality
 * with enhanced debugging and testing capabilities for MicroPython IoT applications.
 * It is designed to be used with QEMU emulation to improve the development experience.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <time.h>
#include <unistd.h>
#include <fcntl.h>
#include <math.h>
#include <stdint.h>
#include "custom_uart_driver.h"

/* Buffer sizes */
const uint16_t UART_TX_BUFFER_SIZE_VAR = 1024;
const uint16_t UART_RX_BUFFER_SIZE_VAR = 1024;

// Status flags
#define UART_FLAG_OVERFLOW   (1 << 0)
#define UART_FLAG_UNDERFLOW  (1 << 1)
#define UART_STATUS_LOOPBACK     (1 << 2)
#define UART_STATUS_RECORDING    (1 << 3)
#define UART_STATUS_NOISE_SIM    (1 << 4)
#define UART_STATUS_TIMING_SIM   (1 << 5)
#define UART_STATUS_DEBUG_MODE   (1 << 6)
#define UART_STATUS_TX_ACTIVE    (1 << 7)
#define UART_STATUS_RX_ACTIVE    (1 << 8)

// Error flags
#define UART_ERROR_OVERFLOW      (1 << 0)
#define UART_ERROR_UNDERFLOW     (1 << 1)
#define UART_ERROR_FRAMING       (1 << 2)
#define UART_ERROR_PARITY        (1 << 3)
#define UART_ERROR_NOISE         (1 << 4)
#define UART_ERROR_BREAK         (1 << 5)

/* Forward declarations for helper functions */
static bool uart_tx_buffer_full(CustomUARTDriver* driver);
static bool uart_rx_buffer_full(CustomUARTDriver* driver);
static bool uart_tx_buffer_empty(CustomUARTDriver* driver);
static bool uart_rx_buffer_empty(CustomUARTDriver* driver);
static void uart_simulate_timing(CustomUARTDriver* driver, uint32_t bytes_count);
static void uart_update_byte_time(CustomUARTDriver* driver);
static void uart_record_data(CustomUARTDriver* driver, const uint8_t* data, size_t size, bool is_tx);

/* Public API Implementation */

CustomUARTDriver* custom_uart_init(uint32_t uart_id, uint32_t baudrate) {
    // Allocate memory for the driver
    CustomUARTDriver* driver = (CustomUARTDriver*)malloc(sizeof(CustomUARTDriver));
    if (driver == NULL) {
        fprintf(stderr, "Failed to allocate memory for UART driver\n");
        return NULL;
    }
    
    // Initialize the driver
    memset(driver, 0, sizeof(CustomUARTDriver));
    
    // Set base configuration
    driver->uart_id = uart_id;
    driver->baudrate = baudrate;
    
    // Set default communication parameters
    driver->data_bits = 8;
    driver->stop_bits = 1;
    driver->parity = CUSTOM_UART_PARITY_NONE;
    driver->flow_control = false;
    
    // Set initial state
    driver->state = UART_STATE_IDLE;
    driver->status_flags = 0;
    driver->error_flags = 0;
    
    // Initialize buffer pointers
    driver->tx_head = 0;
    driver->tx_tail = 0;
    driver->tx_count = 0;
    driver->rx_head = 0;
    driver->rx_tail = 0;
    driver->rx_count = 0;
    
    // Initialize timing
    driver->last_tx_time = 0;
    driver->last_rx_time = 0;
    uart_update_byte_time(driver);
    
    // Initialize features
    driver->loopback_enabled = false;
    driver->record_enabled = false;
    driver->record_filename = NULL;
    driver->record_file = NULL;
    
    driver->error_rate = 0.0f;
    driver->noise_level = 0.0f;
    driver->simulate_timing = false;
    
    driver->debug_tx_callback = NULL;
    driver->debug_rx_callback = NULL;
    driver->debug_user_data = NULL;
    
    driver->qemu_char_driver = NULL;
    driver->qemu_irq_handler = NULL;
    
    // Seed random number generator for error/noise simulation
    srand((unsigned int)time(NULL));
    
    return driver;
}

bool custom_uart_configure(CustomUARTDriver* driver, uint8_t data_bits, 
                            uint8_t stop_bits, uint8_t parity, bool flow_control) {
    if (driver == NULL) {
        return false;
    }
    
    // Validate parameters
    if (data_bits < 5 || data_bits > 9) {
        fprintf(stderr, "Invalid data bits: %d (must be 5-9)\n", data_bits);
        return false;
    }
    
    if (stop_bits < 1 || stop_bits > 2) {
        fprintf(stderr, "Invalid stop bits: %d (must be 1-2)\n", stop_bits);
        return false;
    }
    
    if (parity > CUSTOM_UART_PARITY_EVEN) {
        fprintf(stderr, "Invalid parity: %d\n", parity);
        return false;
    }
    
    // Update configuration
    driver->data_bits = data_bits;
    driver->stop_bits = stop_bits;
    driver->parity = parity;
    driver->flow_control = flow_control;
    
    // Update timing parameters
    uart_update_byte_time(driver);
    
    return true;
}

bool custom_uart_set_baudrate(CustomUARTDriver* driver, uint32_t baudrate) {
    if (driver == NULL) {
        return false;
    }
    
    if (baudrate == 0) {
        fprintf(stderr, "Invalid baudrate: %d\n", baudrate);
        return false;
    }
    
    driver->baudrate = baudrate;
    uart_update_byte_time(driver);
    
    return true;
}

void custom_uart_set_loopback(CustomUARTDriver* driver, bool enable) {
    if (driver == NULL) {
        return;
    }
    
    driver->loopback_enabled = enable;
    
    if (enable) {
        driver->status_flags |= UART_STATUS_LOOPBACK;
    } else {
        driver->status_flags &= ~UART_STATUS_LOOPBACK;
    }
    
    printf("Loopback mode %s\n", enable ? "enabled" : "disabled");
}

bool custom_uart_start_recording(CustomUARTDriver* driver, const char* filename) {
    if (driver == NULL || filename == NULL) {
        return false;
    }
    
    // If already recording, stop it first
    if (driver->record_enabled) {
        custom_uart_stop_recording(driver);
    }
    
    // Open the file for writing
    driver->record_file = fopen(filename, "wb");
    if (driver->record_file == NULL) {
        fprintf(stderr, "Failed to open recording file: %s\n", filename);
        return false;
    }
    
    // Save the filename
    driver->record_filename = strdup(filename);
    driver->record_enabled = true;
    driver->status_flags |= UART_STATUS_RECORDING;
    
    printf("Recording started to file: %s\n", filename);
    return true;
}

void custom_uart_stop_recording(CustomUARTDriver* driver) {
    if (driver == NULL) {
        return;
    }
    
    if (driver->record_enabled) {
        if (driver->record_file != NULL) {
            fclose(driver->record_file);
            driver->record_file = NULL;
        }
        
        if (driver->record_filename != NULL) {
            free(driver->record_filename);
            driver->record_filename = NULL;
        }
        
        driver->record_enabled = false;
        driver->status_flags &= ~UART_STATUS_RECORDING;
        
        printf("Recording stopped\n");
    }
}

void custom_uart_set_error_simulation(CustomUARTDriver* driver, float error_rate) {
    if (driver == NULL) {
        return;
    }
    
    // Clamp error rate between 0.0 and 1.0
    if (error_rate < 0.0f) {
        error_rate = 0.0f;
    } else if (error_rate > 1.0f) {
        error_rate = 1.0f;
    }
    
    driver->error_rate = error_rate;
    
    if (error_rate > 0.0f) {
        printf("Error simulation enabled (rate: %.2f)\n", error_rate);
    } else {
        printf("Error simulation disabled\n");
    }
}

void custom_uart_set_noise_simulation(CustomUARTDriver* driver, float noise_level) {
    if (driver == NULL) {
        return;
    }
    
    // Clamp noise level between 0.0 and 1.0
    if (noise_level < 0.0f) {
        noise_level = 0.0f;
    } else if (noise_level > 1.0f) {
        noise_level = 1.0f;
    }
    
    driver->noise_level = noise_level;
    
    if (noise_level > 0.0f) {
        driver->status_flags |= UART_STATUS_NOISE_SIM;
        printf("Noise simulation enabled (level: %.2f)\n", noise_level);
    } else {
        driver->status_flags &= ~UART_STATUS_NOISE_SIM;
        printf("Noise simulation disabled\n");
    }
}

void custom_uart_set_timing_simulation(CustomUARTDriver* driver, bool enable) {
    if (driver == NULL) {
        return;
    }
    
    driver->simulate_timing = enable;
    
    if (enable) {
        driver->status_flags |= UART_STATUS_TIMING_SIM;
        printf("Timing simulation enabled\n");
    } else {
        driver->status_flags &= ~UART_STATUS_TIMING_SIM;
        printf("Timing simulation disabled\n");
    }
}

void custom_uart_set_debug_callbacks(CustomUARTDriver* driver, 
                                     void (*tx_callback)(uint8_t, void*),
                                     void (*rx_callback)(uint8_t, void*),
                                     void* user_data) {
    if (driver == NULL) {
        return;
    }
    
    driver->debug_tx_callback = tx_callback;
    driver->debug_rx_callback = rx_callback;
    driver->debug_user_data = user_data;
    
    if (tx_callback != NULL || rx_callback != NULL) {
        driver->status_flags |= UART_STATUS_DEBUG_MODE;
        printf("Debug callbacks registered\n");
    } else {
        driver->status_flags &= ~UART_STATUS_DEBUG_MODE;
        printf("Debug callbacks cleared\n");
    }
}

bool custom_uart_send_byte(CustomUARTDriver* driver, uint8_t byte) {
    if (!driver) return false;
    
    // Check if the transmit buffer is full
    if (uart_tx_buffer_full(driver)) {
        // Set overflow error flag and return failure
        driver->error_flags |= UART_ERROR_OVERFLOW;
        return false;
    }
    
    // Store the byte in the transmit buffer regardless of loopback mode
    driver->tx_buffer[driver->tx_head] = byte;
    driver->tx_head = (driver->tx_head + 1) % UART_TX_BUFFER_SIZE;
    driver->tx_count++;
    
    // Call debug TX callback if registered
    if (driver->debug_tx_callback) {
        driver->debug_tx_callback(byte, driver->debug_user_data);
    }
    
    // Check if in loopback mode
    if (driver->loopback_enabled) {
        // In loopback mode, immediately receive the byte
        custom_uart_receive_byte(driver, byte);
    }
    
    // Simulate timing if enabled
    if (driver->simulate_timing) {
        uart_simulate_timing(driver, 1);
    }
    
    // Record the data if recording is enabled
    if (driver->record_enabled && driver->record_file) {
        uart_record_data(driver, &byte, 1, true);
    }
    
    return true;
}

size_t custom_uart_send_data(CustomUARTDriver* driver, const uint8_t* data, size_t length) {
    if (driver == NULL || data == NULL || length == 0) {
        return 0;
    }
    
    size_t bytes_sent = 0;
    for (size_t i = 0; i < length; i++) {
        if (custom_uart_send_byte(driver, data[i])) {
            bytes_sent++;
        } else {
            break;  // Buffer full or other error
        }
    }
    
    return bytes_sent;
}

bool custom_uart_receive_byte(CustomUARTDriver* driver, uint8_t byte) {
    if (driver == NULL) {
        return false;
    }
    
    // Simulate errors if enabled
    if (driver->error_rate > 0.0f) {
        float r = (float)rand() / (float)RAND_MAX;
        if (r < driver->error_rate) {
            // Simulate an error by setting the error flag and discarding the byte
            driver->error_flags |= UART_ERROR_FRAMING;
            return false;
        }
    }
    
    // Simulate noise if enabled
    if (driver->noise_level > 0.0f) {
        float r = (float)rand() / (float)RAND_MAX;
        if (r < driver->noise_level) {
            // Simulate noise by flipping a random bit
            int bit_pos = rand() % 8;
            byte ^= (1 << bit_pos);
            driver->error_flags |= UART_ERROR_NOISE;
        }
    }
    
    if (uart_rx_buffer_full(driver)) {
        // Set overflow flag
        driver->error_flags |= UART_ERROR_OVERFLOW;
        return false;
    }
    
    // Add the byte to the RX buffer
    driver->rx_buffer[driver->rx_head] = byte;
    driver->rx_head = (driver->rx_head + 1) % UART_RX_BUFFER_SIZE;
    driver->rx_count++;
    
    // Update the state
    driver->state = UART_STATE_RECEIVING;
    
    // Record the data if recording is enabled
    if (driver->record_enabled && driver->record_file != NULL) {
        uart_record_data(driver, &byte, 1, false);
    }
    
    // Call the debug callback if registered
    if (driver->debug_rx_callback != NULL) {
        driver->debug_rx_callback(byte, driver->debug_user_data);
    }
    
    return true;
}

bool custom_uart_read_byte(CustomUARTDriver* driver, uint8_t* byte) {
    if (driver == NULL || byte == NULL) {
        return false;
    }
    
    if (uart_rx_buffer_empty(driver)) {
        return false;
    }
    
    // Get the byte from the RX buffer
    *byte = driver->rx_buffer[driver->rx_tail];
    driver->rx_tail = (driver->rx_tail + 1) % UART_RX_BUFFER_SIZE;
    driver->rx_count--;
    
    // If the buffer is now empty, update the state
    if (driver->rx_count == 0) {
        driver->state = UART_STATE_IDLE;
    }
    
    return true;
}

size_t custom_uart_read_data(CustomUARTDriver* driver, uint8_t* buffer, size_t max_length) {
    if (driver == NULL || buffer == NULL || max_length == 0) {
        return 0;
    }
    
    size_t bytes_read = 0;
    for (size_t i = 0; i < max_length; i++) {
        if (custom_uart_read_byte(driver, &buffer[i])) {
            bytes_read++;
        } else {
            break;  // No more data
        }
    }
    
    return bytes_read;
}

size_t custom_uart_available(CustomUARTDriver* driver) {
    if (driver == NULL) {
        return 0;
    }
    
    return driver->rx_count;
}

void custom_uart_flush_tx(CustomUARTDriver* driver) {
    if (driver == NULL) {
        return;
    }
    
    // Reset the TX buffer
    driver->tx_head = 0;
    driver->tx_tail = 0;
    driver->tx_count = 0;
    
    // Clear the TX active flag
    driver->status_flags &= ~UART_STATUS_TX_ACTIVE;
}

void custom_uart_flush_rx(CustomUARTDriver* driver) {
    if (driver == NULL) {
        return;
    }
    
    // Reset the RX buffer
    driver->rx_head = 0;
    driver->rx_tail = 0;
    driver->rx_count = 0;
    
    // Clear the RX active flag
    driver->status_flags &= ~UART_STATUS_RX_ACTIVE;
}

uint32_t custom_uart_get_status(CustomUARTDriver* driver) {
    if (driver == NULL) {
        return 0;
    }
    
    return driver->status_flags;
}

uint32_t custom_uart_get_errors(CustomUARTDriver* driver) {
    if (driver == NULL) {
        return 0;
    }
    
    // Get the current error flags
    uint32_t errors = driver->error_flags;
    
    // Clear the error flags
    driver->error_flags = 0;
    
    return errors;
}

void custom_uart_deinit(CustomUARTDriver* driver) {
    if (driver == NULL) {
        return;
    }
    
    // Stop recording if enabled
    if (driver->record_enabled) {
        custom_uart_stop_recording(driver);
    }
    
    // Clean up allocated memory
    if (driver->record_filename != NULL) {
        free(driver->record_filename);
        driver->record_filename = NULL;
    }
    
    // Free the driver structure
    free(driver);
}

/* Internal helper functions */

static bool uart_tx_buffer_full(CustomUARTDriver* driver) {
    return driver->tx_count >= UART_TX_BUFFER_SIZE;
}

static bool uart_rx_buffer_full(CustomUARTDriver* driver) {
    return driver->rx_count >= UART_RX_BUFFER_SIZE;
}

static bool uart_tx_buffer_empty(CustomUARTDriver* driver) {
    return driver->tx_count == 0;
}

static bool uart_rx_buffer_empty(CustomUARTDriver* driver) {
    return driver->rx_count == 0;
}

static void uart_update_byte_time(CustomUARTDriver* driver) {
    // Calculate the time to transmit one byte in microseconds
    // Formula: (1 start bit + data bits + parity bit + stop bits) * 1000000 / baudrate
    uint8_t total_bits = 1 + driver->data_bits + (driver->parity != CUSTOM_UART_PARITY_NONE ? 1 : 0) + driver->stop_bits;
    driver->byte_transmit_time_us = (uint32_t)((total_bits * 1000000.0) / driver->baudrate);
}

static void uart_simulate_timing(CustomUARTDriver* driver, uint32_t bytes_count) {
    // Get the current time
    uint32_t current_time = (uint32_t)time(NULL);
    
    // Calculate the time needed to transmit the bytes
    uint32_t transmit_time_us = driver->byte_transmit_time_us * bytes_count;
    
    // Simulate timing by sleeping
    // In a real implementation, we would use a more precise timing mechanism
    // but for simulation purposes, this is sufficient
    struct timespec ts;
    ts.tv_sec = transmit_time_us / 1000000;
    ts.tv_nsec = (transmit_time_us % 1000000) * 1000;
    
    // Uncomment this line to actually sleep for the transmit time
    // nanosleep(&ts, NULL);
    
    // Update the last transmission time
    driver->last_tx_time = current_time;
}

static void uart_record_data(CustomUARTDriver* driver, const uint8_t* data, size_t size, bool is_tx) {
    if (driver == NULL || data == NULL || size == 0 || driver->record_file == NULL) {
        return;
    }
    
    // Record format: [timestamp (4 bytes)] [direction (1 byte)] [size (2 bytes)] [data (size bytes)]
    uint32_t timestamp = (uint32_t)time(NULL);
    uint8_t direction = is_tx ? 0x01 : 0x02;
    uint16_t data_size = (uint16_t)size;
    
    // Write the header
    fwrite(&timestamp, sizeof(timestamp), 1, driver->record_file);
    fwrite(&direction, sizeof(direction), 1, driver->record_file);
    fwrite(&data_size, sizeof(data_size), 1, driver->record_file);
    
    // Write the data
    fwrite(data, 1, size, driver->record_file);
    
    // Flush the file to ensure the data is written
    fflush(driver->record_file);
}

size_t custom_uart_transfer(CustomUARTDriver* source, CustomUARTDriver* destination) {
    if (!source || !destination) {
        return 0;
    }
    
    size_t transferred = 0;
    uint8_t byte;
    
    while (source->tx_count > 0) {
        // Get the byte from the source TX buffer
        byte = source->tx_buffer[source->tx_tail];
        source->tx_tail = (source->tx_tail + 1) % UART_TX_BUFFER_SIZE;
        source->tx_count--;
        
        // Directly receive it on the destination
        if (custom_uart_receive_byte(destination, byte)) {
            transferred++;
        }
    }
    
    return transferred;
} 