#!/bin/bash
# Build and run the STM32F4 test program in QEMU
set -e

echo "Building and running STM32F4 test program..."

# Check if arm-none-eabi-gcc is installed
if ! command -v arm-none-eabi-gcc &> /dev/null; then
    echo "Error: arm-none-eabi-gcc not found. Please install ARM toolchain."
    exit 1
fi

# Check if QEMU is installed
if ! command -v qemu-system-arm &> /dev/null; then
    echo "Error: qemu-system-arm not found."
    echo "Using project's QEMU if available..."
    if [ -f "../tools/qemu/build/qemu-system-arm" ]; then
        QEMU_PATH="../tools/qemu/build/qemu-system-arm"
    elif [ -f "../tools/qemu/build/arm-softmmu/qemu-system-arm" ]; then
        QEMU_PATH="../tools/qemu/build/arm-softmmu/qemu-system-arm"
    else
        echo "QEMU not found. Please install QEMU or run setup_env.sh first."
        exit 1
    fi
else
    QEMU_PATH="qemu-system-arm"
fi

# Build the test program
echo "Building test program..."
make clean
make

# Check if build was successful
if [ ! -f "simple_test.bin" ]; then
    echo "Build failed. No binary produced."
    exit 1
fi

# Run in QEMU
echo "Running in QEMU..."
echo "Output will be printed below. Press Ctrl+A, X to exit QEMU."
echo "---------------------------------------------------------"

$QEMU_PATH \
    -machine olimex-stm32-h405 \
    -cpu cortex-m4 \
    -m 128K \
    -kernel simple_test.bin \
    -serial stdio \
    -monitor none \
    -nographic \
    -d guest_errors,unimp \
    -semihosting-config enable=on,target=native \
    -semihosting

echo "---------------------------------------------------------"
echo "QEMU session ended." 