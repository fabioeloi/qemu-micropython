#!/bin/bash
# Set up development environment for STM32 QEMU and MicroPython
set -e

echo "Setting up development environment for STM32 QEMU and MicroPython..."

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS_DIR="$PROJECT_DIR/tools"
QEMU_DIR="$TOOLS_DIR/qemu"
MICROPYTHON_DIR="$TOOLS_DIR/micropython"
CONFIG_DIR="$PROJECT_DIR/config"
BOARD="STM32F4DISC"

# Install prerequisites
echo "Installing prerequisites..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    brew update
    brew install wget git python3 cmake pkg-config glib libffi gettext pixman ninja
    brew install --cask gcc-arm-embedded
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    sudo apt-get update
    sudo apt-get install -y build-essential libglib2.0-dev libpixman-1-dev git python3 python3-pip wget
    sudo apt-get install -y gcc-arm-none-eabi libnewlib-arm-none-eabi
fi

# Create directories
mkdir -p "$TOOLS_DIR"
mkdir -p "$CONFIG_DIR/boards/$BOARD"

# Create basic board configuration files if they don't exist
if [ ! -f "$CONFIG_DIR/boards/$BOARD/mpconfigboard.h" ]; then
    echo "Creating basic board configuration files for $BOARD..."
    mkdir -p "$CONFIG_DIR/boards/$BOARD"
    
    # Create mpconfigboard.h
    cat > "$CONFIG_DIR/boards/$BOARD/mpconfigboard.h" << 'EOF'
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
    cat > "$CONFIG_DIR/boards/$BOARD/mpconfigboard.mk" << 'EOF'
MCU_SERIES = f4
CMSIS_MCU = STM32F407xx
AF_FILE = boards/stm32f405_af.csv
LD_FILES = boards/stm32f405.ld boards/common_ifs.ld
TEXT0_ADDR = 0x08000000
TEXT1_ADDR = 0x08020000
EOF

    # Create pins.csv (simplified version)
    cat > "$CONFIG_DIR/boards/$BOARD/pins.csv" << 'EOF'
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

    echo "Basic board configuration files created."
fi

# Clone and build QEMU with STM32 support
if [ ! -d "$QEMU_DIR" ]; then
    echo "Cloning QEMU..."
    git clone https://github.com/qemu/qemu "$QEMU_DIR"
    cd "$QEMU_DIR"
    echo "Configuring QEMU..."
    ./configure --target-list=arm-softmmu --enable-debug
    echo "Building QEMU..."
    make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu)
    echo "QEMU build complete."
else
    echo "QEMU directory already exists, skipping clone."
fi

# Clone and prepare MicroPython
if [ ! -d "$MICROPYTHON_DIR" ]; then
    echo "Cloning MicroPython..."
    git clone https://github.com/micropython/micropython "$MICROPYTHON_DIR"
    cd "$MICROPYTHON_DIR"
    git submodule update --init
else
    echo "MicroPython directory already exists, updating..."
    cd "$MICROPYTHON_DIR"
    git pull
    git submodule update --init
fi

# Explicitly create and copy board configuration to the correct location
echo "Copying board configuration to MicroPython..."
mkdir -p "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD"
cp -v "$CONFIG_DIR/boards/$BOARD/mpconfigboard.h" "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD/"
cp -v "$CONFIG_DIR/boards/$BOARD/mpconfigboard.mk" "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD/"
cp -v "$CONFIG_DIR/boards/$BOARD/pins.csv" "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD/"

# Verify the board files exist
echo "Verifying board configuration files..."
if [ -f "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD/mpconfigboard.h" ] && \
   [ -f "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD/mpconfigboard.mk" ] && \
   [ -f "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD/pins.csv" ]; then
    echo "Board configuration files successfully copied."
else
    echo "Error: Failed to copy all board configuration files."
    exit 1
fi

# Build MicroPython
cd ports/stm32
echo "Building MicroPython for STM32..."
make BOARD="$BOARD" V=1

# Create symlinks to the project
mkdir -p "$PROJECT_DIR/firmware/build"
ln -sf "$MICROPYTHON_DIR/ports/stm32/build-$BOARD/firmware.bin" "$PROJECT_DIR/firmware/build/firmware.bin"

echo "Environment setup complete."
echo "You can now use the build.sh and run_qemu.sh scripts."