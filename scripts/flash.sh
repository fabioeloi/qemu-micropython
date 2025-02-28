#!/bin/bash
# Flash MicroPython firmware to a physical STM32 board
set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$PROJECT_DIR/firmware/build"
FIRMWARE="$BUILD_DIR/firmware.bin"
DEVICE=${1:-"/dev/ttyACM0"}
BOARD=${2:-"DISCOVERY_F4"}

echo "Flashing MicroPython firmware to physical STM32 board ($BOARD)..."

# Check if firmware exists
if [ ! -f "$FIRMWARE" ]; then
    echo "Firmware not found. Run build.sh first."
    exit 1
fi

# Check if ST-Link utilities are installed
if ! command -v st-flash &> /dev/null; then
    echo "st-flash not found. Please install stlink tools:"
    echo "  macOS: brew install stlink"
    echo "  Linux: apt-get install stlink-tools"
    exit 1
fi

# Flash the firmware
echo "Flashing firmware to device..."
st-flash --reset write "$FIRMWARE" 0x8000000

echo "Flashing complete. Board should be running MicroPython now."
echo "Connect to the serial port to access the REPL:"
echo "  screen $DEVICE 115200"