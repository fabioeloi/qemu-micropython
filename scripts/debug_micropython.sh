#!/bin/bash
# Debug MicroPython in QEMU with GDB support

set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS_DIR="$PROJECT_DIR/tools"
QEMU_DIR="$TOOLS_DIR/qemu"
CONFIG_DIR="$PROJECT_DIR/config"
BUILD_DIR="$PROJECT_DIR/firmware/build"
FIRMWARE="$BUILD_DIR/firmware.bin"
GDB_PORT=1234
LOG_FILE="$PROJECT_DIR/debug_log.txt"

# Check dependencies
if ! command -v arm-none-eabi-gdb &> /dev/null; then
    echo "Error: arm-none-eabi-gdb not found. Please install ARM toolchain."
    exit 1
fi

# Find QEMU executable
if [ -f "$QEMU_DIR/build/arm-softmmu/qemu-system-arm" ]; then
    QEMU_PATH="$QEMU_DIR/build/arm-softmmu/qemu-system-arm"
elif [ -f "$QEMU_DIR/build/qemu-system-arm" ]; then
    QEMU_PATH="$QEMU_DIR/build/qemu-system-arm"
else
    echo "Error: QEMU executable not found."
    exit 1
fi

# Check if firmware exists
if [ ! -f "$FIRMWARE" ]; then
    if [ -f "$BUILD_DIR/firmware0.bin" ] && [ -f "$BUILD_DIR/firmware1.bin" ]; then
        echo "Found split firmware files. Creating combined firmware for QEMU..."
        cat "$BUILD_DIR/firmware0.bin" > "$FIRMWARE"
        dd if=/dev/zero bs=1 count=$((0x20000 - $(stat -f%z "$BUILD_DIR/firmware0.bin"))) >> "$FIRMWARE" 2>/dev/null
        cat "$BUILD_DIR/firmware1.bin" >> "$FIRMWARE"
    else
        echo "Error: No firmware found. Please build first."
        exit 1
    fi
fi

# Create debug directory if it doesn't exist
mkdir -p "$PROJECT_DIR/debug"

# Copy GDB init file to debug directory
cp "$CONFIG_DIR/gdb/gdbinit" "$PROJECT_DIR/debug/.gdbinit"

# Start QEMU in the background
echo "Starting QEMU with GDB server on port $GDB_PORT..."
$QEMU_PATH \
    -machine olimex-stm32-h405 \
    -cpu cortex-m4 \
    -m 128K \
    -kernel "$FIRMWARE" \
    -serial stdio \
    -monitor none \
    -nographic \
    -S \
    -s \
    -d guest_errors,unimp,exec \
    -semihosting-config enable=on,target=native \
    -semihosting \
    2>"$LOG_FILE" &

QEMU_PID=$!

# Give QEMU a moment to start
sleep 1

# Check if QEMU is running
if ! kill -0 $QEMU_PID 2>/dev/null; then
    echo "Error: QEMU failed to start. Check $LOG_FILE for details."
    exit 1
fi

echo "QEMU started successfully (PID: $QEMU_PID)"
echo "Starting GDB..."

# Start GDB with our init file
cd "$PROJECT_DIR"
arm-none-eabi-gdb -x debug/.gdbinit

# Clean up QEMU when GDB exits
kill $QEMU_PID 2>/dev/null || true

echo "Debug session ended." 