# GDB Debugging Guide for QEMU-MicroPython

This guide provides detailed instructions for debugging MicroPython firmware running in QEMU using GDB (GNU Debugger).

## Prerequisites

- ARM GDB (arm-none-eabi-gdb)
- QEMU with STM32 support
- MicroPython firmware built with debug symbols

## Quick Start

1. Build the firmware with debug symbols:
   ```bash
   ./scripts/build.sh
   ```

2. Start debugging session:
   ```bash
   ./scripts/debug_micropython.sh
   ```

## GDB Commands

### Basic Commands
- `continue` (c) - Continue execution
- `step` (s) - Step into function calls
- `next` (n) - Step over function calls
- `break` (b) - Set breakpoint
- `print` (p) - Print variable value
- `x` - Examine memory
- `info break` - List breakpoints
- `quit` (q) - Exit GDB

### MicroPython-Specific Commands
- `mpy-bt` - Show MicroPython backtrace
- `mpy-locals` - Show local variables in current Python frame
- `mpy-globals` - Show global variables
- `mpy-stack` - Show Python stack contents

### Exception Handling Commands
- `mpy-catch` - Configure exception catching and breakpoints
- `mpy-except-info` - Show exception details
- `mpy-except-bt` - Show exception backtrace
- `mpy-except-vars` - Show variables at exception point

## Debugging Workflow

1. **Starting a Debug Session**
   ```bash
   ./scripts/debug_micropython.sh
   ```
   This will:
   - Start QEMU with GDB server enabled
   - Load the firmware with debug symbols
   - Connect GDB to QEMU
   - Load MicroPython debugging helpers

2. **Setting Breakpoints**
   ```gdb
   # Break at Python bytecode execution
   break mp_execute_bytecode
   
   # Break at specific Python function
   break mp_obj_fun_call
   
   # Break at C function
   break SystemInit
   
   # Break on exception
   mpy-catch ValueError
   ```

3. **Examining State**
   ```gdb
   # Show Python backtrace
   mpy-bt
   
   # Show local variables
   mpy-locals
   
   # Show global variables
   mpy-globals
   
   # Show CPU registers
   info registers
   
   # Examine memory
   x/4wx $sp  # Show 4 words at stack pointer
   
   # Show exception information
   mpy-except-info
   ```

4. **Stepping Through Code**
   ```gdb
   # Step into next instruction (including functions)
   step
   
   # Step over functions
   next
   
   # Continue until next breakpoint
   continue
   ```

## Common Debug Scenarios

### 1. Debugging Python Code
```gdb
# Break at Python bytecode execution
break mp_execute_bytecode

# Continue to breakpoint
continue

# Show Python state
mpy-bt
mpy-locals
```

### 2. Debugging Memory Issues
```gdb
# Break at memory allocation
break m_malloc

# Examine memory at address
x/32x $r0

# Watch memory location
watch *0x20000000
```

### 3. Debugging Startup
```gdb
# Break at system initialization
break SystemInit

# Break at MicroPython initialization
break mp_init
```

### 4. Debugging Exceptions
```gdb
# Break on all ZeroDivisionError exceptions
mpy-catch ZeroDivisionError all

# Break only on uncaught ValueError exceptions
mpy-catch ValueError uncaught

# When exception occurs, examine it
mpy-except-info
mpy-except-bt
mpy-except-vars

# Continue execution
continue
```

## Exception Handling

### Configuring Exception Breakpoints

The `mpy-catch` command allows you to set breakpoints that trigger when specific exceptions occur:

```gdb
# Syntax: mpy-catch <exception_type> [all|uncaught]
mpy-catch ValueError           # Break on uncaught ValueError (default)
mpy-catch ZeroDivisionError all  # Break on all ZeroDivisionError exceptions
```

### Examining Exceptions

When an exception breakpoint is hit, you can use these commands to examine the exception:

```gdb
# Show exception type and value
mpy-except-info

# Show exception traceback
mpy-except-bt

# Show local variables at exception point
mpy-except-vars
```

### Exception Debugging Workflow

1. Set up exception breakpoints at the start of your debugging session:
   ```gdb
   mpy-catch ValueError
   mpy-catch ZeroDivisionError all
   ```

2. Run your program:
   ```gdb
   continue
   ```

3. When an exception occurs, GDB will stop. Examine the exception:
   ```gdb
   mpy-except-info
   mpy-except-bt
   mpy-except-vars
   ```

4. After examining the exception, you can:
   - Fix the issue and restart
   - Continue execution to see if the exception is handled
   - Set additional breakpoints to investigate further

## Error Handling

### Common Issues and Solutions

1. **GDB Connection Failed**
   - Check if QEMU is running with GDB server enabled
   - Verify port 1234 is available
   - Check firewall settings

2. **Symbol Loading Failed**
   - Verify firmware was built with debug symbols
   - Check file paths are correct
   - Try reloading symbols: `file firmware/build/firmware.elf`

3. **Breakpoints Not Working**
   - Verify code was compiled with debug info
   - Check if breakpoint address is correct
   - Try hardware breakpoints: `hbreak` instead of `break`

4. **Cannot See Python Variables**
   - Ensure you're at a Python execution point
   - Check if MicroPython helpers are loaded
   - Try reloading Python state: `mpy-reload`

5. **Exception Breakpoints Not Triggering**
   - Verify exception type name is correct
   - Check if exception is being caught before GDB can break
   - Try using `mpy-catch <exception> all` to catch all instances

## Advanced Features

### 1. Conditional Breakpoints
```gdb
# Break when condition is met
break mp_execute_bytecode if $r0 == 0x42

# Break on Python exception
break mp_raise
```

### 2. Logging and Output
```gdb
# Enable logging
set logging on
set logging file debug.log

# Enable debug output
set debug python on
set debug remote 1
```

### 3. Python State Inspection
```gdb
# Print MicroPython object
print mp_obj_str_get_str($r0)

# Show heap statistics
call mp_heap_info()
```

## Best Practices

1. **Efficient Debugging**
   - Use conditional breakpoints to narrow down issues
   - Save debugging commands in a GDB script file
   - Log important state changes

2. **Memory Management**
   - Watch for memory leaks using heap statistics
   - Monitor stack usage
   - Check memory alignment

3. **Python Integration**
   - Use MicroPython-specific commands for Python state
   - Combine C-level and Python-level debugging
   - Keep track of both execution contexts

4. **Exception Handling**
   - Set breakpoints on specific exception types
   - Examine the exception state when breakpoints trigger
   - Check local variables at the exception point
   - Use the traceback to understand the exception path

## Troubleshooting

### Debug Log Analysis
The debug session creates several log files:
- `gdb_test.log` - GDB execution log
- `qemu_log.txt` - QEMU system log
- `debug_log.txt` - Debug session log

Check these logs for:
- Error messages
- Memory access violations
- System state changes
- Python execution trace
- Exception information

### Common Error Messages

1. **"Cannot insert breakpoint"**
   - Cause: Code section not loaded or write-protected
   - Solution: Use hardware breakpoints or verify memory location

2. **"No symbol table loaded"**
   - Cause: Debug symbols missing
   - Solution: Rebuild with debug info and reload symbols

3. **"Remote connection closed"**
   - Cause: QEMU crashed or connection lost
   - Solution: Check QEMU status and restart debug session

4. **"No active exception"**
   - Cause: Trying to examine exception when none exists
   - Solution: Set exception breakpoints and continue until one occurs

## Additional Resources

- [GDB Documentation](https://sourceware.org/gdb/documentation/)
- [MicroPython Development Guide](https://docs.micropython.org/en/latest/develop/)
- [QEMU User Guide](https://www.qemu.org/docs/master/)

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the log files
3. Open an issue on GitHub with:
   - Error messages
   - Log files
   - Steps to reproduce 