# Custom UART Driver Testing

This document describes the comprehensive test suite developed for the custom UART driver in the QEMU-MicroPython project.

## Overview

The custom UART driver extends the standard STM32 UART functionality with enhanced features for debugging, testing, and simulating real-world conditions. To ensure the reliability and proper functioning of these features, a comprehensive test suite has been developed.

## Test Components

The test suite consists of the following components:

1. **Basic UART Test** (`test_uart.sh`): Tests the core functionality of the UART driver, including:
   - Basic data transmission and reception
   - Loopback mode
   - Error simulation with various error rates
   - Noise simulation with different noise levels
   - Data recording capability

2. **Network Simulation Test** (`test_uart_network.sh`): Tests communication between two UART devices, simulating real-world network conditions:
   - Perfect conditions (no errors or noise)
   - Bit noise simulation (random bit flips)
   - Packet loss simulation
   - Combined error and noise conditions
   - Harsh communication environments

3. **Stress Test** (`test_uart_stress.sh`): Tests the UART driver under high load conditions:
   - Rapid data transmission and reception
   - Buffer edge conditions
   - Error recovery capabilities

4. **MicroPython Bindings Test** (`test_uart_bindings.sh`): Tests the MicroPython integration of the custom UART driver, including:
   - Basic UART functionality in MicroPython
   - Enhanced features (loopback, error simulation, noise simulation, recording)

5. **Bridge Test** (`bridge_test.c`): A specialized test for the UART device bridging functionality, demonstrating:
   - Data transfer between two UART devices
   - Bidirectional communication
   - Debug callbacks

## Simulation Capabilities

The custom UART driver provides several simulation capabilities for testing:

### Error Simulation

The driver can simulate communication errors at a configurable rate. This is useful for testing how applications handle packet loss and transmission failures.

Example:
```c
// Configure for 10% error rate
custom_uart_set_error_simulation(uart, 0.1);
```

### Noise Simulation

The driver can simulate signal noise by randomly flipping bits in the transmitted data. This helps test application robustness against corruption.

Example:
```c
// Configure for 5% bit noise
custom_uart_set_noise_simulation(uart, 0.05);
```

### Timing Simulation

The driver can simulate real-world timing constraints, making transmission and reception respect the configured baud rate.

Example:
```c
// Enable timing simulation
custom_uart_set_timing_simulation(uart, true);
```

## Test Scripts

The test suite includes several scripts to run different aspects of the tests:

- `scripts/test_uart.sh`: Runs the basic UART test
- `scripts/test_uart_network.sh`: Runs the network simulation test
- `scripts/test_uart_stress.sh`: Runs the stress test
- `scripts/test_uart_bindings.sh`: Runs the MicroPython bindings test
- `scripts/test_uart_all.sh`: Runs all tests in sequence
- `scripts/test_uart_micropython.sh`: Runs the MicroPython test on QEMU

## Running the Tests

To run all tests at once:

```bash
./scripts/test_uart_all.sh
```

To run individual tests:

```bash
./scripts/test_uart.sh               # Basic test
./scripts/test_uart_network.sh       # Network test
./scripts/test_uart_stress.sh        # Stress test
./scripts/test_uart_bindings.sh      # MicroPython bindings test
```

To run the MicroPython test on QEMU:

```bash
./scripts/test_uart_micropython.sh
```

## Integration with QEMU

The custom UART driver is designed to integrate with QEMU's character device subsystem. This integration allows for:

1. **Hardware Emulation**: The driver can be used to emulate UART hardware in QEMU.
2. **Data Transfer**: Data can be transferred between emulated UART devices.
3. **Bidirectional Communication**: Devices can communicate in both directions.

## MicroPython Integration

The custom UART driver provides Python bindings for MicroPython, exposing all enhanced features:

```python
import machine

# Initialize UART
uart = machine.UART(2, 115200)

# Enable loopback mode
uart.set_loopback(True)

# Configure error simulation
uart.set_error_simulation(0.1)  # 10% error rate

# Configure noise simulation
uart.set_noise_simulation(0.05)  # 5% bit noise

# Start recording
uart.start_recording("uart_traffic.bin")

# Send and receive data
uart.write("Hello, world!")
data = uart.read()

# Stop recording
uart.stop_recording()
```

## Future Enhancements

Planned enhancements to the testing framework include:

1. **Performance Benchmarking**: Automated tests to measure throughput and latency.
2. **Integration Testing**: Testing communication with other peripherals.
3. **QEMU Integration Improvements**: Better integration with QEMU's timing and interrupt systems.
4. **Extended Protocol Testing**: Testing common serial protocols (MODBUS, SLIP, etc.). 