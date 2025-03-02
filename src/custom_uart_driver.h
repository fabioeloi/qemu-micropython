/*
 * Custom UART Driver for QEMU-MicroPython Integration - Header
 *
 * This header file defines the interface for the custom UART driver that extends
 * the STM32F2XX USART functionality with enhanced debugging and testing capabilities.
 */

#ifndef CUSTOM_UART_DRIVER_H
#define CUSTOM_UART_DRIVER_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>

/* Maximum number of UART instances supported */
#define MAX_UART_INSTANCES 10

/* Buffer sizes */
#define UART_TX_BUFFER_SIZE 1024
#define UART_RX_BUFFER_SIZE 1024

/* Parity options - use custom names to avoid conflicts with STM32 HAL */
#define CUSTOM_UART_PARITY_NONE  0
#define CUSTOM_UART_PARITY_ODD   1
#define CUSTOM_UART_PARITY_EVEN  2

/* Error flags returned by custom_uart_get_errors() */
#define UART_ERROR_OVERFLOW      (1 << 0)  /* Buffer overflow */
#define UART_ERROR_UNDERFLOW     (1 << 1)  /* Buffer underflow */
#define UART_ERROR_FRAMING       (1 << 2)  /* Framing error */
#define UART_ERROR_PARITY        (1 << 3)  /* Parity error */
#define UART_ERROR_NOISE         (1 << 4)  /* Noise detected */
#define UART_ERROR_BREAK         (1 << 5)  /* Break condition */

/* Status flags returned by custom_uart_get_status() */
#define UART_STATUS_OVERFLOW     (1 << 0)  /* Buffer overflow occurred */
#define UART_STATUS_UNDERFLOW    (1 << 1)  /* Buffer underflow occurred */
#define UART_STATUS_LOOPBACK     (1 << 2)  /* Loopback mode active */
#define UART_STATUS_RECORDING    (1 << 3)  /* Recording active */
#define UART_STATUS_NOISE_SIM    (1 << 4)  /* Noise simulation active */
#define UART_STATUS_TIMING_SIM   (1 << 5)  /* Timing simulation active */
#define UART_STATUS_DEBUG_MODE   (1 << 6)  /* Debug callbacks active */
#define UART_STATUS_TX_ACTIVE    (1 << 7)  /* Transmitter active */
#define UART_STATUS_RX_ACTIVE    (1 << 8)  /* Receiver active */

/* Custom UART state */
typedef enum {
    UART_STATE_IDLE,
    UART_STATE_TRANSMITTING,
    UART_STATE_RECEIVING,
    UART_STATE_ERROR
} uart_state_t;

/* Custom UART driver structure */
typedef struct CustomUARTDriver {
    /* Base configuration */
    uint32_t uart_id;
    uint32_t baudrate;
    uint8_t data_bits;
    uint8_t stop_bits;
    uint8_t parity;
    bool flow_control;
    
    /* Internal state */
    uart_state_t state;
    uint32_t status_flags;
    uint32_t error_flags;
    
    /* Buffers */
    uint8_t tx_buffer[UART_TX_BUFFER_SIZE];
    uint16_t tx_head;
    uint16_t tx_tail;
    uint16_t tx_count;
    
    uint8_t rx_buffer[UART_RX_BUFFER_SIZE];
    uint16_t rx_head;
    uint16_t rx_tail;
    uint16_t rx_count;
    
    /* Timing simulation */
    uint32_t last_tx_time;
    uint32_t last_rx_time;
    uint32_t byte_transmit_time_us; // Time to transmit one byte in microseconds
    
    /* Enhanced features */
    bool loopback_enabled;
    bool record_enabled;
    char* record_filename;
    FILE* record_file;
    
    /* Noise and error simulation */
    float error_rate;
    float noise_level;
    bool simulate_timing;

    /* Debug callbacks */
    void (*debug_tx_callback)(uint8_t byte, void* user_data);
    void (*debug_rx_callback)(uint8_t byte, void* user_data);
    void* debug_user_data;
    
    /* Integration with QEMU */
    void* qemu_char_driver;
    void* qemu_irq_handler;
} CustomUARTDriver;

/*
 * Initialize a new UART driver instance
 *
 * uart_id: The UART ID (0-based, maps to UART1, UART2, etc.)
 * baudrate: Initial baudrate
 *
 * Returns: Pointer to the driver instance, or NULL on failure
 */
CustomUARTDriver* custom_uart_init(uint32_t uart_id, uint32_t baudrate);

/*
 * Configure the UART parameters
 *
 * driver: The UART driver instance
 * data_bits: Number of data bits (5-9)
 * stop_bits: Number of stop bits (1-2)
 * parity: Parity mode (CUSTOM_UART_PARITY_NONE, CUSTOM_UART_PARITY_ODD, CUSTOM_UART_PARITY_EVEN)
 * flow_control: Whether to use hardware flow control
 *
 * Returns: true on success, false on failure
 */
bool custom_uart_configure(CustomUARTDriver* driver, uint8_t data_bits, 
                          uint8_t stop_bits, uint8_t parity, bool flow_control);

/*
 * Set the baudrate
 *
 * driver: The UART driver instance
 * baudrate: The new baudrate
 *
 * Returns: true on success, false on failure
 */
bool custom_uart_set_baudrate(CustomUARTDriver* driver, uint32_t baudrate);

/*
 * Enable or disable loopback mode
 *
 * driver: The UART driver instance
 * enable: Whether to enable loopback mode
 */
void custom_uart_set_loopback(CustomUARTDriver* driver, bool enable);

/*
 * Start recording UART traffic to a file
 *
 * driver: The UART driver instance
 * filename: The path to the recording file
 *
 * Returns: true on success, false on failure
 */
bool custom_uart_start_recording(CustomUARTDriver* driver, const char* filename);

/*
 * Stop recording UART traffic
 *
 * driver: The UART driver instance
 */
void custom_uart_stop_recording(CustomUARTDriver* driver);

/*
 * Configure error simulation
 *
 * driver: The UART driver instance
 * error_rate: The probability of errors (0.0 - 1.0)
 */
void custom_uart_set_error_simulation(CustomUARTDriver* driver, float error_rate);

/*
 * Configure noise simulation
 *
 * driver: The UART driver instance
 * noise_level: The probability of bit flips (0.0 - 1.0)
 */
void custom_uart_set_noise_simulation(CustomUARTDriver* driver, float noise_level);

/*
 * Enable or disable timing simulation
 *
 * driver: The UART driver instance
 * enable: Whether to enable timing simulation
 */
void custom_uart_set_timing_simulation(CustomUARTDriver* driver, bool enable);

/*
 * Register debug callbacks for TX and RX operations
 *
 * driver: The UART driver instance
 * tx_callback: Function called when a byte is transmitted
 * rx_callback: Function called when a byte is received
 * user_data: User data passed to the callbacks
 */
void custom_uart_set_debug_callbacks(CustomUARTDriver* driver, 
                                    void (*tx_callback)(uint8_t byte, void* user_data),
                                    void (*rx_callback)(uint8_t byte, void* user_data),
                                    void* user_data);

/*
 * Send a byte over UART
 *
 * driver: The UART driver instance
 * byte: The byte to send
 *
 * Returns: true on success, false on failure
 */
bool custom_uart_send_byte(CustomUARTDriver* driver, uint8_t byte);

/*
 * Send multiple bytes over UART
 *
 * driver: The UART driver instance
 * data: The data to send
 * length: The number of bytes to send
 *
 * Returns: The number of bytes sent
 */
size_t custom_uart_send_data(CustomUARTDriver* driver, const uint8_t* data, size_t length);

/*
 * Receive a byte from UART (called by QEMU or loopback)
 *
 * driver: The UART driver instance
 * byte: The received byte
 *
 * Returns: true on success, false on failure
 */
bool custom_uart_receive_byte(CustomUARTDriver* driver, uint8_t byte);

/*
 * Read a byte from the UART RX buffer
 *
 * driver: The UART driver instance
 * byte: Pointer to store the read byte
 *
 * Returns: true on success, false on failure
 */
bool custom_uart_read_byte(CustomUARTDriver* driver, uint8_t* byte);

/*
 * Read multiple bytes from the UART RX buffer
 *
 * driver: The UART driver instance
 * buffer: Buffer to store the read bytes
 * max_length: Maximum number of bytes to read
 *
 * Returns: The number of bytes read
 */
size_t custom_uart_read_data(CustomUARTDriver* driver, uint8_t* buffer, size_t max_length);

/*
 * Check if there are bytes available to read
 *
 * driver: The UART driver instance
 *
 * Returns: The number of bytes available
 */
size_t custom_uart_available(CustomUARTDriver* driver);

/*
 * Flush the TX buffer
 *
 * driver: The UART driver instance
 */
void custom_uart_flush_tx(CustomUARTDriver* driver);

/*
 * Flush the RX buffer
 *
 * driver: The UART driver instance
 */
void custom_uart_flush_rx(CustomUARTDriver* driver);

/*
 * Get the driver status flags
 *
 * driver: The UART driver instance
 *
 * Returns: The status flags (see UART_STATUS_* defines)
 */
uint32_t custom_uart_get_status(CustomUARTDriver* driver);

/*
 * Get the driver error flags and clear them
 *
 * driver: The UART driver instance
 *
 * Returns: The error flags (see UART_ERROR_* defines)
 */
uint32_t custom_uart_get_errors(CustomUARTDriver* driver);

/*
 * Clean up and release resources
 *
 * driver: The UART driver instance
 */
void custom_uart_deinit(CustomUARTDriver* driver);

/**
 * Transfer data from one UART to another
 * 
 * This function simulates a physical connection between two UART devices
 * by reading data from the source device and directly receiving it on the
 * destination device.
 * 
 * @param source The source UART driver
 * @param destination The destination UART driver
 * @return Number of bytes transferred
 */
size_t custom_uart_transfer(CustomUARTDriver* source, CustomUARTDriver* destination);

#endif /* CUSTOM_UART_DRIVER_H */ 