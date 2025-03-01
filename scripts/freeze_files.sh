#!/bin/bash
# Prepare Python files for freezing into MicroPython firmware
set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MICROPYTHON_DIR="$PROJECT_DIR/tools/micropython"
STM32_PORT_DIR="$MICROPYTHON_DIR/ports/stm32"
SRC_DIR="$PROJECT_DIR/src"
BOARD=${1:-"STM32F4DISC_QEMU"}
BOARD_DIR="$STM32_PORT_DIR/boards/$BOARD"

echo "Preparing Python files for $BOARD board..."

# Check if source directory exists
if [ ! -d "$SRC_DIR" ]; then
    echo "Source directory not found: $SRC_DIR"
    exit 1
fi

# Check if board directory exists
if [ ! -d "$BOARD_DIR" ]; then
    echo "Board directory not found: $BOARD_DIR"
    exit 1
fi

# Check that manifest.py contains the freeze_namespace directive
if ! grep -q "freeze_namespace" "$BOARD_DIR/manifest.py"; then
    echo "Warning: manifest.py does not contain a freeze_namespace directive."
    echo "Files may not be frozen properly."
fi

# Create main.py stub in the build directory
# Note: This script doesn't actually copy main.py into the firmware - it's frozen via the manifest
echo "Checking main.py..."
if [ -f "$SRC_DIR/main.py" ]; then
    echo "Found main.py in source directory."
else
    echo "Warning: main.py not found in source directory."
    # Create a default main.py if it doesn't exist
    mkdir -p "$SRC_DIR"
    cat > "$SRC_DIR/main.py" << EOF
"""
Default MicroPython application
"""
import machine
import time

# Simple LED blink application
led = machine.Pin("PA0", machine.Pin.OUT)

def main():
    print("MicroPython on QEMU started")
    count = 0
    while True:
        led.toggle()
        print(f"LED toggled, count={count}")
        time.sleep(1)
        count += 1

if __name__ == "__main__":
    main()
EOF
    echo "Created default main.py"
fi

# Check for Python libraries
echo "Checking library files..."
LIB_DIR="$SRC_DIR/lib"
if [ ! -d "$LIB_DIR" ]; then
    echo "Creating lib directory..."
    mkdir -p "$LIB_DIR"
fi

# List files that will be frozen
echo "The following files will be frozen into the firmware:"
echo "-------------------------------------------------"
echo "main.py"
find "$LIB_DIR" -name "*.py" | sort | while read -r file; do
    # Get relative path without using realpath (for macOS compatibility)
    rel_path=${file#$SRC_DIR/}
    echo "$rel_path"
done
echo "-------------------------------------------------"

echo "Python files ready for freezing."
echo "Run './scripts/build.sh $BOARD' to build the firmware." 