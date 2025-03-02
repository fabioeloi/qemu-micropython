#!/bin/bash
# Test the MicroPython UART bindings on QEMU
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC_DIR="$PROJECT_DIR/src"
BUILD_DIR="$PROJECT_DIR/firmware/build"

echo "Testing MicroPython UART bindings in QEMU..."

# Copy the test script to main.py
cp "$SRC_DIR/micropython_uart_test.py" "$SRC_DIR/main.py"

# Build the firmware
echo "Building firmware with UART test..."
"$PROJECT_DIR/scripts/build.sh"

# Run in QEMU
echo "Running test in QEMU..."
"$PROJECT_DIR/scripts/run_qemu.sh"

# Restore original main.py if it exists
if [ -f "$SRC_DIR/main.py.bak" ]; then
    mv "$SRC_DIR/main.py.bak" "$SRC_DIR/main.py"
fi

echo "MicroPython UART test completed" 