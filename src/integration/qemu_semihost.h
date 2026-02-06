/*
 * QEMU Semihosting Support for MicroPython
 * 
 * Provides console output capabilities using ARM semihosting
 * when running MicroPython firmware in QEMU environments.
 */

#ifndef QEMU_SEMIHOST_H
#define QEMU_SEMIHOST_H

#include <stddef.h>
#include <stdbool.h>

/* Initialize semihosting subsystem */
void qemu_semihost_init(void);

/* Write string to semihosting console */
int qemu_semihost_write_string(const char *text);

/* Write single character to semihosting console */
int qemu_semihost_write_char(char ch);

/* Check if semihosting is available */
bool qemu_semihost_is_available(void);

#endif /* QEMU_SEMIHOST_H */
