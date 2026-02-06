# Integration Modules

This directory contains C modules that integrate various features with MicroPython for the QEMU environment.

## Modules

### QEMU UART Bridge (`qemu_uart_bridge.c/h`)
Custom UART driver integration with enhanced simulation features for QEMU.

**Features:**
- Loopback mode for testing
- Error and noise simulation
- Device-to-device communication
- Network protocol simulation

### MicroPython UART Integration (`micropython_integration.c`)
Python bindings for the custom UART driver.

**Provides:**
- `machine.UART` extensions for QEMU
- Enhanced testing capabilities
- Simulation control from Python

### QEMU Semihosting (`qemu_semihost.c/h`, `micropython_semihost.c`)
ARM semihosting support for reliable console I/O in QEMU.

**Features:**
- Direct console output without UART emulation
- Simple Python API via `qemu_console` module
- Character and string output operations
- Runtime availability checking

**Python API:**
```python
import qemu_console

# Write strings
qemu_console.print_text("Hello World\r\n")

# Write characters
qemu_console.print_char(ord('A'))

# Check availability
if qemu_console.available():
    qemu_console.print_text("Semihosting is available\r\n")
```

## Building

Each module is compiled as part of the MicroPython build process. To build individually:

```bash
# Build semihosting module
./scripts/build_semihost.sh

# Build UART modules (typically part of main build)
make -C src/
```

## Testing

Test scripts are located in the `tests/` directory:

- `tests/test_semihosting.py` - Semihosting functionality tests
- `tests/test_gdb_integration.py` - GDB integration tests
- Various UART test scripts

## Documentation

Detailed documentation for each module:

- [Semihosting Guide](../docs/SEMIHOSTING_GUIDE.md)
- [UART Driver Testing](../docs/UART_DRIVER_TESTING.md)
- [UART Integration Guide](../docs/UART_INTEGRATION_GUIDE.md)

## Development

### Adding New Integration Modules

1. Create your C source files in this directory
2. Implement the functionality
3. Create Python bindings using MicroPython's module system
4. Register the module with `MP_REGISTER_MODULE`
5. Add tests in `tests/`
6. Document in `docs/`

### Module Registration Pattern

```c
// Define your module functions
STATIC mp_obj_t my_function(mp_obj_t arg) {
    // Implementation
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(my_function_obj, my_function);

// Create module globals table
STATIC const mp_rom_map_elem_t my_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_my_module) },
    { MP_ROM_QSTR(MP_QSTR_my_function), MP_ROM_PTR(&my_function_obj) },
};
STATIC MP_DEFINE_CONST_DICT(my_module_globals, my_module_globals_table);

// Define the module
const mp_obj_module_t my_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&my_module_globals,
};

// Register with MicroPython
MP_REGISTER_MODULE(MP_QSTR_my_module, my_module);
```

## Requirements

- ARM GCC toolchain (`arm-none-eabi-gcc`)
- MicroPython source tree
- QEMU with ARM Cortex-M4 support

## Related Files

- `config/boards/` - Board configuration files
- `config/qemu/` - QEMU machine configurations
- `scripts/` - Build and test scripts
- `firmware/` - Compiled firmware binaries
