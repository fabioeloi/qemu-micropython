#!/bin/bash
# Setup board configuration files for DISCOVERY_F4
set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS_DIR="$PROJECT_DIR/tools"
MICROPYTHON_DIR="$TOOLS_DIR/micropython"
CONFIG_DIR="$PROJECT_DIR/config"
BOARD="DISCOVERY_F4"  # Use the exact name the build system is looking for

echo "Setting up board configuration for $BOARD..."

# Create directories
mkdir -p "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD"
mkdir -p "$CONFIG_DIR/boards/$BOARD"

# Create mpconfigboard.h
cat > "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD/mpconfigboard.h" << 'EOF'
#define MICROPY_HW_BOARD_NAME       "STM32F4DISCOVERY"
#define MICROPY_HW_MCU_NAME         "STM32F407VGT6"

#define MICROPY_HW_ENABLE_RTC       (1)
#define MICROPY_HW_ENABLE_USB       (1)
#define MICROPY_HW_ENABLE_SDCARD    (0)

// UART config
#define MICROPY_HW_UART1_TX         (pin_A9)
#define MICROPY_HW_UART1_RX         (pin_A10)

// I2C buses
#define MICROPY_HW_I2C1_SCL         (pin_B6)
#define MICROPY_HW_I2C1_SDA         (pin_B7)

// SPI buses
#define MICROPY_HW_SPI1_NSS         (pin_A4)
#define MICROPY_HW_SPI1_SCK         (pin_A5)
#define MICROPY_HW_SPI1_MISO        (pin_A6)
#define MICROPY_HW_SPI1_MOSI        (pin_A7)

// USRSW is pulled low. Pressing the button makes the input go high.
#define MICROPY_HW_USRSW_PIN        (pin_A0)
#define MICROPY_HW_USRSW_PULL       (GPIO_NOPULL)
#define MICROPY_HW_USRSW_EXTI_MODE  (GPIO_MODE_IT_RISING)
#define MICROPY_HW_USRSW_PRESSED    (1)

// LEDs
#define MICROPY_HW_LED1             (pin_D14) // Green LED (LD4)
#define MICROPY_HW_LED2             (pin_D12) // Orange LED (LD3)
#define MICROPY_HW_LED3             (pin_D13) // Red LED (LD5)
#define MICROPY_HW_LED4             (pin_D15) // Blue LED (LD6)
#define MICROPY_HW_LED_ON(pin)      (mp_hal_pin_high(pin))
#define MICROPY_HW_LED_OFF(pin)     (mp_hal_pin_low(pin))
EOF

# Create mpconfigboard.mk
cat > "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD/mpconfigboard.mk" << 'EOF'
MCU_SERIES = f4
CMSIS_MCU = STM32F407xx
AF_FILE = boards/stm32f405_af.csv
LD_FILES = boards/stm32f405.ld boards/common_ifs.ld
TEXT0_ADDR = 0x08000000
TEXT1_ADDR = 0x08020000
EOF

# Create pins.csv
cat > "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD/pins.csv" << 'EOF'
D0,PA0
D1,PA1
D2,PA2
D3,PA3
D4,PA4
D5,PA5
D6,PA6
D7,PA7
D8,PA8
D9,PA9
D10,PA10
D11,PA11
D12,PA12
D13,PA13
D14,PA14
D15,PA15
EOF

# Verify the board files exist
echo "Verifying board configuration files..."
if [ -f "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD/mpconfigboard.h" ] && \
   [ -f "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD/mpconfigboard.mk" ] && \
   [ -f "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD/pins.csv" ]; then
    echo "Board configuration files successfully created for $BOARD."
    echo "You can now build MicroPython with './scripts/build.sh'"
else
    echo "Error: Failed to create all board configuration files."
    exit 1
fi
