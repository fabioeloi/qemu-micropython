# Semihosting Integration Guide

This guide explains how to integrate the semihosting module into your MicroPython build for QEMU environments.

## Overview

The semihosting integration provides reliable console I/O for MicroPython running in QEMU through ARM's semihosting protocol. This guide covers the complete integration process.

## Prerequisites

Before starting, ensure you have:

1. ARM GCC toolchain installed (`arm-none-eabi-gcc`)
2. MicroPython source tree cloned and configured
3. QEMU with ARM support
4. Basic knowledge of MicroPython's build system

## Integration Steps

### Step 1: Verify Source Files

Ensure these files exist in `src/integration/`:

```
src/integration/
├── qemu_semihost.h          # Header for semihosting API
├── qemu_semihost.c          # Core semihosting implementation
└── micropython_semihost.c   # Python bindings
```

### Step 2: Add to MicroPython Build

#### Option A: Using MicroPython's Module Registration

The module uses `MP_REGISTER_MODULE` which automatically registers the module with MicroPython. Simply include the source files in your build.

Add to your `Makefile` or build configuration:

```makefile
# Add semihosting sources to build
SRC_C += \
    src/integration/qemu_semihost.c \
    src/integration/micropython_semihost.c
```

#### Option B: Manual Integration

If using a custom build system, compile the files separately and link them:

```bash
# Compile semihosting core
arm-none-eabi-gcc -c src/integration/qemu_semihost.c \
    -o build/qemu_semihost.o \
    -mcpu=cortex-m4 -mthumb -O2

# Compile Python bindings
arm-none-eabi-gcc -c src/integration/micropython_semihost.c \
    -o build/micropython_semihost.o \
    -mcpu=cortex-m4 -mthumb -O2 \
    -I path/to/micropython \
    -I path/to/micropython/py

# Link with your firmware
arm-none-eabi-gcc ... build/qemu_semihost.o build/micropython_semihost.o ...
```

### Step 3: Configure QEMU

When running your firmware in QEMU, enable semihosting:

```bash
qemu-system-arm \
    -machine olimex-stm32-h405 \
    -cpu cortex-m4 \
    -kernel firmware.elf \
    -semihosting \
    -semihosting-config enable=on,target=native \
    -nographic
```

**Important flags:**
- `-semihosting`: Enables semihosting support
- `-semihosting-config enable=on,target=native`: Configures semihosting for native host

### Step 4: Test the Integration

Create a test script to verify functionality:

```python
# test_semihost_integration.py

try:
    import qemu_console
    
    if qemu_console.available():
        qemu_console.print_text("Semihosting is working!\r\n")
        print("Success: Module imported and working")
    else:
        print("Warning: Module loaded but semihosting unavailable")
        
except ImportError as e:
    print(f"Error: Cannot import qemu_console - {e}")
    print("Module integration failed")
```

Run in QEMU:

```bash
./scripts/test_semihosting.sh
```

### Step 5: Use in Your Application

Once integrated, use semihosting in your MicroPython code:

```python
import qemu_console

# Simple output
qemu_console.print_text("System starting...\r\n")

# Logging function
def log(message):
    if qemu_console.available():
        qemu_console.print_text(f"LOG: {message}\r\n")
    else:
        print(message)

log("Application initialized")
```

## Troubleshooting

### Module Not Found

**Problem:** `ImportError: no module named 'qemu_console'`

**Solutions:**
1. Verify files are compiled into firmware
2. Check `MP_REGISTER_MODULE` macro is present
3. Ensure no build errors occurred
4. Rebuild firmware completely

### No Output in QEMU

**Problem:** No semihosting output appears

**Solutions:**
1. Verify QEMU flags: `-semihosting` and `-semihosting-config enable=on`
2. Check `qemu_console.available()` returns True
3. Ensure proper line endings (`\r\n` for console)
4. Check QEMU console output mode

### Build Errors

**Problem:** Compilation fails

**Solutions:**
1. Ensure MicroPython headers are in include path
2. Verify ARM GCC toolchain is correct version
3. Check for missing dependencies
4. Review build log for specific errors

### Semihosting Not Available

**Problem:** `qemu_console.available()` returns False

**Solutions:**
1. Only works in QEMU, not physical hardware
2. QEMU must be configured with semihosting
3. Check QEMU command line flags
4. Verify firmware built with module

## Advanced Configuration

### Custom Output Formatting

Create helper functions for formatted output:

```python
import qemu_console

def print_hex(value):
    """Print value in hexadecimal"""
    if qemu_console.available():
        qemu_console.print_text(f"0x{value:08X}\r\n")

def print_binary(value):
    """Print value in binary"""
    if qemu_console.available():
        qemu_console.print_text(f"0b{value:08b}\r\n")
```

### Conditional Compilation

To include semihosting only for QEMU builds:

```c
// In your board config or mpconfigboard.h
#ifdef BUILD_FOR_QEMU
#define MODULE_QEMU_CONSOLE_ENABLED (1)
#else
#define MODULE_QEMU_CONSOLE_ENABLED (0)
#endif
```

Then in Python:

```python
try:
    import qemu_console
    USE_SEMIHOSTING = qemu_console.available()
except ImportError:
    USE_SEMIHOSTING = False

def output(text):
    if USE_SEMIHOSTING:
        qemu_console.print_text(text + "\r\n")
    else:
        print(text)
```

## Performance Considerations

1. **Direct Output**: Semihosting writes directly to host, bypassing buffers
2. **Overhead**: Breakpoint instructions have minimal overhead in QEMU
3. **Buffering**: Consider buffering multiple writes for performance:

```python
def buffered_output(lines):
    """Write multiple lines efficiently"""
    if qemu_console.available():
        output = "".join(line + "\r\n" for line in lines)
        qemu_console.print_text(output)
```

## Integration Checklist

Use this checklist to verify your integration:

- [ ] Source files present in `src/integration/`
- [ ] Files added to build system
- [ ] Firmware compiles without errors
- [ ] QEMU configured with semihosting flags
- [ ] Test script runs successfully
- [ ] `qemu_console.available()` returns True
- [ ] Output appears in QEMU console
- [ ] Application uses semihosting correctly

## Next Steps

After successful integration:

1. Review the [Semihosting Guide](SEMIHOSTING_GUIDE.md) for usage patterns
2. Explore the demo examples in `src/demo/semihosting_demo.py`
3. Run comprehensive tests with `scripts/test_semihosting.sh`
4. Integrate semihosting into your application's logging system

## Related Documentation

- [Semihosting User Guide](SEMIHOSTING_GUIDE.md)
- [GDB Debugging Guide](GDB_DEBUGGING.md)
- [QEMU Configuration](../QEMU-STM32-NOTES.md)
- [Integration Modules](../src/integration/README.md)

## Support

For issues or questions:

1. Check troubleshooting section above
2. Review test scripts for working examples
3. Open an issue on GitHub with:
   - Build configuration
   - QEMU command line
   - Error messages
   - Expected vs actual behavior
