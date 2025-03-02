#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include "custom_uart_driver.h"

#define TEST_DATA_SIZE 8192
#define TRANSFER_SIZE 64
#define NUM_ITERATIONS 50

// Create random data buffer
void fill_random(uint8_t* buffer, size_t size) {
    for (size_t i = 0; i < size; i++) {
        buffer[i] = rand() % 256;
    }
}

// Test rapid transmission
void test_rapid_transmission(CustomUARTDriver* uart) {
    printf("Testing rapid transmission...\n");
    
    uint8_t test_data[TEST_DATA_SIZE];
    fill_random(test_data, TEST_DATA_SIZE);
    
    // Enable loopback
    custom_uart_set_loopback(uart, true);
    
    clock_t start = clock();
    
    size_t total_sent = 0;
    size_t total_received = 0;
    
    for (int i = 0; i < NUM_ITERATIONS; i++) {
        size_t sent = 0;
        while (sent < TEST_DATA_SIZE) {
            size_t to_send = (TEST_DATA_SIZE - sent < TRANSFER_SIZE) ? TEST_DATA_SIZE - sent : TRANSFER_SIZE;
            size_t bytes_sent = custom_uart_send_data(uart, test_data + sent, to_send);
            if (bytes_sent == 0) {
                usleep(1000); // Give some time if buffer is full
                continue;
            }
            sent += bytes_sent;
            total_sent += bytes_sent;
        }
        
        // Read back data
        uint8_t receive_buffer[TEST_DATA_SIZE];
        size_t received = 0;
        
        while (received < TEST_DATA_SIZE) {
            size_t bytes_available = custom_uart_available(uart);
            if (bytes_available == 0) {
                usleep(1000); // Wait for data
                continue;
            }
            
            size_t to_read = (TEST_DATA_SIZE - received < bytes_available) ? TEST_DATA_SIZE - received : bytes_available;
            size_t bytes_read = custom_uart_read_data(uart, receive_buffer + received, to_read);
            received += bytes_read;
            total_received += bytes_read;
        }
        
        // Verify data
        if (memcmp(test_data, receive_buffer, TEST_DATA_SIZE) != 0) {
            printf("ERROR: Data verification failed on iteration %d\n", i);
        }
        
        // Progress indicator
        printf(".");
        fflush(stdout);
    }
    
    clock_t end = clock();
    double elapsed = (double)(end - start) / CLOCKS_PER_SEC;
    
    printf("\nRapid transmission test results:\n");
    printf("Total bytes sent: %zu\n", total_sent);
    printf("Total bytes received: %zu\n", total_received);
    printf("Time elapsed: %.2f seconds\n", elapsed);
    printf("Transfer rate: %.2f KB/s\n\n", (total_sent / 1024.0) / elapsed);
}

// Test buffer edge conditions
void test_buffer_edges(CustomUARTDriver* uart) {
    printf("Testing buffer edge conditions...\n");
    
    // Reset the UART
    custom_uart_flush_tx(uart);
    custom_uart_flush_rx(uart);
    
    // Enable loopback
    custom_uart_set_loopback(uart, true);
    
    // Get buffer sizes from the driver header
    #define UART_TX_BUFFER_SIZE 1024
    #define UART_RX_BUFFER_SIZE 1024
    
    // Create data that's exactly buffer size
    uint8_t* test_data = (uint8_t*)malloc(UART_TX_BUFFER_SIZE);
    fill_random(test_data, UART_TX_BUFFER_SIZE);
    
    printf("Testing exact buffer size transmission...\n");
    
    // Try to fill the buffer exactly
    size_t sent = custom_uart_send_data(uart, test_data, UART_TX_BUFFER_SIZE - 1); // -1 for buffer tracking
    printf("Sent %zu bytes of %d requested\n", sent, UART_TX_BUFFER_SIZE - 1);
    
    // Read it back
    uint8_t* receive_buffer = (uint8_t*)malloc(UART_TX_BUFFER_SIZE);
    usleep(100000); // Wait for loopback to process
    
    size_t received = custom_uart_read_data(uart, receive_buffer, UART_TX_BUFFER_SIZE);
    printf("Received %zu bytes\n", received);
    
    // Verify data
    if (sent == received && memcmp(test_data, receive_buffer, sent) == 0) {
        printf("Data verification successful\n");
    } else {
        printf("Data verification failed\n");
    }
    
    // Clean up
    free(test_data);
    free(receive_buffer);
    
    printf("Buffer edge tests completed\n\n");
}

// Test error recovery
void test_error_recovery(CustomUARTDriver* uart) {
    printf("Testing error recovery...\n");
    
    // Reset the UART
    custom_uart_flush_tx(uart);
    custom_uart_flush_rx(uart);
    
    // Enable loopback
    custom_uart_set_loopback(uart, true);
    
    // Set a high error rate
    custom_uart_set_error_simulation(uart, 0.5);
    
    uint8_t test_data[256];
    fill_random(test_data, 256);
    
    // Send data with high error rate
    size_t sent = custom_uart_send_data(uart, test_data, 256);
    printf("Sent %zu bytes with 50%% error rate\n", sent);
    
    // Check errors
    uint32_t errors = custom_uart_get_errors(uart);
    printf("Errors detected: 0x%08X\n", errors);
    
    // Try to read whatever made it through
    uint8_t receive_buffer[256];
    usleep(100000); // Wait for processing
    size_t received = custom_uart_read_data(uart, receive_buffer, 256);
    printf("Received %zu bytes\n", received);
    
    // Disable error simulation
    custom_uart_set_error_simulation(uart, 0.0);
    
    // Try normal transmission again to verify recovery
    custom_uart_flush_tx(uart);
    custom_uart_flush_rx(uart);
    
    sent = custom_uart_send_data(uart, test_data, 256);
    usleep(100000);
    received = custom_uart_read_data(uart, receive_buffer, 256);
    
    if (sent == received && memcmp(test_data, receive_buffer, sent) == 0) {
        printf("Recovery successful - normal operation restored\n");
    } else {
        printf("Recovery failed - normal operation not restored\n");
    }
    
    printf("Error recovery test completed\n");
}

int main() {
    printf("UART Driver Stress Test\n");
    printf("======================\n\n");
    
    // Seed random number generator
    srand(time(NULL));
    
    // Initialize UART
    CustomUARTDriver* uart = custom_uart_init(0, 115200);
    if (!uart) {
        printf("Failed to initialize UART\n");
        return 1;
    }
    
    // Configure UART
    custom_uart_configure(uart, 8, 1, CUSTOM_UART_PARITY_NONE, false);
    
    // Run tests
    test_rapid_transmission(uart);
    test_buffer_edges(uart);
    test_error_recovery(uart);
    
    // Clean up
    custom_uart_deinit(uart);
    
    printf("\nAll stress tests completed\n");
    return 0;
}
