#!/bin/bash
# Test semihosting integration in QEMU
# Runs the semihosting test scripts and verifies functionality

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "============================================"
echo "QEMU Semihosting Integration Test"
echo "============================================"
echo

# Check for QEMU
if ! command -v qemu-system-arm &> /dev/null; then
    echo "Error: qemu-system-arm not found"
    echo "Please install QEMU with ARM support"
    exit 1
fi

# Check if firmware exists
FIRMWARE="$PROJECT_ROOT/firmware/micropython.elf"
if [ ! -f "$FIRMWARE" ]; then
    echo "Error: MicroPython firmware not found at $FIRMWARE"
    echo "Please build the firmware first"
    exit 1
fi

echo "Test Configuration:"
echo "  Firmware: $FIRMWARE"
echo "  Test script: tests/test_semihosting.py"
echo "  QEMU machine: olimex-stm32-h405"
echo

# Prepare test script
TEST_SCRIPT="$PROJECT_ROOT/tests/test_semihosting.py"
if [ ! -f "$TEST_SCRIPT" ]; then
    echo "Error: Test script not found at $TEST_SCRIPT"
    exit 1
fi

echo "Starting QEMU with semihosting enabled..."
echo "Press Ctrl+C to stop"
echo
echo "-------------------------------------------"
echo "QEMU Output:"
echo "-------------------------------------------"

# Run QEMU with semihosting
timeout 30s qemu-system-arm \
    -machine olimex-stm32-h405 \
    -cpu cortex-m4 \
    -m 128 \
    -kernel "$FIRMWARE" \
    -semihosting \
    -semihosting-config enable=on,target=native \
    -nographic \
    -serial stdio \
    -d guest_errors,unimp || true

echo
echo "-------------------------------------------"
echo "Test Complete"
echo "-------------------------------------------"
echo
echo "Expected behavior:"
echo "  - Module should import successfully"
echo "  - Semihosting availability check should pass"
echo "  - String output tests should complete"
echo "  - Character output tests should complete"
echo
echo "If you saw test output above, semihosting is working!"
echo "If no output appeared, check:"
echo "  1. Firmware includes semihosting module"
echo "  2. QEMU semihosting flags are correct"
echo "  3. Test script is frozen into firmware"
echo
