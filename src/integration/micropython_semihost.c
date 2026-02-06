/*
 * MicroPython Bindings for QEMU Semihosting
 * 
 * Exposes semihosting functionality to Python code
 * Provides: qemu_console module with print_text() and print_char() functions
 */

#include "py/runtime.h"
#include "py/mphal.h"
#include "py/objstr.h"
#include "qemu_semihost.h"

/* Module initialization flag */
static bool module_initialized = false;

/*
 * Python: qemu_console.print_text(text)
 * Write a string to QEMU console via semihosting
 */
STATIC mp_obj_t qemu_console_print_text(mp_obj_t text_obj) {
    /* Ensure initialization */
    if (!module_initialized) {
        qemu_semihost_init();
        module_initialized = true;
    }
    
    /* Extract string from Python object */
    const char *text_str = mp_obj_str_get_str(text_obj);
    
    /* Perform semihosting write */
    int result = qemu_semihost_write_string(text_str);
    
    if (result < 0) {
        mp_raise_OSError(MP_EIO);
    }
    
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(qemu_console_print_text_obj, qemu_console_print_text);

/*
 * Python: qemu_console.print_char(ch)
 * Write a single character to QEMU console via semihosting
 */
STATIC mp_obj_t qemu_console_print_char(mp_obj_t char_obj) {
    /* Ensure initialization */
    if (!module_initialized) {
        qemu_semihost_init();
        module_initialized = true;
    }
    
    /* Get character from argument */
    mp_int_t char_val = mp_obj_get_int(char_obj);
    
    if (char_val < 0 || char_val > 255) {
        mp_raise_ValueError(MP_ERROR_TEXT("Character value must be 0-255"));
    }
    
    /* Perform semihosting write */
    char ch = (char)char_val;
    int result = qemu_semihost_write_char(ch);
    
    if (result < 0) {
        mp_raise_OSError(MP_EIO);
    }
    
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(qemu_console_print_char_obj, qemu_console_print_char);

/*
 * Python: qemu_console.available()
 * Check if semihosting is available
 */
STATIC mp_obj_t qemu_console_available(void) {
    bool avail = qemu_semihost_is_available();
    return mp_obj_new_bool(avail);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(qemu_console_available_obj, qemu_console_available);

/* Module global table */
STATIC const mp_rom_map_elem_t qemu_console_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_qemu_console) },
    { MP_ROM_QSTR(MP_QSTR_print_text), MP_ROM_PTR(&qemu_console_print_text_obj) },
    { MP_ROM_QSTR(MP_QSTR_print_char), MP_ROM_PTR(&qemu_console_print_char_obj) },
    { MP_ROM_QSTR(MP_QSTR_available), MP_ROM_PTR(&qemu_console_available_obj) },
};
STATIC MP_DEFINE_CONST_DICT(qemu_console_module_globals, qemu_console_module_globals_table);

/* Module definition */
const mp_obj_module_t qemu_console_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&qemu_console_module_globals,
};

/* Register module with MicroPython */
MP_REGISTER_MODULE(MP_QSTR_qemu_console, qemu_console_module);
