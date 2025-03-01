#include <stdint.h>

// Semihosting operations
#define SYS_WRITEC 0x03
#define SYS_WRITE0 0x04

// Simple delay function
void delay(int count) {
    volatile int i;
    for (i = 0; i < count; i++) {
        __asm__("nop");
    }
}

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

// Write a character via semihosting
void sh_putc(char c) {
    semihosting_call(SYS_WRITEC, &c);
}

// Write a string via semihosting
void sh_puts(const char *s) {
    semihosting_call(SYS_WRITE0, (void*)s);
}

// Main function
int main(void) {
    // Simple welcome message
    sh_puts("\r\n\r\n**************************\r\n");
    sh_puts("STM32F4 QEMU Test Program\r\n");
    sh_puts("Using Semihosting for Output\r\n");
    sh_puts("**************************\r\n\r\n");
    
    // Blink an LED (simulated via output messages)
    int counter = 0;
    while (counter < 10) {  // Only run 10 iterations
        // Toggle LED (just a delay loop for simulation)
        delay(1000000);
        sh_puts("LED ON  - Counter: ");
        
        // Print counter value as digits
        if (counter == 0) {
            sh_putc('0');
        } else {
            // Convert counter to string
            char digits[10];
            int temp = counter;
            int i = 0;
            
            while (temp > 0) {
                digits[i++] = '0' + (temp % 10);
                temp /= 10;
            }
            
            // Print digits in reverse order
            while (i > 0) {
                sh_putc(digits[--i]);
            }
        }
        
        sh_puts("\r\n");
        
        delay(1000000);
        sh_puts("LED OFF\r\n");
        
        counter++;
    }
    
    sh_puts("\r\nTest complete! Exiting...\r\n");
    
    return 0;
} 