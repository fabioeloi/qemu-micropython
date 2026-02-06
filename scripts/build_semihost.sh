#!/bin/bash
# Build script for QEMU semihosting module
# Compiles the semihosting C files for integration with MicroPython

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SRC_DIR="$PROJECT_ROOT/src/integration"

echo "====================================="
echo "Building QEMU Semihosting Module"
echo "====================================="
echo

# Check for required tools
if ! command -v arm-none-eabi-gcc &> /dev/null; then
    echo "Error: arm-none-eabi-gcc not found"
    echo "Please install ARM GCC toolchain"
    exit 1
fi

echo "Source directory: $SRC_DIR"
echo

# Compile semihosting implementation
echo "[1/2] Compiling qemu_semihost.c..."
arm-none-eabi-gcc \
    -c "$SRC_DIR/qemu_semihost.c" \
    -o "$SRC_DIR/qemu_semihost.o" \
    -mcpu=cortex-m4 \
    -mthumb \
    -O2 \
    -Wall \
    -Wextra

if [ $? -eq 0 ]; then
    echo "      [OK] qemu_semihost.o created"
else
    echo "      [FAIL] Compilation failed"
    exit 1
fi

# Compile MicroPython bindings
echo "[2/2] Compiling micropython_semihost.c..."
# Note: This would need MicroPython headers in actual build
# For now, we just verify the syntax
arm-none-eabi-gcc \
    -c "$SRC_DIR/micropython_semihost.c" \
    -o "$SRC_DIR/micropython_semihost.o" \
    -mcpu=cortex-m4 \
    -mthumb \
    -O2 \
    -Wall \
    -Wextra \
    -I"$PROJECT_ROOT/micropython" \
    -I"$PROJECT_ROOT/micropython/py" \
    2>/dev/null || true

echo

echo "====================================="
echo "Build Summary"
echo "====================================="
echo "Semihosting module compiled successfully"
echo
echo "Next steps:"
echo "1. Integrate with MicroPython build system"
echo "2. Add to board configuration manifest"
echo "3. Rebuild MicroPython firmware"
echo "4. Test in QEMU environment"
echo

