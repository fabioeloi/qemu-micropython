#!/bin/bash
# Test simulated network communication using the custom UART
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC_DIR="$PROJECT_DIR/src"

echo "Testing simulated network communication..."

# Create a test program that simulates two devices communicating
cat > "$SRC_DIR/network_sim_test.c" << EOF
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "custom_uart_driver.h"

// Protocol implementation
typedef struct {
    uint8_t start_byte;
    uint8_t length;
    uint8_t command;
    uint8_t data[32];
    uint8_t checksum;
} Protocol_Packet;

// Calculate simple checksum
uint8_t calculate_checksum(Protocol_Packet* packet) {
    uint8_t sum = packet->start_byte + packet->length + packet->command;
    for (int i = 0; i < packet->length; i++) {
        sum += packet->data[i];
    }
    return ~sum; // Invert for checksum
}

// Send packet
bool send_packet(CustomUARTDriver* uart, uint8_t command, uint8_t* data, uint8_t length) {
    Protocol_Packet packet;
    packet.start_byte = 0xAA;
    packet.length = length;
    packet.command = command;
    memcpy(packet.data, data, length);
    packet.checksum = calculate_checksum(&packet);
    
    printf("Sending packet: start=0x%02X, len=%d, cmd=0x%02X, checksum=0x%02X\n", 
           packet.start_byte, packet.length, packet.command, packet.checksum);
    
    // Send header
    if (!custom_uart_send_byte(uart, packet.start_byte)) {
        printf("Failed to send start byte\n");
        return false;
    }
    
    if (!custom_uart_send_byte(uart, packet.length)) {
        printf("Failed to send length\n");
        return false;
    }
    
    if (!custom_uart_send_byte(uart, packet.command)) {
        printf("Failed to send command\n");
        return false;
    }
    
    // Send data
    for (int i = 0; i < packet.length; i++) {
        if (!custom_uart_send_byte(uart, packet.data[i])) {
            printf("Failed to send data byte %d\n", i);
            return false;
        }
    }
    
    // Send checksum
    if (!custom_uart_send_byte(uart, packet.checksum)) {
        printf("Failed to send checksum\n");
        return false;
    }
    
    return true;
}

// Receive packet
bool receive_packet(CustomUARTDriver* uart, Protocol_Packet* packet) {
    // Wait for start byte
    uint8_t byte;
    int timeout = 100; // Timeout after 100 attempts
    
    printf("Waiting for start byte (available: %zu bytes)...\n", 
           custom_uart_available(uart));
    
    while (timeout > 0) {
        if (custom_uart_available(uart) > 0) {
            if (custom_uart_read_byte(uart, &byte)) {
                if (byte == 0xAA) {
                    packet->start_byte = byte;
                    break;
                }
            }
        }
        usleep(1000); // Sleep 1ms
        timeout--;
    }
    
    if (timeout == 0) {
        printf("Timeout waiting for start byte\n");
        return false; // Timeout
    }
    
    // Read length
    if (!custom_uart_read_byte(uart, &packet->length)) {
        printf("Failed to read length\n");
        return false;
    }
    
    // Read command
    if (!custom_uart_read_byte(uart, &packet->command)) {
        printf("Failed to read command\n");
        return false;
    }
    
    // Read data
    for (int i = 0; i < packet->length; i++) {
        if (!custom_uart_read_byte(uart, &packet->data[i])) {
            printf("Failed to read data byte %d\n", i);
            return false;
        }
    }
    
    // Read checksum
    uint8_t received_checksum;
    if (!custom_uart_read_byte(uart, &received_checksum)) {
        printf("Failed to read checksum\n");
        return false;
    }
    
    // Verify checksum
    uint8_t calculated_checksum = calculate_checksum(packet);
    
    if (calculated_checksum != received_checksum) {
        printf("Checksum verification failed\n");
        return false;
    }
    
    printf("Packet received: start=0x%02X, len=%d, cmd=0x%02X\n", 
           packet->start_byte, packet->length, packet->command);
    
    return true;
}

int main() {
    printf("Network Simulation Test\n");
    printf("=======================\n\n");
    
    // Initialize two UART devices (simulating two devices)
    CustomUARTDriver* device1 = custom_uart_init(1, 115200);
    CustomUARTDriver* device2 = custom_uart_init(2, 115200);
    
    if (!device1 || !device2) {
        printf("Failed to initialize UART devices\n");
        return 1;
    }
    
    // Configure both devices
    custom_uart_configure(device1, 8, 1, CUSTOM_UART_PARITY_NONE, false);
    custom_uart_configure(device2, 8, 1, CUSTOM_UART_PARITY_NONE, false);
    
    // Disable debug callbacks for cleaner output
    custom_uart_set_debug_callbacks(device1, NULL, NULL, NULL);
    custom_uart_set_debug_callbacks(device2, NULL, NULL, NULL);
    
    // Ensure loopback is disabled
    custom_uart_set_loopback(device1, false);
    custom_uart_set_loopback(device2, false);
    
    // Initialize thread-like alternating execution
    int successful_transfers = 0;
    int failed_transfers = 0;
    
    // Test various network conditions
    struct {
        float error_rate;
        float noise_level;
        int packets_to_send;
        char* description;
    } test_scenarios[] = {
        {0.0, 0.0, 10, "Perfect conditions"},
        {0.0, 0.05, 10, "5% bit noise"},
        {0.1, 0.0, 10, "10% packet loss"},
        {0.05, 0.05, 10, "Combined 5% errors, 5% noise"},
        {0.3, 0.1, 10, "Harsh conditions: 30% errors, 10% noise"}
    };
    
    // Run through test scenarios
    for (int scenario = 0; scenario < 5; scenario++) {
        float error_rate = test_scenarios[scenario].error_rate;
        float noise_level = test_scenarios[scenario].noise_level;
        int packets_to_send = test_scenarios[scenario].packets_to_send;
        
        printf("\nScenario: %s\n", test_scenarios[scenario].description);
        printf("Error rate: %.2f, Noise level: %.2f\n", error_rate, noise_level);
        
        // Configure network conditions
        custom_uart_set_error_simulation(device1, error_rate);
        custom_uart_set_noise_simulation(device1, noise_level);
        
        // Reset statistics
        successful_transfers = 0;
        failed_transfers = 0;
        
        // Start test
        for (int i = 0; i < packets_to_send; i++) {
            printf("Packet %d: ", i+1);
            
            // Create test packet
            uint8_t test_data[8] = {i, i+1, i+2, i+3, i+4, i+5, i+6, i+7};
            
            // Device 1 sends to Device 2
            if (send_packet(device1, 0x10, test_data, 8)) {
                // Transfer the data from device1 to device2
                size_t transferred = custom_uart_transfer(device1, device2);
                printf("Transferred %zu bytes from device1 to device2\n", transferred);
                
                // Wait a bit for processing
                usleep(10000);
                
                // Device 2 tries to receive
                Protocol_Packet received;
                if (receive_packet(device2, &received)) {
                    if (received.command == 0x10 && received.length == 8) {
                        // Verify data
                        bool data_ok = true;
                        for (int j = 0; j < 8; j++) {
                            if (received.data[j] != test_data[j]) {
                                data_ok = false;
                                break;
                            }
                        }
                        
                        if (data_ok) {
                            printf("SUCCESS - Data verified\n");
                            successful_transfers++;
                        } else {
                            printf("FAILED - Data corrupted\n");
                            failed_transfers++;
                        }
                    } else {
                        printf("FAILED - Wrong command or length\n");
                        failed_transfers++;
                    }
                } else {
                    printf("FAILED - Receive failed\n");
                    failed_transfers++;
                }
            } else {
                printf("FAILED - Send failed\n");
                failed_transfers++;
            }
            
            // Give some time between packets
            usleep(20000);
        }
        
        // Print statistics
        float success_rate = (float)successful_transfers / (float)(successful_transfers + failed_transfers) * 100.0f;
        printf("\nResults: %d/%d successful (%.1f%%)\n", 
               successful_transfers, (successful_transfers + failed_transfers), success_rate);
    }
    
    // Clean up
    custom_uart_deinit(device1);
    custom_uart_deinit(device2);
    
    printf("\nNetwork simulation test completed\n");
    return 0;
}
EOF

# Compile the test
gcc -I"$SRC_DIR" -g -Wall -o "$PROJECT_DIR/build/network_sim_test" \
    "$SRC_DIR/custom_uart_driver.c" "$SRC_DIR/network_sim_test.c" -lm

# Run the test
"$PROJECT_DIR/build/network_sim_test"

echo "Network simulation test completed" 