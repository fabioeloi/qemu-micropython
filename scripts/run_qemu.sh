#!/bin/bash
# Run MicroPython firmware in QEMU STM32 emulator
set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS_DIR="$PROJECT_DIR/tools"
QEMU_DIR="$TOOLS_DIR/qemu"
CONFIG_DIR="$PROJECT_DIR/config"
BUILD_DIR="$PROJECT_DIR/firmware/build"
FIRMWARE="$BUILD_DIR/firmware.bin"
BOARD=${1:-"stm32f4-discovery"}
LOG_FILE="$PROJECT_DIR/qemu_log.txt"

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

# Create a log file for QEMU output
echo "QEMU output will be logged to $LOG_FILE"

# Kill any existing QEMU instances to avoid conflicts
pkill -f qemu-system-arm 2>/dev/null || true
sleep 1

# Run QEMU with enhanced debugging and semihosting
echo "Starting QEMU with enhanced configuration..."
"$QEMU_PATH" \
    -machine olimex-stm32-h405 \
    -cpu cortex-m4 \
    -m 128K \
    -kernel "$FIRMWARE" \
    -serial stdio \
    -monitor none \
    -nographic \
    -d guest_errors,unimp,semihosting,int \
    -semihosting-config enable=on,target=native,arg=test \
    -semihosting \
    2>&1 | tee "$LOG_FILE"

echo "QEMU session ended."