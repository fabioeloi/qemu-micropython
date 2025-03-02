/*
 * QEMU UART Bridge for Custom UART Driver - Header
 *
 * This file provides the header declarations for integration between 
 * the custom UART driver and QEMU's character device API.
 */

#ifndef QEMU_UART_BRIDGE_H
#define QEMU_UART_BRIDGE_H

#include <stdint.h>
#include <stdbool.h>

/* Forward declarations to avoid circular dependencies */
typedef struct CharBackend CharBackend;
struct CustomUARTDriver;

/* 
 * Initialize a new UART bridge for QEMU
 *
 * uart_id: The UART ID to use (matching the STM32 UART number)
 * baudrate: The initial baudrate
 * chr: QEMU character backend
 * 
 * Returns: Bridge ID on success, -1 on failure
 */
int qemu_uart_bridge_init(uint32_t uart_id, uint32_t baudrate, CharBackend *chr);

/* 
 * Get the custom UART driver for a bridge
 */
struct CustomUARTDriver* qemu_uart_bridge_get_driver(int bridge_id);

/* 
 * Clean up a UART bridge
 */
void qemu_uart_bridge_deinit(int bridge_id);

#endif /* QEMU_UART_BRIDGE_H */ 