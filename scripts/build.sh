#!/bin/bash
# Build MicroPython for STM32 target
set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MICROPYTHON_DIR="$PROJECT_DIR/tools/micropython"
STM32_PORT_DIR="$MICROPYTHON_DIR/ports/stm32"
BUILD_DIR="$PROJECT_DIR/firmware/build"
BOARD=${1:-"STM32F4DISC_QEMU"}

echo "Building MicroPython firmware for $BOARD board..."

# Check if MicroPython repository exists
if [ ! -d "$MICROPYTHON_DIR" ]; then
    echo "MicroPython directory not found. Run setup_env.sh first."
    exit 1
fi

# Create build directory if it doesn't exist
mkdir -p "$BUILD_DIR"

# Prepare Python files for freezing
echo "Preparing Python files..."
"$PROJECT_DIR/scripts/freeze_files.sh" "$BOARD"

# Navigate to the STM32 port directory
cd "$STM32_PORT_DIR"

# Clean previous build
make BOARD=$BOARD clean

# Build the firmware
make BOARD=$BOARD -j4

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