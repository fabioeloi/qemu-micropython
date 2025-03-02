/*
 * QEMU UART Bridge for Custom UART Driver
 *
 * This file provides integration between the custom UART driver
 * and QEMU's character device API.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#include "custom_uart_driver.h"

// These would be defined by QEMU in a real implementation
typedef struct CharDriverState CharDriverState;
typedef struct QEMUTimer QEMUTimer;

// Dummy definitions for testing/demo purposes
typedef void (*qemu_chr_write_cb)(void* opaque, const uint8_t* buf, int size);
typedef int (*qemu_chr_can_receive_cb)(void* opaque);
typedef void (*qemu_chr_receive_cb)(void* opaque, const uint8_t* buf, int size);
typedef void (*qemu_chr_event_cb)(void* opaque, int event);

typedef struct {
    // The custom UART driver instance
    CustomUARTDriver* uart_driver;
    
    // QEMU character device state
    CharDriverState* chr;
    
    // QEMU timer for simulating UART timing
    QEMUTimer* timer;
    
    // Callback for when QEMU sends data to the UART
    qemu_chr_receive_cb receive_cb;
    
    // Opaque pointer for callbacks
    void* opaque;
    
    // Internal state
    bool initialized;
    bool is_open;
} QEMUUARTBridge;

// Global array of UART bridges
#define MAX_UART_BRIDGES 10
static QEMUUARTBridge uart_bridges[MAX_UART_BRIDGES];
static int num_uart_bridges = 0;

// Forward declarations of QEMU callback handlers
static int qemu_uart_can_receive(void* opaque);
static void qemu_uart_receive(void* opaque, const uint8_t* buf, int size);
static void qemu_uart_event(void* opaque, int event);
static void qemu_uart_timer_cb(void* opaque);

//-----------------------------------------------------------------------
// Debug callbacks to connect with QEMU
//-----------------------------------------------------------------------
static void uart_tx_debug_cb(uint8_t byte, void* user_data) {
    QEMUUARTBridge* bridge = (QEMUUARTBridge*)user_data;
    
    // When the UART transmits a byte, forward it to QEMU
    if (bridge && bridge->chr) {
        // In a real implementation, this would call a QEMU function to send data
        // For example: qemu_chr_fe_write(bridge->chr, &byte, 1);
        printf("QEMU UART Bridge: TX 0x%02X\n", byte);
    }
}

static void uart_rx_debug_cb(uint8_t byte, void* user_data) {
    QEMUUARTBridge* bridge = (QEMUUARTBridge*)user_data;
    
    // This is called when the UART receives a byte (for debugging)
    if (bridge) {
        printf("QEMU UART Bridge: RX 0x%02X\n", byte);
    }
}

//-----------------------------------------------------------------------
// QEMU callback implementations
//-----------------------------------------------------------------------
static int qemu_uart_can_receive(void* opaque) {
    QEMUUARTBridge* bridge = (QEMUUARTBridge*)opaque;
    
    if (!bridge || !bridge->uart_driver || !bridge->is_open) {
        return 0;
    }
    
    // Check if the UART can receive data (not full)
    size_t available_space = UART_RX_BUFFER_SIZE - custom_uart_available(bridge->uart_driver);
    return available_space > 0 ? available_space : 0;
}

static void qemu_uart_receive(void* opaque, const uint8_t* buf, int size) {
    QEMUUARTBridge* bridge = (QEMUUARTBridge*)opaque;
    
    if (!bridge || !bridge->uart_driver || !bridge->is_open || size <= 0) {
        return;
    }
    
    // Forward data from QEMU to the UART driver
    for (int i = 0; i < size; i++) {
        custom_uart_receive_byte(bridge->uart_driver, buf[i]);
    }
}

static void qemu_uart_event(void* opaque, int event) {
    QEMUUARTBridge* bridge = (QEMUUARTBridge*)opaque;
    
    if (!bridge) {
        return;
    }
    
    // Handle QEMU character device events
    // For example, open, close, break condition, etc.
    switch (event) {
        case 0: // CHR_EVENT_OPENED in QEMU
            bridge->is_open = true;
            printf("QEMU UART Bridge: Connection opened\n");
            break;
            
        case 1: // CHR_EVENT_CLOSED in QEMU
            bridge->is_open = false;
            printf("QEMU UART Bridge: Connection closed\n");
            break;
            
        default:
            printf("QEMU UART Bridge: Unknown event %d\n", event);
            break;
    }
}

static void qemu_uart_timer_cb(void* opaque) {
    QEMUUARTBridge* bridge = (QEMUUARTBridge*)opaque;
    
    if (!bridge || !bridge->uart_driver) {
        return;
    }
    
    // This would be called periodically to handle UART timing simulation
    // In a real implementation, it would check for data to send, handle
    // timing delays, etc.
    
    // Example of reading from the UART and forwarding to QEMU:
    uint8_t byte;
    while (custom_uart_read_byte(bridge->uart_driver, &byte)) {
        // In a real implementation: qemu_chr_fe_write(bridge->chr, &byte, 1);
        printf("QEMU UART Bridge Timer: Forwarding byte 0x%02X\n", byte);
    }
    
    // Re-arm the timer
    // In a real implementation: timer_mod(bridge->timer, qemu_clock_get_ns(QEMU_CLOCK_VIRTUAL) + UART_TIMER_NS);
}

//-----------------------------------------------------------------------
// Public API for QEMU integration
//-----------------------------------------------------------------------

/*
 * Initialize a new UART bridge for QEMU
 *
 * uart_id: The UART ID to use
 * baudrate: The initial baudrate
 * chr: QEMU character device state
 * 
 * Returns: Bridge ID on success, -1 on failure
 */
int qemu_uart_bridge_init(uint32_t uart_id, uint32_t baudrate, CharDriverState* chr) {
    if (num_uart_bridges >= MAX_UART_BRIDGES) {
        fprintf(stderr, "QEMU UART Bridge: Maximum number of bridges reached\n");
        return -1;
    }
    
    int bridge_id = num_uart_bridges++;
    QEMUUARTBridge* bridge = &uart_bridges[bridge_id];
    memset(bridge, 0, sizeof(QEMUUARTBridge));
    
    // Initialize the custom UART driver
    bridge->uart_driver = custom_uart_init(uart_id, baudrate);
    if (!bridge->uart_driver) {
        fprintf(stderr, "QEMU UART Bridge: Failed to initialize UART driver\n");
        num_uart_bridges--;
        return -1;
    }
    
    // Set up debug callbacks
    custom_uart_set_debug_callbacks(bridge->uart_driver, uart_tx_debug_cb, uart_rx_debug_cb, bridge);
    
    // Store the QEMU character device
    bridge->chr = chr;
    
    // In a real implementation, set up the QEMU timer:
    // bridge->timer = timer_new_ns(QEMU_CLOCK_VIRTUAL, qemu_uart_timer_cb, bridge);
    // timer_mod(bridge->timer, qemu_clock_get_ns(QEMU_CLOCK_VIRTUAL) + UART_TIMER_NS);
    
    // Set up QEMU callbacks
    // In a real implementation:
    // qemu_chr_add_handlers(chr, qemu_uart_can_receive, qemu_uart_receive, qemu_uart_event, bridge);
    
    bridge->initialized = true;
    printf("QEMU UART Bridge: Initialized bridge %d for UART%d at %d baud\n", 
           bridge_id, uart_id, baudrate);
    
    return bridge_id;
}

/*
 * Get the custom UART driver for a bridge
 */
CustomUARTDriver* qemu_uart_bridge_get_driver(int bridge_id) {
    if (bridge_id < 0 || bridge_id >= num_uart_bridges || 
        !uart_bridges[bridge_id].initialized) {
        return NULL;
    }
    
    return uart_bridges[bridge_id].uart_driver;
}

/*
 * Clean up a UART bridge
 */
void qemu_uart_bridge_deinit(int bridge_id) {
    if (bridge_id < 0 || bridge_id >= num_uart_bridges || 
        !uart_bridges[bridge_id].initialized) {
        return;
    }
    
    QEMUUARTBridge* bridge = &uart_bridges[bridge_id];
    
    // Cancel the timer if it exists
    // In a real implementation: timer_del(bridge->timer);
    
    // Clean up the UART driver
    if (bridge->uart_driver) {
        custom_uart_deinit(bridge->uart_driver);
        bridge->uart_driver = NULL;
    }
    
    bridge->initialized = false;
    printf("QEMU UART Bridge: Deinitialized bridge %d\n", bridge_id);
} 