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

# Check if firmware exists
if [ ! -f "$FIRMWARE" ]; then
    echo "Firmware not found. Run build.sh first."
    exit 1
fi

# Read QEMU arguments from config file
QEMU_ARGS=$(cat "$QEMU_CONFIG" | grep -v '^#' | tr '\n' ' ')

# Replace firmware.bin with the actual path
QEMU_ARGS=$(echo "$QEMU_ARGS" | sed "s|firmware.bin|$FIRMWARE|g")

# Run QEMU
echo "Starting QEMU with arguments: $QEMU_ARGS"
"$QEMU_DIR/build/arm-softmmu/qemu-system-arm" $QEMU_ARGS

echo "QEMU session ended."