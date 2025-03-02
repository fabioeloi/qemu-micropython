/*
 * MicroPython integration for custom UART driver
 *
 * This file provides Python bindings for the enhanced features of
 * the custom UART driver used in QEMU environments.
 */

#include <stdio.h>
#include <string.h>
#include <stdbool.h>

#include "py/runtime.h"
#include "py/mphal.h"
#include "py/objstr.h"
#include "py/mperrno.h"

#include "custom_uart_driver.h"

// External references to the MicroPython UART object
// These would come from the actual MicroPython implementation
extern const mp_obj_type_t machine_uart_type;
typedef struct _machine_uart_obj_t machine_uart_obj_t;

// Forward declaration of the helper function to get the CustomUARTDriver from a UART object
static CustomUARTDriver* get_uart_driver(mp_obj_t uart_obj);

//-----------------------------------------------------------------------
// set_loopback method
//-----------------------------------------------------------------------
STATIC mp_obj_t machine_uart_set_loopback(mp_obj_t self_in, mp_obj_t enable_in) {
    CustomUARTDriver* driver = get_uart_driver(self_in);
    if (driver == NULL) {
        mp_raise_ValueError(MP_ERROR_TEXT("UART driver not initialized or not in QEMU mode"));
        return mp_const_none;
    }
    
    bool enable = mp_obj_is_true(enable_in);
    custom_uart_set_loopback(driver, enable);
    
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(machine_uart_set_loopback_obj, machine_uart_set_loopback);

//-----------------------------------------------------------------------
// set_error_simulation method
//-----------------------------------------------------------------------
STATIC mp_obj_t machine_uart_set_error_simulation(mp_obj_t self_in, mp_obj_t rate_in) {
    CustomUARTDriver* driver = get_uart_driver(self_in);
    if (driver == NULL) {
        mp_raise_ValueError(MP_ERROR_TEXT("UART driver not initialized or not in QEMU mode"));
        return mp_const_none;
    }
    
    mp_float_t rate = mp_obj_get_float(rate_in);
    if (rate < 0.0f || rate > 1.0f) {
        mp_raise_ValueError(MP_ERROR_TEXT("Error rate must be between 0.0 and 1.0"));
        return mp_const_none;
    }
    
    custom_uart_set_error_simulation(driver, (float)rate);
    
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(machine_uart_set_error_simulation_obj, machine_uart_set_error_simulation);

//-----------------------------------------------------------------------
// set_noise_simulation method
//-----------------------------------------------------------------------
STATIC mp_obj_t machine_uart_set_noise_simulation(mp_obj_t self_in, mp_obj_t level_in) {
    CustomUARTDriver* driver = get_uart_driver(self_in);
    if (driver == NULL) {
        mp_raise_ValueError(MP_ERROR_TEXT("UART driver not initialized or not in QEMU mode"));
        return mp_const_none;
    }
    
    mp_float_t level = mp_obj_get_float(level_in);
    if (level < 0.0f || level > 1.0f) {
        mp_raise_ValueError(MP_ERROR_TEXT("Noise level must be between 0.0 and 1.0"));
        return mp_const_none;
    }
    
    custom_uart_set_noise_simulation(driver, (float)level);
    
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(machine_uart_set_noise_simulation_obj, machine_uart_set_noise_simulation);

//-----------------------------------------------------------------------
// start_recording method
//-----------------------------------------------------------------------
STATIC mp_obj_t machine_uart_start_recording(mp_obj_t self_in, mp_obj_t filename_in) {
    CustomUARTDriver* driver = get_uart_driver(self_in);
    if (driver == NULL) {
        mp_raise_ValueError(MP_ERROR_TEXT("UART driver not initialized or not in QEMU mode"));
        return mp_const_none;
    }
    
    const char *filename = mp_obj_str_get_str(filename_in);
    bool success = custom_uart_start_recording(driver, filename);
    
    if (!success) {
        mp_raise_OSError(MP_EIO);
        return mp_const_none;
    }
    
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(machine_uart_start_recording_obj, machine_uart_start_recording);

//-----------------------------------------------------------------------
// stop_recording method
//-----------------------------------------------------------------------
STATIC mp_obj_t machine_uart_stop_recording(mp_obj_t self_in) {
    CustomUARTDriver* driver = get_uart_driver(self_in);
    if (driver == NULL) {
        mp_raise_ValueError(MP_ERROR_TEXT("UART driver not initialized or not in QEMU mode"));
        return mp_const_none;
    }
    
    custom_uart_stop_recording(driver);
    
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(machine_uart_stop_recording_obj, machine_uart_stop_recording);

//-----------------------------------------------------------------------
// get_errors method
//-----------------------------------------------------------------------
STATIC mp_obj_t machine_uart_get_errors(mp_obj_t self_in) {
    CustomUARTDriver* driver = get_uart_driver(self_in);
    if (driver == NULL) {
        mp_raise_ValueError(MP_ERROR_TEXT("UART driver not initialized or not in QEMU mode"));
        return mp_const_none;
    }
    
    uint32_t errors = custom_uart_get_errors(driver);
    
    return mp_obj_new_int(errors);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(machine_uart_get_errors_obj, machine_uart_get_errors);

//-----------------------------------------------------------------------
// set_timing_simulation method
//-----------------------------------------------------------------------
STATIC mp_obj_t machine_uart_set_timing_simulation(mp_obj_t self_in, mp_obj_t enable_in) {
    CustomUARTDriver* driver = get_uart_driver(self_in);
    if (driver == NULL) {
        mp_raise_ValueError(MP_ERROR_TEXT("UART driver not initialized or not in QEMU mode"));
        return mp_const_none;
    }
    
    bool enable = mp_obj_is_true(enable_in);
    custom_uart_set_timing_simulation(driver, enable);
    
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(machine_uart_set_timing_simulation_obj, machine_uart_set_timing_simulation);

//-----------------------------------------------------------------------
// get_status method
//-----------------------------------------------------------------------
STATIC mp_obj_t machine_uart_get_status(mp_obj_t self_in) {
    CustomUARTDriver* driver = get_uart_driver(self_in);
    if (driver == NULL) {
        mp_raise_ValueError(MP_ERROR_TEXT("UART driver not initialized or not in QEMU mode"));
        return mp_const_none;
    }
    
    uint32_t status = custom_uart_get_status(driver);
    
    return mp_obj_new_int(status);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(machine_uart_get_status_obj, machine_uart_get_status);

//-----------------------------------------------------------------------
// Helper function to get the driver instance from a MicroPython UART object
//-----------------------------------------------------------------------
static CustomUARTDriver* get_uart_driver(mp_obj_t uart_obj) {
    // Verify that the object is a UART object
    if (!mp_obj_is_type(uart_obj, &machine_uart_type)) {
        return NULL;
    }
    
    // In a real implementation, we would extract the driver instance 
    // from the machine_uart_obj_t structure.
    // For now, this is just a placeholder - the actual implementation
    // would depend on how the machine_uart_obj_t is structured.
    
    // This is a simplified example:
    // machine_uart_obj_t *uart = MP_OBJ_TO_PTR(uart_obj);
    // return (CustomUARTDriver*)uart->driver;
    
    // For testing/demonstration purposes:
    static CustomUARTDriver* test_driver = NULL;
    if (test_driver == NULL) {
        // Initialize a test driver for development
        test_driver = custom_uart_init(2, 115200);
    }
    return test_driver;
}

//-----------------------------------------------------------------------
// Register the new methods with the MicroPython UART class
//-----------------------------------------------------------------------
void custom_uart_init_module(void) {
    // This function would be called during MicroPython port initialization
    // to register the new methods with the machine.UART class.
    
    // Example of how to add methods to an existing class:
    // mp_obj_t uart_class = (mp_obj_t)&machine_uart_type;
    // mp_store_attr(uart_class, MP_QSTR_set_loopback, (mp_obj_t)&machine_uart_set_loopback_obj);
    // mp_store_attr(uart_class, MP_QSTR_set_error_simulation, (mp_obj_t)&machine_uart_set_error_simulation_obj);
    // ... register other methods ...
} 