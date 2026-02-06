/*
 * QEMU Semihosting Implementation
 * 
 * Implements ARM semihosting protocol for console I/O
 * This allows MicroPython running in QEMU to produce output
 * via the host's console using ARM's standard semihosting mechanism.
 */

#include "qemu_semihost.h"
#include <stdint.h>
#include <string.h>

/* ARM Semihosting operation codes */
#define SEMIHOST_OP_WRITE_CHAR    0x03
#define SEMIHOST_OP_WRITE_STRING  0x04

/* State tracking */
static bool semihost_initialized = false;
static bool semihost_available = true;

/*
 * Perform ARM semihosting call using breakpoint instruction
 * Parameters:
 *   - operation: Semihosting operation code
 *   - parameter: Pointer to operation-specific parameter
 * Returns: Operation result code
 */
static inline int perform_semihost_call(int operation, void *parameter) {
    register int op_reg __asm__("r0") = operation;
    register void *param_reg __asm__("r1") = parameter;
    register int result_reg __asm__("r0");
    
    __asm__ volatile (
        "bkpt #0xAB\n"
        : "=r" (result_reg)
        : "r" (op_reg), "r" (param_reg)
        : "memory"
    );
    
    return result_reg;
}

void qemu_semihost_init(void) {
    if (!semihost_initialized) {
        semihost_initialized = true;
        /* Test if semihosting works by attempting a null operation */
        /* In a real scenario, we'd test this more carefully */
    }
}

int qemu_semihost_write_char(char ch) {
    if (!semihost_available) {
        return -1;
    }
    
    return perform_semihost_call(SEMIHOST_OP_WRITE_CHAR, &ch);
}

int qemu_semihost_write_string(const char *text) {
    if (!semihost_available || text == NULL) {
        return -1;
    }
    
    return perform_semihost_call(SEMIHOST_OP_WRITE_STRING, (void*)text);
}

bool qemu_semihost_is_available(void) {
    return semihost_available;
}
