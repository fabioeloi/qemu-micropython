#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "custom_uart_driver.h"

// Debug callback for device 1
static void debug_tx1(uint8_t byte, void* user_data) {
    printf("DEV1 TX: 0x%02X (%c)\n", byte, byte >= 32 && byte < 127 ? byte : '.');
}

static void debug_rx1(uint8_t byte, void* user_data) {
    printf("DEV1 RX: 0x%02X (%c)\n", byte, byte >= 32 && byte < 127 ? byte : '.');
}

// Debug callback for device 2
static void debug_tx2(uint8_t byte, void* user_data) {
    printf("DEV2 TX: 0x%02X (%c)\n", byte, byte >= 32 && byte < 127 ? byte : '.');
}

static void debug_rx2(uint8_t byte, void* user_data) {
    printf("DEV2 RX: 0x%02X (%c)\n", byte, byte >= 32 && byte < 127 ? byte : '.');
}

int main() {
    printf("UART Bridge Test\n");
    printf("================\n\n");
    
    // Initialize two UART devices
    CustomUARTDriver* device1 = custom_uart_init(1, 115200);
    CustomUARTDriver* device2 = custom_uart_init(2, 115200);
    
    if (!device1 || !device2) {
        printf("Failed to initialize UART devices\n");
        return 1;
    }
    
    // Configure both devices
    custom_uart_configure(device1, 8, 1, CUSTOM_UART_PARITY_NONE, false);
    custom_uart_configure(device2, 8, 1, CUSTOM_UART_PARITY_NONE, false);
    
    // Register debug callbacks
    custom_uart_set_debug_callbacks(device1, debug_tx1, debug_rx1, NULL);
    custom_uart_set_debug_callbacks(device2, debug_tx2, debug_rx2, NULL);
    
    // Ensure loopback is disabled
    custom_uart_set_loopback(device1, false);
    custom_uart_set_loopback(device2, false);
    
    printf("Sending data from device 1 to device 2...\n");
    
    // Send test message from device 1
    const char* message = "Hello, Bridge!";
    size_t message_len = strlen(message);
    
    // Send byte by byte
    for (size_t i = 0; i < message_len; i++) {
        custom_uart_send_byte(device1, message[i]);
    }
    
    printf("\nTesting transfer from device 1 to device 2...\n");
    printf("Bytes in device 1 TX buffer: %zu\n", custom_uart_available(device1));
    printf("Bytes in device 2 RX buffer before transfer: %zu\n", custom_uart_available(device2));
    
    // Use the new transfer function
    size_t transferred = custom_uart_transfer(device1, device2);
    
    printf("Transferred %zu bytes\n", transferred);
    printf("Bytes in device 1 TX buffer after transfer: %zu\n", custom_uart_available(device1));
    printf("Bytes in device 2 RX buffer after transfer: %zu\n", custom_uart_available(device2));
    
    // Test bidirectional communication
    printf("\nTesting bidirectional communication...\n");
    
    // Send reply from device 2 to device 1
    const char* reply = "Bridge works!";
    size_t reply_len = strlen(reply);
    
    // Send byte by byte
    for (size_t i = 0; i < reply_len; i++) {
        custom_uart_send_byte(device2, reply[i]);
    }
    
    // Transfer from device 2 to device 1
    transferred = custom_uart_transfer(device2, device1);
    
    printf("Transferred %zu bytes from device 2 to device 1\n", transferred);
    
    // Read data from both devices
    char buffer1[100] = {0};
    char buffer2[100] = {0};
    size_t len1 = 0;
    size_t len2 = 0;
    
    uint8_t byte;
    while (custom_uart_available(device1) > 0 && len1 < sizeof(buffer1) - 1) {
        if (custom_uart_read_byte(device1, &byte)) {
            buffer1[len1++] = byte;
        }
    }
    
    while (custom_uart_available(device2) > 0 && len2 < sizeof(buffer2) - 1) {
        if (custom_uart_read_byte(device2, &byte)) {
            buffer2[len2++] = byte;
        }
    }
    
    printf("Device 1 received: '%s'\n", buffer1);
    printf("Device 2 received: '%s'\n", buffer2);
    
    if (strcmp(reply, buffer1) == 0 && strcmp(message, buffer2) == 0) {
        printf("\nBridge test SUCCESSFUL! Bidirectional communication works.\n");
    } else {
        printf("\nBridge test FAILED!\n");
    }
    
    // Clean up
    custom_uart_deinit(device1);
    custom_uart_deinit(device2);
    
    return 0;
} 