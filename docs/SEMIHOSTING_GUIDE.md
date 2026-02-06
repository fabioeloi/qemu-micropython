# QEMU Semihosting Integration for MicroPython

## Overview

This document describes the semihosting integration for MicroPython running in QEMU environments. Semihosting provides a reliable mechanism for console I/O that bypasses the need for UART emulation, which can be unreliable in QEMU.

## What is Semihosting?

Semihosting is an ARM feature that allows embedded software to communicate with a host computer through a debug connection. When running in QEMU, semihosting operations are handled by the QEMU host process, providing reliable console output without requiring peripheral emulation.

## Architecture

The semihosting integration consists of three layers:

### 1. Core Semihosting Layer (`qemu_semihost.c/h`)
- Implements ARM semihosting protocol using breakpoint instructions
- Provides low-level console write operations
- Handles character and string output operations

### 2. MicroPython Bindings (`micropython_semihost.c`)
- Exposes semihosting functionality to Python code
- Provides the `qemu_console` Python module
- Handles Python-to-C parameter conversion

### 3. Python API (`qemu_console` module)
- High-level Python interface for console output
- Simple functions for common operations
- Error handling and availability checking

## Using Semihosting in Python

### Basic Usage

```python
import qemu_console

# Check if semihosting is available
if qemu_console.available():
    # Write a string
    qemu_console.print_text("Hello from MicroPython!\r\n")
    
    # Write individual characters
    qemu_console.print_char(ord('A'))
    qemu_console.print_char(ord('\n'))
```

### Practical Example: Logging

```python
import qemu_console

def log_message(level, message):
    """Log a message via semihosting"""
    if qemu_console.available():
        timestamp = "2025-03-04"  # Would use real time in practice
        output = f"[{timestamp}] {level}: {message}\r\n"
        qemu_console.print_text(output)
    else:
        # Fallback to standard print
        print(f"{level}: {message}")

# Usage
log_message("INFO", "System initialized")
log_message("WARN", "Low memory condition")
log_message("ERROR", "Sensor read failed")
```

### Practical Example: Progress Tracking

```python
import qemu_console
import time

def show_progress(total_steps):
    """Display progress bar using semihosting"""
    if not qemu_console.available():
        return
    
    qemu_console.print_text("Progress: [")
    
    for step in range(total_steps):
        # Do some work...
        time.sleep(0.1)
        
        # Update progress
        qemu_console.print_char(ord('#'))
    
    qemu_console.print_text("] Done!\r\n")
```

## API Reference

### `qemu_console.print_text(text)`

Write a string to the QEMU console via semihosting.

**Parameters:**
- `text` (str): The string to output

**Returns:** None

**Raises:** OSError if semihosting operation fails

### `qemu_console.print_char(char_code)`

Write a single character to the QEMU console.

**Parameters:**
- `char_code` (int): ASCII code of character to output (0-255)

**Returns:** None

**Raises:** 
- ValueError if char_code is out of range
- OSError if semihosting operation fails

### `qemu_console.available()`

Check if semihosting is available in the current environment.

**Parameters:** None

**Returns:** bool - True if semihosting is available, False otherwise

## Building and Integration

### Adding to MicroPython Build

1. Ensure files are in the `src/integration/` directory:
   - `qemu_semihost.c`
   - `qemu_semihost.h`
   - `micropython_semihost.c`

2. The module uses `MP_REGISTER_MODULE` for automatic registration

3. Rebuild MicroPython firmware with these files included

### QEMU Configuration

Ensure QEMU is started with semihosting enabled:

```bash
qemu-system-arm \
    -machine olimex-stm32-h405 \
    -cpu cortex-m4 \
    -kernel firmware.elf \
    -semihosting \
    -semihosting-config enable=on,target=native \
    -nographic
```

## Testing

### Running Tests

```bash
# Run the test script in QEMU
./scripts/run_qemu.sh tests/test_semihosting.py
```

### Expected Output

```
=== Testing QEMU Semihosting Integration ===

[OK] qemu_console module imported successfully

1. Checking semihosting availability...
[OK] Semihosting is available

2. Testing string output via semihosting...
[OK] String output successful

3. Testing character output via semihosting...
[OK] Character output successful

4. Testing multiple string outputs...
[OK] Multiple string outputs successful

=== All Tests Passed ===
```

## Benefits

1. **Reliability**: More reliable than emulated UART in QEMU
2. **Simplicity**: No peripheral configuration required
3. **Performance**: Direct host I/O without emulation overhead
4. **Debugging**: Immediate console output for debugging

## Limitations

1. **QEMU Only**: Only works when running in QEMU, not on physical hardware
2. **Output Only**: Current implementation only supports output operations
3. **No Buffering**: Each call results in immediate output

## Future Enhancements

Potential improvements for future versions:

- Input operations (reading from console)
- File I/O operations
- System call support
- Performance optimizations with buffering

## Troubleshooting

### Module Import Fails

If `import qemu_console` fails:
1. Verify the module was compiled and linked into firmware
2. Check MicroPython build logs for errors
3. Ensure `MP_REGISTER_MODULE` macro is working

### No Output Appears

If semihosting output doesn't appear:
1. Verify QEMU was started with `-semihosting` flag
2. Check that `-semihosting-config enable=on` is set
3. Ensure `qemu_console.available()` returns True

### Output is Garbled

If output appears corrupted:
1. Ensure proper line endings (`\r\n` for console)
2. Check character encoding (ASCII expected)
3. Verify breakpoint instruction format (should be `bkpt #0xAB`)

## Related Documentation

- [GDB Debugging Guide](GDB_DEBUGGING.md)
- [UART Driver Testing](UART_DRIVER_TESTING.md)
- [QEMU Configuration](../QEMU-STM32-NOTES.md)

## References

- ARM Semihosting Specification
- QEMU Semihosting Documentation
- MicroPython C Module Development Guide
