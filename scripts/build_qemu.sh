#!/bin/bash
# Build MicroPython for QEMU STM32 target
set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MICROPYTHON_DIR="$PROJECT_DIR/tools/micropython"
STM32_PORT_DIR="$MICROPYTHON_DIR/ports/stm32"
BUILD_DIR="$PROJECT_DIR/firmware/build"
BOARD="STM32F4DISC_QEMU"

echo "Building MicroPython firmware for $BOARD board with QEMU support..."

# Check if MicroPython repository exists
if [ ! -d "$MICROPYTHON_DIR" ]; then
    echo "MicroPython directory not found. Run setup_env.sh first."
    exit 1
fi

# Create build directory if it doesn't exist
mkdir -p "$BUILD_DIR"

# Make sure our custom UART driver is properly linked
echo "Setting up QEMU integration..."
mkdir -p "$PROJECT_DIR/src/integration"

# Verify the files are there and have correct paths
if [ ! -f "$PROJECT_DIR/src/custom_uart_driver.c" ]; then
    echo "Error: custom_uart_driver.c not found in $PROJECT_DIR/src"
    exit 1
fi

if [ ! -f "$PROJECT_DIR/src/custom_uart_driver.h" ]; then
    echo "Error: custom_uart_driver.h not found in $PROJECT_DIR/src"
    exit 1
fi

if [ ! -f "$PROJECT_DIR/src/integration/qemu_uart_bridge.c" ]; then
    echo "Error: qemu_uart_bridge.c not found in $PROJECT_DIR/src/integration"
    exit 1
fi

if [ ! -f "$PROJECT_DIR/src/integration/micropython_integration.c" ]; then
    echo "Error: micropython_integration.c not found in $PROJECT_DIR/src/integration"
    exit 1
fi

# Prepare Python files for freezing
echo "Preparing Python files..."
"$PROJECT_DIR/scripts/freeze_files.sh" "$BOARD"

# Navigator to the STM32 port directory
cd "$STM32_PORT_DIR"

# Update the Makefile with absolute paths
ESCAPED_PROJECT_DIR=$(echo "$PROJECT_DIR" | sed 's/\//\\\//g')
echo "Setting PROJECT_DIR=$ESCAPED_PROJECT_DIR in Makefile"

# Create a temporary Makefile section for our custom driver
cat > "$STM32_PORT_DIR/custom_uart_section.mk" << EOF
# Add QEMU simulation support
ifeq (\$(QEMU_SIMULATION),1)
CFLAGS_EXTRA += -DMICROPY_QEMU_SIMULATION=1
SRC_C += \\
	$ESCAPED_PROJECT_DIR/src/custom_uart_driver.c \\
	$ESCAPED_PROJECT_DIR/src/integration/micropython_integration.c \\
	$ESCAPED_PROJECT_DIR/src/integration/qemu_uart_bridge.c
CFLAGS_EXTRA += -I$ESCAPED_PROJECT_DIR
endif
EOF

# Check if the section already exists in the Makefile
if ! grep -q "QEMU_SIMULATION" "$STM32_PORT_DIR/Makefile"; then
    # Append the section before the last line
    sed -i '' -e '$i\
# Add QEMU simulation support\
ifeq ($(QEMU_SIMULATION),1)\
CFLAGS_EXTRA += -DMICROPY_QEMU_SIMULATION=1\
SRC_C += \\\
\t$(PROJECT_DIR)/src/custom_uart_driver.c \\\
\t$(PROJECT_DIR)/src/integration/micropython_integration.c \\\
\t$(PROJECT_DIR)/src/integration/qemu_uart_bridge.c\
CFLAGS_EXTRA += -I$(PROJECT_DIR)\
endif\
' "$STM32_PORT_DIR/Makefile"
    echo "Added QEMU simulation section to Makefile"
fi

# Clean previous build
make BOARD=$BOARD clean

# Define PROJECT_DIR for the build
export PROJECT_DIR="$PROJECT_DIR"

# Build the firmware with QEMU simulation enabled
echo "Building with PROJECT_DIR=$PROJECT_DIR"
make BOARD=$BOARD QEMU_SIMULATION=1 -j4

# Check if build succeeded
if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

# Check for split firmware files (common for STM32F4 boards)
if [ -f "build-$BOARD/firmware0.bin" ] && [ -f "build-$BOARD/firmware1.bin" ]; then
    echo "Detected split firmware files. Copying to build directory..."
    cp "build-$BOARD/firmware0.bin" "$BUILD_DIR/"
    cp "build-$BOARD/firmware1.bin" "$BUILD_DIR/"
    
    # Create a combined firmware file for QEMU
    echo "Creating combined firmware for QEMU..."
    cat "build-$BOARD/firmware0.bin" > "$BUILD_DIR/firmware.bin"
    # Padding to 0x20000 (128KB)
    dd if=/dev/zero bs=1 count=$((0x20000 - $(stat -f%z "build-$BOARD/firmware0.bin"))) >> "$BUILD_DIR/firmware.bin" 2>/dev/null
    cat "build-$BOARD/firmware1.bin" >> "$BUILD_DIR/firmware.bin"
    echo "Combined firmware created at $BUILD_DIR/firmware.bin"
else
    # Copy the standard firmware file if it exists
    if [ -f "build-$BOARD/firmware.bin" ]; then
        cp "build-$BOARD/firmware.bin" "$BUILD_DIR/"
    else
        echo "Warning: No firmware bin file found in build directory!"
        exit 1
    fi
fi

# Copy additional build files if they exist
cp "build-$BOARD/firmware.dfu" "$BUILD_DIR/" 2>/dev/null || true
cp "build-$BOARD/firmware.elf" "$BUILD_DIR/" 2>/dev/null || true

echo "Firmware successfully built at $BUILD_DIR/"
echo "Run './scripts/run_qemu.sh' to test the firmware with QEMU." 