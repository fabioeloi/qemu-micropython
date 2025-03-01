#!/bin/bash
# Set up development environment for MicroPython on QEMU project
set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS_DIR="$PROJECT_DIR/tools"
CONFIG_DIR="$PROJECT_DIR/config"
QEMU_DIR="$TOOLS_DIR/qemu"
MICROPYTHON_DIR="$TOOLS_DIR/micropython"
FIRMWARE_DIR="$PROJECT_DIR/firmware"
BUILD_DIR="$FIRMWARE_DIR/build"
BOARD=${1:-"STM32F4DISC_QEMU"}  # Default to QEMU-optimized board

echo "Setting up environment for MicroPython on QEMU with board $BOARD..."

# Create directories
mkdir -p "$TOOLS_DIR" "$BUILD_DIR"

# Clone QEMU repository if it doesn't exist
if [ ! -d "$QEMU_DIR" ]; then
    echo "Cloning QEMU repository..."
    git clone --depth 1 --branch v8.0.0 https://github.com/qemu/qemu.git "$QEMU_DIR"
    
    # Build QEMU
    echo "Building QEMU..."
    cd "$QEMU_DIR"
    ./configure --target-list=arm-softmmu --enable-debug
    make -j4
fi

# Clone MicroPython repository if it doesn't exist
if [ ! -d "$MICROPYTHON_DIR" ]; then
    echo "Cloning MicroPython repository..."
    git clone --depth 1 --branch v1.22.0 https://github.com/micropython/micropython.git "$MICROPYTHON_DIR"
    
    # Set up MicroPython build environment
    echo "Setting up MicroPython build environment..."
    cd "$MICROPYTHON_DIR"
    
    # Update submodules
    git submodule update --init lib/berkeley-db-1.xx
    git submodule update --init lib/micropython-lib
    
    # Build cross-compiler and mpy-cross
    make -C mpy-cross
fi

echo "Environment setup complete."
echo "Next steps:"
echo "1. Run './scripts/build.sh' to build the MicroPython firmware"
echo "2. Run './scripts/run_qemu.sh' to run the firmware in QEMU"