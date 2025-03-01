#include <stdint.h>

// Stack pointer
extern uint32_t _estack;

// Defined in linker script
extern uint32_t _sdata;
extern uint32_t _edata;
extern uint32_t _sidata;
extern uint32_t _sbss;
extern uint32_t _ebss;

// Forward declaration of the main function
int main(void);

void SystemInit(void);

// Reset handler
void Reset_Handler(void) {
    // Initialize data section
    uint32_t *pSrc = &_sidata;
    uint32_t *pDst = &_sdata;
    
    while (pDst < &_edata) {
        *pDst++ = *pSrc++;
    }
    
    // Clear BSS section
    pDst = &_sbss;
    while (pDst < &_ebss) {
        *pDst++ = 0;
    }
    
    // Call system initialization
    SystemInit();
    
    // Call the main function
    main();
    
    // Infinite loop if main returns
    while (1);
}

// System initialization function
void SystemInit(void) {
    // Basic system setup for STM32F4
    // For QEMU test, we're keeping this minimal
}

// Default handler for all interrupts
void Default_Handler(void) {
    while (1);
}

// Vector table
__attribute__((section(".isr_vector")))
void (*const g_pfnVectors[])(void) = {
    (void (*)(void))&_estack,  // Stack pointer
    Reset_Handler,             // Reset handler
    Default_Handler,           // NMI handler
    Default_Handler,           // Hard fault handler
    Default_Handler,           // Memory management fault
    Default_Handler,           // Bus fault
    Default_Handler,           // Usage fault
    0, 0, 0, 0,                // Reserved
    Default_Handler,           // SVCall
    Default_Handler,           // Debug monitor
    0,                         // Reserved
    Default_Handler,           // PendSV
    Default_Handler,           // SysTick
    
    // External interrupts (simplified)
    Default_Handler,           // Window Watchdog
    Default_Handler,           // PVD through EXTI Line detection
    Default_Handler,           // Tamper and TimeStamp
    Default_Handler,           // RTC Wakeup
    Default_Handler,           // FLASH
    Default_Handler,           // RCC
    Default_Handler,           // EXTI Line0
    Default_Handler,           // EXTI Line1
    Default_Handler,           // EXTI Line2
    Default_Handler,           // EXTI Line3
    Default_Handler,           // EXTI Line4
    Default_Handler,           // DMA1 Stream0
    Default_Handler,           // DMA1 Stream1
    Default_Handler,           // DMA1 Stream2
    Default_Handler,           // DMA1 Stream3
    Default_Handler,           // DMA1 Stream4
}; 