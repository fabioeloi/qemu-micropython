/*
 * Custom UART Driver Test Program
 *
 * This program demonstrates how to use the custom UART driver
 * for testing and simulation of UART communications in a QEMU environment.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <unistd.h>  /* For sleep() */
#include <time.h>    /* For time() */

#include "custom_uart_driver.h"

/* Debug callback functions */
static void debug_tx_callback(uint8_t byte, void* user_data);
static void debug_rx_callback(uint8_t byte, void* user_data);

/* Test scenarios */
static void test_basic_communication(CustomUARTDriver* uart);
static void test_loopback_mode(CustomUARTDriver* uart);
static void test_error_simulation(CustomUARTDriver* uart);
static void test_noise_simulation(CustomUARTDriver* uart);
static void test_data_recording(CustomUARTDriver* uart);

/* Helper functions */
static void print_buffer(const uint8_t* buffer, size_t size);
static void clear_buffer(uint8_t* buffer, size_t size);

int main(int argc, char* argv[]) {
    printf("Custom UART Driver Test Program\n");
    printf("================================\n\n");
    
    /* Seed the random number generator */
    srand((unsigned int)time(NULL));
    
    /* Initialize UART channel 0 with baudrate 115200 */
    CustomUARTDriver* uart = custom_uart_init(0, 115200);
    if (!uart) {
        printf("Failed to initialize UART driver\n");
        return 1;
    }
    
    /* Configure for 8 data bits, 1 stop bit, no parity, no flow control */
    printf("Configuring UART...\n");
    if (!custom_uart_configure(uart, 8, 1, CUSTOM_UART_PARITY_NONE, false)) {
        fprintf(stderr, "Failed to configure UART\n");
        custom_uart_deinit(uart);
        return 1;
    }
    
    /* Register debug callbacks */
    custom_uart_set_debug_callbacks(uart, debug_tx_callback, debug_rx_callback, NULL);
    
    /* Run the tests */
    printf("\n--- Basic Communication Test ---\n");
    test_basic_communication(uart);
    
    printf("\n--- Loopback Mode Test ---\n");
    test_loopback_mode(uart);
    
    printf("\n--- Error Simulation Test ---\n");
    test_error_simulation(uart);
    
    printf("\n--- Noise Simulation Test ---\n");
    test_noise_simulation(uart);
    
    printf("\n--- Data Recording Test ---\n");
    test_data_recording(uart);
    
    /* Clean up */
    custom_uart_deinit(uart);
    
    printf("\nAll tests completed\n");
    return 0;
}

/* Debug callback for transmitted bytes */
static void debug_tx_callback(uint8_t byte, void* user_data) {
    printf("TX: 0x%02X ('%c')\n", byte, (byte >= 32 && byte <= 126) ? byte : '.');
}

/* Debug callback for received bytes */
static void debug_rx_callback(uint8_t byte, void* user_data) {
    printf("RX: 0x%02X ('%c')\n", byte, (byte >= 32 && byte <= 126) ? byte : '.');
}

/* Basic communication test */
static void test_basic_communication(CustomUARTDriver* uart) {
    const uint8_t data[] = "Hello, UART!";
    const size_t data_size = sizeof(data) - 1; /* Don't include null terminator */
    uint8_t buffer[64];
    size_t bytes_read;
    
    printf("Sending: \"%s\"\n", data);
    
    /* Send the data */
    size_t bytes_sent = custom_uart_send_data(uart, data, data_size);
    printf("Bytes sent: %zu\n", bytes_sent);
    
    /* Sleep briefly to simulate processing time */
    usleep(100000); /* 100 ms */
    
    /* Check how many bytes are available to read */
    size_t available = custom_uart_available(uart);
    printf("Bytes available to read: %zu\n", available);
    
    /* Read the data */
    clear_buffer(buffer, sizeof(buffer));
    bytes_read = custom_uart_read_data(uart, buffer, sizeof(buffer));
    
    /* Print the received data */
    printf("Bytes read: %zu\n", bytes_read);
    if (bytes_read > 0) {
        printf("Received: \"");
        for (size_t i = 0; i < bytes_read; i++) {
            printf("%c", buffer[i]);
        }
        printf("\"\n");
        printf("Raw data: ");
        print_buffer(buffer, bytes_read);
    }
    
    /* Check for any errors */
    uint32_t errors = custom_uart_get_errors(uart);
    if (errors) {
        printf("Errors detected: 0x%08X\n", errors);
    } else {
        printf("No errors detected\n");
    }
}

/* Loopback mode test */
static void test_loopback_mode(CustomUARTDriver* uart) {
    const uint8_t data[] = "Testing loopback mode";
    const size_t data_size = sizeof(data) - 1; /* Don't include null terminator */
    uint8_t buffer[64];
    size_t bytes_read;
    
    /* Enable loopback mode */
    custom_uart_set_loopback(uart, true);
    printf("Loopback mode enabled\n");
    
    printf("Sending: \"%s\"\n", data);
    
    /* Send the data */
    size_t bytes_sent = custom_uart_send_data(uart, data, data_size);
    printf("Bytes sent: %zu\n", bytes_sent);
    
    /* Since loopback is enabled, the data should be immediately available */
    size_t available = custom_uart_available(uart);
    printf("Bytes available to read: %zu\n", available);
    
    /* Read the data */
    clear_buffer(buffer, sizeof(buffer));
    bytes_read = custom_uart_read_data(uart, buffer, sizeof(buffer));
    
    /* Print the received data */
    printf("Bytes read: %zu\n", bytes_read);
    if (bytes_read > 0) {
        printf("Received: \"");
        for (size_t i = 0; i < bytes_read; i++) {
            printf("%c", buffer[i]);
        }
        printf("\"\n");
    }
    
    /* Disable loopback mode */
    custom_uart_set_loopback(uart, false);
    printf("Loopback mode disabled\n");
}

/* Error simulation test */
static void test_error_simulation(CustomUARTDriver* uart) {
    const uint8_t data[] = "Testing error simulation";
    const size_t data_size = sizeof(data) - 1; /* Don't include null terminator */
    uint8_t buffer[64];
    size_t bytes_read, bytes_sent;
    
    /* Enable loopback mode for testing */
    custom_uart_set_loopback(uart, true);
    
    /* Test with different error rates */
    float error_rates[] = {0.0, 0.1, 0.25, 0.5, 0.75};
    
    for (size_t i = 0; i < sizeof(error_rates) / sizeof(error_rates[0]); i++) {
        /* Set the error rate */
        float error_rate = error_rates[i];
        custom_uart_set_error_simulation(uart, error_rate);
        printf("\nTesting with error rate: %.2f\n", error_rate);
        
        /* Flush the RX buffer */
        custom_uart_flush_rx(uart);
        
        /* Send the data */
        printf("Sending: \"%s\" (%zu bytes)\n", data, data_size);
        bytes_sent = custom_uart_send_data(uart, data, data_size);
        printf("Bytes sent: %zu\n", bytes_sent);
        
        /* Check how many bytes are available to read */
        size_t available = custom_uart_available(uart);
        printf("Bytes available to read: %zu\n", available);
        
        /* Read the data */
        clear_buffer(buffer, sizeof(buffer));
        bytes_read = custom_uart_read_data(uart, buffer, sizeof(buffer));
        
        /* Print the received data */
        printf("Bytes read: %zu\n", bytes_read);
        if (bytes_read > 0) {
            printf("Received: \"");
            for (size_t j = 0; j < bytes_read; j++) {
                printf("%c", buffer[j]);
            }
            printf("\"\n");
        }
        
        /* Calculate effective error rate */
        float effective_error_rate = 1.0f - ((float)bytes_read / (float)data_size);
        printf("Effective error rate: %.2f (expected: %.2f)\n", effective_error_rate, error_rate);
    }
    
    /* Disable error simulation */
    custom_uart_set_error_simulation(uart, 0.0);
    
    /* Disable loopback mode */
    custom_uart_set_loopback(uart, false);
}

/* Noise simulation test */
static void test_noise_simulation(CustomUARTDriver* uart) {
    const uint8_t data[] = "Testing noise simulation";
    const size_t data_size = sizeof(data) - 1; /* Don't include null terminator */
    uint8_t buffer[64];
    uint8_t original[64];
    size_t bytes_read, bytes_sent;
    
    /* Enable loopback mode for testing */
    custom_uart_set_loopback(uart, true);
    
    /* Test with different noise levels */
    float noise_levels[] = {0.0, 0.01, 0.05, 0.1, 0.2};
    
    for (size_t i = 0; i < sizeof(noise_levels) / sizeof(noise_levels[0]); i++) {
        /* Set the noise level */
        float noise_level = noise_levels[i];
        custom_uart_set_noise_simulation(uart, noise_level);
        printf("\nTesting with noise level: %.2f\n", noise_level);
        
        /* Flush the RX buffer */
        custom_uart_flush_rx(uart);
        
        /* Send the data */
        printf("Sending: \"%s\" (%zu bytes)\n", data, data_size);
        
        /* Save the original data for comparison */
        memcpy(original, data, data_size);
        
        bytes_sent = custom_uart_send_data(uart, data, data_size);
        printf("Bytes sent: %zu\n", bytes_sent);
        
        /* Check how many bytes are available to read */
        size_t available = custom_uart_available(uart);
        printf("Bytes available to read: %zu\n", available);
        
        /* Read the data */
        clear_buffer(buffer, sizeof(buffer));
        bytes_read = custom_uart_read_data(uart, buffer, sizeof(buffer));
        
        /* Print the received data */
        printf("Bytes read: %zu\n", bytes_read);
        if (bytes_read > 0) {
            printf("Received: \"");
            for (size_t j = 0; j < bytes_read; j++) {
                printf("%c", buffer[j]);
            }
            printf("\"\n");
            
            /* Compare with original data */
            int different_bytes = 0;
            int different_bits = 0;
            for (size_t j = 0; j < bytes_read && j < data_size; j++) {
                if (buffer[j] != original[j]) {
                    different_bytes++;
                    /* Count the number of different bits */
                    uint8_t xor_result = buffer[j] ^ original[j];
                    for (int k = 0; k < 8; k++) {
                        if ((xor_result >> k) & 0x01) {
                            different_bits++;
                        }
                    }
                }
            }
            printf("Different bytes: %d/%zu (%.2f%%)\n", different_bytes, bytes_read, 
                  (float)different_bytes / bytes_read * 100.0f);
            printf("Different bits: %d/%zu (%.2f%%)\n", different_bits, bytes_read * 8, 
                  (float)different_bits / (bytes_read * 8) * 100.0f);
        }
    }
    
    /* Disable noise simulation */
    custom_uart_set_noise_simulation(uart, 0.0);
    
    /* Disable loopback mode */
    custom_uart_set_loopback(uart, false);
}

/* Data recording test */
static void test_data_recording(CustomUARTDriver* uart) {
    const uint8_t data1[] = "First message";
    const uint8_t data2[] = "Second message";
    const uint8_t data3[] = "Third message";
    
    /* Enable loopback mode for testing */
    custom_uart_set_loopback(uart, true);
    
    /* Start recording */
    const char* filename = "uart_traffic.bin";
    if (!custom_uart_start_recording(uart, filename)) {
        printf("Failed to start recording\n");
        return;
    }
    printf("Recording started to file: %s\n", filename);
    
    /* Send some data */
    printf("Sending: \"%s\"\n", data1);
    custom_uart_send_data(uart, data1, strlen((const char*)data1));
    
    /* Read the data to trigger the loopback */
    uint8_t buffer[64];
    custom_uart_read_data(uart, buffer, sizeof(buffer));
    
    /* Send more data */
    printf("Sending: \"%s\"\n", data2);
    custom_uart_send_data(uart, data2, strlen((const char*)data2));
    
    /* Read the data to trigger the loopback */
    custom_uart_read_data(uart, buffer, sizeof(buffer));
    
    /* Send one more message */
    printf("Sending: \"%s\"\n", data3);
    custom_uart_send_data(uart, data3, strlen((const char*)data3));
    
    /* Read the data to trigger the loopback */
    custom_uart_read_data(uart, buffer, sizeof(buffer));
    
    /* Stop recording */
    custom_uart_stop_recording(uart);
    printf("Recording stopped\n");
    
    /* Verify the file was created */
    FILE* file = fopen(filename, "rb");
    if (file) {
        fseek(file, 0, SEEK_END);
        long size = ftell(file);
        fclose(file);
        printf("Recording file size: %ld bytes\n", size);
    } else {
        printf("Failed to open recording file\n");
    }
    
    /* Disable loopback mode */
    custom_uart_set_loopback(uart, false);
}

/* Helper function to print a buffer in hex format */
static void print_buffer(const uint8_t* buffer, size_t size) {
    for (size_t i = 0; i < size; i++) {
        printf("%02X ", buffer[i]);
    }
    printf("\n");
}

/* Helper function to clear a buffer */
static void clear_buffer(uint8_t* buffer, size_t size) {
    memset(buffer, 0, size);
} 