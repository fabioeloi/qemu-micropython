#include <stdint.h>

// Stack top defined in the linker script (e.g., end of RAM)
extern uint32_t _estack;

// Symbols defined in the linker script for .data and .bss sections
extern uint32_t _sdata;   // Start of .data in RAM
extern uint32_t _edata;   // End of .data in RAM
extern uint32_t _sidata;  // Start of .data initial values in Flash (LMA)
extern uint32_t _sbss;    // Start of .bss in RAM
extern uint32_t _ebss;    // End of .bss in RAM

// Forward declaration of the test runner's main function (from e.g. test_string_utils_runner.c)
int main(void);

// Minimal SystemInit. For QEMU, often not much is needed unless testing
// specific clock-dependent peripherals that require RCC setup.
void SystemInit(void) {
    // Placeholder for any minimal system initialization required before main().
    // For many unit tests not touching complex hardware, this can be empty.
}

// Reset Handler: Entry point for the MCU after reset
void Reset_Handler(void) {
    uint32_t *pSrc, *pDst;

    // Copy the .data section from Flash to RAM
    pSrc = &_sidata; // Source: End of .text in Flash where .data initial values are stored
    pDst = &_sdata;  // Destination: Start of .data in RAM
    while (pDst < &_edata) {
        *pDst++ = *pSrc++;
    }

    // Initialize the .bss section to zero in RAM
    pDst = &_sbss;   // Start of .bss in RAM
    while (pDst < &_ebss) {
        *pDst++ = 0;
    }

    // Call SystemInit (if any specific low-level init is needed, e.g. FPU)
    SystemInit();

    // Call the main function of the test runner
    main();

    // If main() returns (e.g. UnityEnd calls qemu_exit which might not halt immediately,
    // or if qemu_exit is not called), loop indefinitely.
    // qemu_exit via semihosting should terminate QEMU before this loop is hit.
    volatile int i = 0;
    while (1) {
        i++; // Prevent optimization
    }
}

// Default Handler for unconfigured interrupts
void Default_Handler(void) {
    while (1);
}

// Vector Table (Minimal for Cortex-M4)
// It's crucial that this is correctly placed by the linker script at the beginning of FLASH.
__attribute__((section(".isr_vector"), used))
void (*const g_pfnVectors[])(void) = {
    (void (*)(void))&_estack,      // Initial Stack Pointer
    Reset_Handler,                 // Reset Handler
    Default_Handler,               // NMI_Handler
    Default_Handler,               // HardFault_Handler
    Default_Handler,               // MemManage_Handler
    Default_Handler,               // BusFault_Handler
    Default_Handler,               // UsageFault_Handler
    0, 0, 0, 0,                    // Reserved
    Default_Handler,               // SVCall_Handler
    Default_Handler,               // DebugMon_Handler
    0,                             // Reserved
    Default_Handler,               // PendSV_Handler
    Default_Handler,               // SysTick_Handler
    // Add more Default_Handler entries if your MCU expects a longer vector table
    // For basic unit tests, this minimal set is often sufficient.
};
