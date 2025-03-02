# Custom UART Driver for QEMU-MicroPython Integration

This module provides an enhanced UART driver implementation designed specifically for the QEMU-MicroPython project. It extends the standard STM32 UART functionality with additional features for testing, debugging, and simulating real-world conditions.

## Purpose

The custom UART driver serves several key purposes:

1. **Enhanced Debugging**: Provides hooks for monitoring and debugging UART communications in the virtual environment
2. **Network Simulation**: Simulates real-world network conditions including noise, errors, and timing constraints
3. **Data Recording**: Allows recording of UART traffic for later analysis or replay
4. **Testing Framework**: Enables comprehensive testing of IoT applications in a controlled environment
5. **Loopback Mode**: Simplifies unit testing by providing instantaneous local echo capabilities

## Features

- **Multiple UART Instances**: Supports up to 10 independent UART channels
- **Flexible Configuration**: Configurable baudrate, data bits, stop bits, parity, and flow control
- **Debug Callbacks**: Register custom callbacks to monitor TX and RX operations
- **Error Simulation**: Simulate communication errors at configurable rates
- **Noise Simulation**: Add random bit flips to test application robustness
- **Timing Simulation**: Simulate real-world timing constraints
- **Data Recording**: Record UART traffic to a file for later analysis
- **Loopback Mode**: Automatically echo transmitted bytes back to the receiver
- **Buffered Operation**: Efficient buffered TX and RX operations
- **State Monitoring**: Track the UART state and error conditions

## Integration with QEMU

This driver is designed to integrate with QEMU's device emulation framework. It provides a bridge between the MicroPython code running in the virtual environment and the host system. 

The integration is handled through:

1. **Character Device Backend**: Connects to QEMU's character device subsystem
2. **IRQ Handling**: Properly signals interrupts to the virtual CPU
3. **Timing Coordination**: Works with QEMU's timing infrastructure

## Usage Example

Here's a simple example of how to use the custom UART driver:

```c
#include "custom_uart_driver.h"

// Initialize UART channel 0 with baudrate 115200
CustomUARTDriver* uart = custom_uart_init(0, 115200);

// Configure for 8 data bits, 1 stop bit, no parity, no flow control
custom_uart_configure(uart, 8, 1, UART_PARITY_NONE, false);

// Enable loopback mode for testing
custom_uart_set_loopback(uart, true);

// Send some data
const uint8_t data[] = "Hello, UART!";
custom_uart_send_data(uart, data, sizeof(data) - 1); // Don't send the null terminator

// Read the data back (should be available immediately in loopback mode)
uint8_t buffer[20];
size_t bytes_read = custom_uart_read_data(uart, buffer, sizeof(buffer));

// Clean up when done
custom_uart_deinit(uart);
```

## Testing Network Conditions

One of the key features of this driver is the ability to simulate various network conditions:

```c
// Simulate 5% packet loss
custom_uart_set_error_simulation(uart, 0.05);

// Add random bit flips (2% of bits affected)
custom_uart_set_noise_simulation(uart, 0.02);

// Enable timing simulation to accurately model UART timing
custom_uart_set_timing_simulation(uart, true);
```

## Recording UART Traffic

For debugging or analysis purposes, you can record all UART traffic:

```c
// Start recording to a file
custom_uart_start_recording(uart, "uart_traffic.bin");

// ... perform your UART operations ...

// Stop recording
custom_uart_stop_recording(uart);
```

## Debug Callbacks

Register callbacks to monitor UART operations:

```c
void on_tx(uint8_t byte, void* user_data) {
    printf("TX: 0x%02X\n", byte);
}

void on_rx(uint8_t byte, void* user_data) {
    printf("RX: 0x%02X\n", byte);
}

// Register the callbacks
custom_uart_set_debug_callbacks(uart, on_tx, on_rx, NULL);
```

## Error Handling

The driver provides comprehensive error reporting:

```c
// Check for errors and clear the error flags
uint32_t errors = custom_uart_get_errors(uart);
if (errors & UART_ERROR_OVERFLOW) {
    printf("Buffer overflow occurred\n");
}
if (errors & UART_ERROR_FRAMING) {
    printf("Framing error detected\n");
}
// ... check other error flags ...
```

## Integration with MicroPython

To use this driver with MicroPython, it needs to be integrated with the MicroPython machine.UART implementation. This integration involves:

1. Modifying MicroPython's UART implementation to use the custom driver
2. Extending the MicroPython UART API to expose the enhanced features
3. Creating Python bindings for the simulation and debugging capabilities

## Building and Installation

The driver is designed to be integrated into the QEMU-MicroPython project. To build and install:

1. Place the custom_uart_driver.c and custom_uart_driver.h files in the appropriate source directory
2. Update the build system to include these files
3. Modify the QEMU integration layer to use the custom driver
4. Build the project as usual

## License

This driver is released under the MIT License. See the LICENSE file for details.

## Contributing

Contributions to improve the driver are welcome. Please follow the standard contribution process:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Known Issues and Limitations

- The timing simulation is currently a placeholder and needs to be integrated with QEMU's timing system
- Error simulation is basic and could be extended to model more complex error patterns
- The recording format is simple; a more structured format might be better for complex analysis 