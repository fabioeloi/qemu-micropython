# QEMU STM32 MicroPython Notes

## Overview

This document captures findings and best practices for running MicroPython on an STM32F4 microcontroller emulated in QEMU.

## Findings

### QEMU STM32 Support

QEMU's STM32 emulation has several limitations:

1. **Peripheral Support**: QEMU doesn't fully emulate all STM32F4 peripherals. We consistently see messages like:
   - `stm32_rcc_write: The RCC peripheral only supports enable and reset in QEMU`
   - `Flash Int: unimplemented device read/write`
   - `GPIOA: unimplemented device read/write`

2. **Machine Configuration**: We use the `olimex-stm32-h405` machine type as it's the closest to STM32F4 Discovery board available in QEMU.

3. **Output Challenges**: Getting output from MicroPython in QEMU is challenging due to limited UART emulation.

### Successful Techniques

In our experiments, we found several approaches to maximize compatibility:

1. **Simple C Test Programs**: A basic C program using semihosting for output works reliably in QEMU. This confirms that QEMU's core ARM Cortex-M4 emulation works.

2. **Semihosting**: Semihosting (using the `bkpt 0xAB` instruction) works reliably for output in C programs. For MicroPython, we attempted to use `micropython.asm_thumb` to implement semihosting but had mixed results.

3. **UART Configuration**: Our experiments indicate that direct UART initialization and usage may not be reliable due to QEMU's limited peripheral emulation.

4. **Board Configuration**: We created a custom `STM32F4DISC_QEMU` board configuration for MicroPython that disables hardware features not well-supported by QEMU.

## Best Practices

1. **Simple Programs First**: When troubleshooting QEMU issues, start with the simplest possible programs (like our C test) to verify basic functionality.

2. **Semihosting for Output**: Use semihosting for output when possible, as it's more reliable than emulated UART in QEMU.

3. **QEMU Command-Line Options**:
   - Enable relevant debug options: `-d guest_errors,unimp,semihosting,int`
   - Configure semihosting properly: `-semihosting-config enable=on,target=native`
   - Use the most compatible machine: `-machine olimex-stm32-h405`

4. **MicroPython**: For MicroPython in QEMU:
   - Keep scripts simple
   - Avoid hardware-specific operations when possible
   - Use standard print() functions and rely on MicroPython's internal console handling
   - Implement fallback mechanisms for hardware operations

## Example Code

### C Test with Semihosting Output

```c
#include <stdint.h>

// Semihosting operations
#define SYS_WRITEC 0x03
#define SYS_WRITE0 0x04

// Semihosting call
static inline int semihosting_call(int operation, void *args) {
    register int r0 __asm__("r0") = operation;
    register void *r1 __asm__("r1") = args;
    
    __asm__ volatile (
        "bkpt 0xAB"
        : "=r" (r0)
        : "r" (r0), "r" (r1)
        : "memory"
    );
    
    return r0;
}

// Write a string via semihosting
void sh_puts(const char *s) {
    semihosting_call(SYS_WRITE0, (void*)s);
}

int main(void) {
    sh_puts("Hello from STM32F4 QEMU test!\r\n");
    return 0;
}
```

### MicroPython Script

```python
"""
MicroPython QEMU Demo
Simple test script focused on using UART directly
"""

import time
import machine
import sys

# Setup UART (STM32 usually has UART2 on pins A2/A3)
try:
    uart = machine.UART(2, 115200)  # UART2
    uart.init(115200, bits=8, parity=None, stop=1)
    uart_ok = True
    print("UART initialized successfully")
except Exception as e:
    uart_ok = False
    print("UART initialization failed:", e)

def uart_print(msg):
    """Print to both UART and standard output"""
    print(msg)  # Standard output
    if uart_ok:
        uart.write(msg + '\r\n')  # UART output

# Main application loop
for i in range(10):
    uart_print("Counter: {}".format(i))
    time.sleep(1)
```

## Future Work

1. **GDB Integration**: Connect GDB to QEMU for step-by-step debugging and better insight into execution.

2. **Custom UART Driver**: Implement a custom UART driver in MicroPython specifically optimized for QEMU.

3. **Semihosting Integration**: Better integrate semihosting support into MicroPython for reliable output in QEMU.

4. **Explore Other QEMU Machines**: Try other machine types or create a custom machine definition for better STM32F4 support. 