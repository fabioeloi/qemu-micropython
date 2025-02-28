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
BOARD=${1:-"DISCOVERY_F4"}

echo "Building MicroPython firmware for STM32 ($BOARD)..."

# Check if MicroPython is available
if [ ! -d "$MICROPYTHON_DIR" ]; then
    echo "MicroPython directory not found. Run setup_env.sh first."
    exit 1
fi

# Copy our manifest file
mkdir -p "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD"
cp "$CONFIG_DIR/micropython/manifest.py" "$MICROPYTHON_DIR/ports/stm32/boards/$BOARD/"

# Copy our source files to the MicroPython src directory
if [ -d "$SRC_DIR/lib" ]; then
    mkdir -p "$MICROPYTHON_DIR/ports/stm32/modules"
    cp -r "$SRC_DIR/lib/"* "$MICROPYTHON_DIR/ports/stm32/modules/"
fi

# Copy main.py to the filesystem
if [ -f "$SRC_DIR/main.py" ]; then
    cp "$SRC_DIR/main.py" "$MICROPYTHON_DIR/ports/stm32/"
fi

# Build MicroPython
cd "$MICROPYTHON_DIR"
cd ports/stm32
make clean
make BOARD=$BOARD

# Copy the firmware to our build directory
mkdir -p "$BUILD_DIR"
cp "$MICROPYTHON_DIR/ports/stm32/build-$BOARD/firmware.bin" "$BUILD_DIR/"
cp "$MICROPYTHON_DIR/ports/stm32/build-$BOARD/firmware.elf" "$BUILD_DIR/"
cp "$MICROPYTHON_DIR/ports/stm32/build-$BOARD/firmware.hex" "$BUILD_DIR/"

echo "Build complete. Firmware is available in $BUILD_DIR/"