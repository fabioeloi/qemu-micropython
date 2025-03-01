#!/bin/bash
# Build MicroPython firmware for STM32
set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS_DIR="$PROJECT_DIR/tools"
MICROPYTHON_DIR="$TOOLS_DIR/micropython"
SRC_DIR="$PROJECT_DIR/src"
CONFIG_DIR="$PROJECT_DIR/config"
BUILD_DIR="$PROJECT_DIR/firmware/build"
BOARD="STM32F4DISC"  # Using STM32F4DISC which has the necessary config files

# Ensure the BOARD variable is used and not overridden
export BOARD

echo "Debug: BOARD variable at script start: $BOARD"

# Look for any environment variables that might be overriding our BOARD setting
echo "Debug: Environment variables:"
env | grep -i board

echo "Building MicroPython firmware for STM32 ($BOARD)..."

# Check if MicroPython is available
if [ ! -d "$MICROPYTHON_DIR" ]; then
    echo "MicroPython directory not found. Run setup_env.sh first."
    exit 1
fi

# Print debug info
echo "Debug: Using board name: $BOARD"
echo "Debug: MicroPython dir: $MICROPYTHON_DIR"
echo "Debug: Looking for board config in: $MICROPYTHON_DIR/ports/stm32/boards/$BOARD"

# Check if board directory exists
if [ ! -d "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD" ]; then
    echo "Error: Board directory not found at $MICROPYTHON_DIR/ports/stm32/boards/$BOARD"
    echo "Available boards:"
    ls -la "$MICROPYTHON_DIR/ports/stm32/boards/"
    exit 1
fi

# Copy our manifest file if it exists
if [ -f "$CONFIG_DIR/micropython/manifest.py" ]; then
    mkdir -p "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD"
    cp "$CONFIG_DIR/micropython/manifest.py" "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD/"
fi

# Copy our source files to the MicroPython src directory
if [ -d "$SRC_DIR/lib" ]; then
    mkdir -p "$MICROPYTHON_DIR/ports/stm32/modules"
    cp -r "$SRC_DIR/lib/"* "$MICROPYTHON_DIR/ports/stm32/modules/"
fi

# Copy main.py to the filesystem
if [ -f "$SRC_DIR/main.py" ]; then
    cp "$SRC_DIR/main.py" "$MICROPYTHON_DIR/ports/stm32/"
fi

# Create the build directory before starting
mkdir -p "$BUILD_DIR"

# Build MicroPython with explicit board name
cd "$MICROPYTHON_DIR/ports/stm32"
echo "Debug: Current BOARD value before make: $BOARD"
echo "Cleaning previous build for board: $BOARD"
make clean BOARD=$BOARD V=1
echo "Building firmware for board: $BOARD"
make V=1 BOARD=$BOARD

# Copy the firmware to our build directory
mkdir -p "$BUILD_DIR"

# Check for split or single firmware binary
if [ -f "$MICROPYTHON_DIR/ports/stm32/build-$BOARD/firmware.bin" ]; then
    # Single firmware file approach
    cp "$MICROPYTHON_DIR/ports/stm32/build-$BOARD/firmware.bin" "$BUILD_DIR/"
    echo "Copied firmware.bin to build directory."
elif [ -f "$MICROPYTHON_DIR/ports/stm32/build-$BOARD/firmware0.bin" ] && [ -f "$MICROPYTHON_DIR/ports/stm32/build-$BOARD/firmware1.bin" ]; then
    # Split firmware approach
    cp "$MICROPYTHON_DIR/ports/stm32/build-$BOARD/firmware0.bin" "$BUILD_DIR/"
    cp "$MICROPYTHON_DIR/ports/stm32/build-$BOARD/firmware1.bin" "$BUILD_DIR/"
    echo "Copied split firmware (firmware0.bin and firmware1.bin) to build directory."
else
    echo "Error: Build completed but no firmware binary found in $MICROPYTHON_DIR/ports/stm32/build-$BOARD/"
    echo "Checking build directory contents:"
    ls -la "$MICROPYTHON_DIR/ports/stm32/build-$BOARD/"
    exit 1
fi

# Copy additional firmware files if they exist
[ -f "$MICROPYTHON_DIR/ports/stm32/build-$BOARD/firmware.elf" ] && cp "$MICROPYTHON_DIR/ports/stm32/build-$BOARD/firmware.elf" "$BUILD_DIR/"
[ -f "$MICROPYTHON_DIR/ports/stm32/build-$BOARD/firmware.hex" ] && cp "$MICROPYTHON_DIR/ports/stm32/build-$BOARD/firmware.hex" "$BUILD_DIR/"
[ -f "$MICROPYTHON_DIR/ports/stm32/build-$BOARD/firmware.dfu" ] && cp "$MICROPYTHON_DIR/ports/stm32/build-$BOARD/firmware.dfu" "$BUILD_DIR/"

echo "Build complete. Firmware is available in $BUILD_DIR/"