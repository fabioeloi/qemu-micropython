#!/bin/bash
# Run MicroPython firmware in QEMU STM32 emulator
set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS_DIR="$PROJECT_DIR/tools"
QEMU_DIR="$TOOLS_DIR/qemu"
CONFIG_DIR="$PROJECT_DIR/config"
BUILD_DIR="$PROJECT_DIR/firmware/build"
QEMU_CONFIG="$CONFIG_DIR/qemu/stm32f4.cfg"
FIRMWARE="$BUILD_DIR/firmware.bin"
BOARD=${1:-"stm32f4-discovery"}

echo "Running MicroPython on QEMU STM32 emulator ($BOARD)..."

# Check if QEMU is available
if [ ! -d "$QEMU_DIR" ]; then
    echo "QEMU directory not found. Run setup_env.sh first."
    exit 1
fi

# Check if firmware exists, if not check for split firmware
if [ ! -f "$FIRMWARE" ]; then
    if [ -f "$BUILD_DIR/firmware0.bin" ] && [ -f "$BUILD_DIR/firmware1.bin" ]; then
        echo "Found split firmware files. Creating combined firmware for QEMU..."
        # Create a combined firmware file for QEMU
        # In STM32F4, firmware0.bin is typically placed at address 0x8000000 and 
        # firmware1.bin at address 0x8020000
        cat "$BUILD_DIR/firmware0.bin" > "$FIRMWARE"
        # Padding to 0x20000 (128KB)
        dd if=/dev/zero bs=1 count=$((0x20000 - $(stat -f%z "$BUILD_DIR/firmware0.bin"))) >> "$FIRMWARE" 2>/dev/null
        cat "$BUILD_DIR/firmware1.bin" >> "$FIRMWARE"
        echo "Combined firmware created at $FIRMWARE"
    else
        echo "Firmware not found. Run build.sh first."
        echo "Looking for either $FIRMWARE or split firmware files ($BUILD_DIR/firmware0.bin and $BUILD_DIR/firmware1.bin)"
        exit 1
    fi
fi

# Read QEMU arguments from config file
QEMU_ARGS=$(cat "$QEMU_CONFIG" 2>/dev/null | grep -v '^#' | tr '\n' ' ')
if [ -z "$QEMU_ARGS" ]; then
    echo "QEMU config file not found or empty. Using default configuration."
    QEMU_ARGS="-M stm32f4-discovery -nographic -monitor null -serial stdio -kernel $FIRMWARE"
else
    # Replace firmware.bin with the actual path
    QEMU_ARGS=$(echo "$QEMU_ARGS" | sed "s|firmware.bin|$FIRMWARE|g")
fi

# Run QEMU
echo "Starting QEMU with arguments: $QEMU_ARGS"
# Look for the qemu executable in different possible locations
if [ -f "$QEMU_DIR/build/arm-softmmu/qemu-system-arm" ]; then
    QEMU_PATH="$QEMU_DIR/build/arm-softmmu/qemu-system-arm"
elif [ -f "$QEMU_DIR/build/qemu-system-arm" ]; then
    QEMU_PATH="$QEMU_DIR/build/qemu-system-arm"
else
    echo "Error: QEMU executable not found in expected locations."
    echo "Checked:"
    echo " - $QEMU_DIR/build/arm-softmmu/qemu-system-arm"
    echo " - $QEMU_DIR/build/qemu-system-arm"
    exit 1
fi

"$QEMU_PATH" $QEMU_ARGS

echo "QEMU session ended."