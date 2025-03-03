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