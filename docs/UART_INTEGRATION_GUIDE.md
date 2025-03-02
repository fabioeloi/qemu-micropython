# Custom UART Driver Integration Guide

This guide provides step-by-step instructions for integrating the custom UART driver with QEMU and MicroPython. The custom UART driver enhances the capabilities of the standard STM32 UART by adding simulation features, debugging tools, and improved reliability in the QEMU environment.

## Overview

The integration involves three main components:

1. **Custom UART Driver**: A C implementation of a UART driver with enhanced features
2. **QEMU Bridge**: Connects the custom driver to QEMU's character device subsystem
3. **MicroPython Bindings**: Provides Python interfaces for the enhanced features

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│                  │    │                  │    │                  │
│   MicroPython    │◄───┤  Custom UART     │◄───┤  QEMU           │
│   Application    │    │  Driver          │    │  Character       │
│                  │    │                  │    │  Device          │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

## Prerequisites

Before beginning the integration, ensure you have:

- The QEMU-MicroPython project set up
- QEMU built with STM32 support
- MicroPython source code

## Integration Steps

### 1. Add Custom UART Driver Files

Copy the following files to your project:

- `src/custom_uart_driver.h` and `src/custom_uart_driver.c`: Core UART driver
- `src/qemu_uart_bridge.c`: QEMU integration layer
- `src/micropython_integration.c`: MicroPython bindings

### 2. Modify QEMU STM32 UART Implementation

To integrate with QEMU, modify the STM32 UART implementation in QEMU:

1. Locate the QEMU STM32 UART implementation:

   ```bash
   cd tools/qemu
   find . -name "*uart*" | grep stm32
   ```

2. Edit the STM32 UART implementation (e.g., `hw/char/stm32f2xx_usart.c`):

   ```c
   // Include the QEMU bridge header at the top
   #include "qemu_uart_bridge.h"
   
   // In the stm32f2xx_usart_realize function, initialize the bridge
   static void stm32f2xx_usart_realize(DeviceState *dev, Error **errp)
   {
       STM32F2XXUSARTState *s = STM32F2XX_USART(dev);
       
       // Existing code...
       
       // Initialize the bridge with the UART ID and default baudrate
       s->bridge_id = qemu_uart_bridge_init(s->uart_id, 115200, s->chr);
       
       // Rest of existing code...
   }
   
   // In the stm32f2xx_usart_receive function, use the bridge
   static void stm32f2xx_usart_receive(void *opaque, const uint8_t *buf, int size)
   {
       STM32F2XXUSARTState *s = STM32F2XX_USART(opaque);
       
       // Get the UART driver from the bridge
       CustomUARTDriver* driver = qemu_uart_bridge_get_driver(s->bridge_id);
       if (driver) {
           // Use the custom driver to receive data
           for (int i = 0; i < size; i++) {
               custom_uart_receive_byte(driver, buf[i]);
           }
           return;
       }
       
       // Fall back to the original code if the bridge isn't available
       // Original implementation...
   }
   ```

3. Update the STM32F2XX USART state structure to include the bridge ID:

   ```c
   typedef struct STM32F2XXUSARTState {
       // Existing fields...
       
       // Add bridge ID
       int bridge_id;
       
       // Rest of existing fields...
   } STM32F2XXUSARTState;
   ```

### 3. Modify MicroPython UART Implementation

To integrate with MicroPython, modify the STM32 UART implementation:

1. Locate the MicroPython UART implementation:

   ```bash
   cd tools/micropython
   find ports/stm32 -name "*uart*"
   ```

2. Edit the STM32 UART implementation (e.g., `ports/stm32/uart.c`):

   ```c
   // Include the custom UART header at the top
   #include "custom_uart_driver.h"
   
   // In the machine_uart_init function, check if running in QEMU
   STATIC mp_obj_t machine_uart_init_helper(machine_uart_obj_t *self, size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
       // Existing code...
       
       // Check if running in QEMU
       #if defined(MICROPY_QEMU_SIMULATION)
       if (is_qemu_simulation()) {
           // Initialize the custom UART driver
           self->custom_driver = custom_uart_init(self->uart_id, baudrate);
           if (self->custom_driver) {
               // Configure the driver
               custom_uart_configure(self->custom_driver, bits, stop, parity, flow);
               return mp_const_none;
           }
       }
       #endif
       
       // Original implementation for physical hardware
       // Rest of existing code...
   }
   
   // Update the machine_uart_deinit function
   STATIC mp_obj_t machine_uart_deinit(mp_obj_t self_in) {
       machine_uart_obj_t *self = MP_OBJ_TO_PTR(self_in);
       
       #if defined(MICROPY_QEMU_SIMULATION)
       if (self->custom_driver) {
           custom_uart_deinit(self->custom_driver);
           self->custom_driver = NULL;
           return mp_const_none;
       }
       #endif
       
       // Original implementation
       // Rest of existing code...
   }
   ```

3. Update the machine_uart_obj_t structure to include the custom driver:

   ```c
   typedef struct _machine_uart_obj_t {
       // Existing fields...
       
       // Add custom driver
       #if defined(MICROPY_QEMU_SIMULATION)
       CustomUARTDriver* custom_driver;
       #endif
       
       // Rest of existing fields...
   } machine_uart_obj_t;
   ```

4. Add the custom methods to the UART class:

   ```c
   // In ports/stm32/uart.c or a separate file
   
   // Include the MicroPython integration header
   #include "micropython_integration.h"
   
   // In the UART class definition, register the new methods
   STATIC const mp_rom_map_elem_t machine_uart_locals_dict_table[] = {
       // Existing methods...
       
       // Add custom methods when in QEMU mode
       #if defined(MICROPY_QEMU_SIMULATION)
       { MP_ROM_QSTR(MP_QSTR_set_loopback), MP_ROM_PTR(&machine_uart_set_loopback_obj) },
       { MP_ROM_QSTR(MP_QSTR_set_error_simulation), MP_ROM_PTR(&machine_uart_set_error_simulation_obj) },
       { MP_ROM_QSTR(MP_QSTR_set_noise_simulation), MP_ROM_PTR(&machine_uart_set_noise_simulation_obj) },
       { MP_ROM_QSTR(MP_QSTR_start_recording), MP_ROM_PTR(&machine_uart_start_recording_obj) },
       { MP_ROM_QSTR(MP_QSTR_stop_recording), MP_ROM_PTR(&machine_uart_stop_recording_obj) },
       { MP_ROM_QSTR(MP_QSTR_get_errors), MP_ROM_PTR(&machine_uart_get_errors_obj) },
       { MP_ROM_QSTR(MP_QSTR_set_timing_simulation), MP_ROM_PTR(&machine_uart_set_timing_simulation_obj) },
       { MP_ROM_QSTR(MP_QSTR_get_status), MP_ROM_PTR(&machine_uart_get_status_obj) },
       #endif
       
       // Rest of existing methods...
   };
   ```

### 4. Update the Build System

1. Modify the MicroPython STM32 port Makefile to include the custom UART driver:

   ```makefile
   # In ports/stm32/Makefile
   
   # Add QEMU simulation support
   ifeq ($(QEMU_SIMULATION),1)
   CFLAGS_EXTRA += -DMICROPY_QEMU_SIMULATION=1
   SRC_C += \
   	$(PROJECT_DIR)/src/custom_uart_driver.c \
   	$(PROJECT_DIR)/src/micropython_integration.c
   CFLAGS_EXTRA += -I$(PROJECT_DIR)/src
   endif
   ```

2. Modify the QEMU Makefile to include the bridge:

   ```makefile
   # In tools/qemu/Makefile.target or appropriate QEMU build file
   
   # Add the UART bridge
   obj-y += uart-bridge.o
   uart-bridge.o: $(PROJECT_DIR)/src/qemu_uart_bridge.c $(PROJECT_DIR)/src/custom_uart_driver.c
   	$(CC) $(CFLAGS) -c -o $@ $<
   ```

### 5. Configure the Board for QEMU

Update the board configuration for QEMU:

```bash
cd tools/micropython/ports/stm32/boards/STM32F4DISC_QEMU
```

Edit the mpconfigboard.mk file:

```makefile
# Add QEMU simulation support
CFLAGS_EXTRA += -DMICROPY_QEMU_SIMULATION=1
```

### 6. Testing the Integration

1. Build MicroPython with QEMU support:

   ```bash
   cd scripts
   ./build.sh STM32F4DISC_QEMU
   ```

2. Run the UART demo:

   ```bash
   # Copy the demo script to the src directory
   cp src/demo/uart_test.py src/main.py
   
   # Rebuild and run
   ./build.sh STM32F4DISC_QEMU
   ./run_qemu.sh
   ```

3. Verify that the custom UART features work as expected.

## Troubleshooting

### Common Issues

1. **Build errors**: Ensure all paths are correct and the custom UART driver files are included in the build.

2. **QEMU crashes**: Check that the QEMU STM32 UART implementation is correctly modified and the bridge is properly initialized.

3. **MicroPython errors**: Verify that the MicroPython UART implementation is correctly updated and the custom methods are properly registered.

4. **Performance issues**: If you encounter performance problems, try disabling timing simulation or reducing the error/noise rates.

### Debug Logging

To enable debug logging for the custom UART driver:

1. Add debug flags to the build:

   ```makefile
   CFLAGS_EXTRA += -DUART_DEBUG=1
   ```

2. Check the QEMU output for debug messages:

   ```bash
   ./run_qemu.sh 2>&1 | grep "UART"
   ```

## Advanced Usage

### Custom UART Configuration

You can customize the UART driver behavior by modifying the following parameters:

- **Buffer sizes**: Change `UART_TX_BUFFER_SIZE` and `UART_RX_BUFFER_SIZE` in custom_uart_driver.h
- **Error simulation**: Adjust error rates in the Python test script
- **Timing simulation**: Modify the timing parameters for more realistic behavior

### Adding New Features

To add new features to the custom UART driver:

1. Implement the feature in `custom_uart_driver.c`
2. Add the appropriate function declaration to `custom_uart_driver.h`
3. Create a MicroPython binding in `micropython_integration.c`
4. Register the new method in the UART class
5. Test the feature in a MicroPython script

## Reference

### Custom UART Driver API

See the header file `custom_uart_driver.h` for the complete API reference.

### MicroPython UART Extensions

The following methods are added to the MicroPython UART class when running in QEMU:

- `uart.set_loopback(enable)`: Enable or disable loopback mode
- `uart.set_error_simulation(rate)`: Set the error simulation rate (0.0 to 1.0)
- `uart.set_noise_simulation(level)`: Set the noise simulation level (0.0 to 1.0)
- `uart.start_recording(filename)`: Start recording UART traffic to a file
- `uart.stop_recording()`: Stop recording UART traffic
- `uart.get_errors()`: Get the current error flags
- `uart.set_timing_simulation(enable)`: Enable or disable timing simulation
- `uart.get_status()`: Get the current status flags

## Conclusion

This guide provides a comprehensive overview of integrating the custom UART driver with QEMU and MicroPython. By following these steps, you can enhance the UART capabilities in the virtual environment and enable advanced testing and simulation features. 