// STM32F4DISC_QEMU board configuration for QEMU environment
// Based on STM32F4DISC but optimized for QEMU emulation

#define MICROPY_HW_BOARD_NAME       "STM32F4DISC_QEMU"
#define MICROPY_HW_MCU_NAME         "STM32F407VG"

// Enable USB for REPL
#define MICROPY_HW_ENABLE_USB       (1)
#define MICROPY_HW_USB_FS           (1)

// UART configuration - UART2 is commonly supported in QEMU
#define MICROPY_HW_UART2_TX         (pin_A2)
#define MICROPY_HW_UART2_RX         (pin_A3)
#define MICROPY_HW_UART_REPL        PYB_UART_2
#define MICROPY_HW_UART_REPL_BAUD   115200

// Disable features not well-supported in QEMU
#define MICROPY_HW_ENABLE_RTC       (0)
#define MICROPY_HW_ENABLE_ADC       (0)
#define MICROPY_HW_ENABLE_DAC       (0)
#define MICROPY_HW_ENABLE_TIMER     (0)
#define MICROPY_HW_ENABLE_SERVO     (0)
#define MICROPY_HW_ENABLE_SDCARD    (0)
#define MICROPY_HW_ENABLE_MMCARD    (0)

// SPI configuration (minimal)
#define MICROPY_HW_ENABLE_SPI       (0)

// I2C configuration (minimal)
#define MICROPY_HW_ENABLE_I2C       (0)

// CAN configuration
#define MICROPY_HW_ENABLE_CAN       (0)

// LEDs - basic configuration for QEMU
#define MICROPY_HW_LED1             (pin_D12) // Green LED
#define MICROPY_HW_LED_ON(pin)      (mp_hal_pin_high(pin))
#define MICROPY_HW_LED_OFF(pin)     (mp_hal_pin_low(pin))

// HSE crystal configuration
#define MICROPY_HW_CLK_PLLM         (8)
#define MICROPY_HW_CLK_PLLN         (336)
#define MICROPY_HW_CLK_PLLP         (RCC_PLLP_DIV2)
#define MICROPY_HW_CLK_PLLQ         (7)
#define MICROPY_HW_CLK_LAST_FREQ    (1)

// Flash storage configuration (simplified for QEMU)
#define MICROPY_HW_ENABLE_INTERNAL_FLASH_STORAGE (0)

// The board has an 8MHz crystal
#define MICROPY_HW_CLK_USE_HSE      (1)
#define MICROPY_HW_CLK_HSE_MHZ      (8)
