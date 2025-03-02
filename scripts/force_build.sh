
#!/bin/bash
# Force build MicroPython with specific board
set -e

BOARD="STM32F4DISC"
export BOARD

echo "Forcing build for board: $BOARD"

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS_DIR="$PROJECT_DIR/tools"
MICROPYTHON_DIR="$TOOLS_DIR/micropython"

# Directly run make with explicit board name
cd "$MICROPYTHON_DIR/ports/stm32"
make clean BOARD=$BOARD V=1
make BOARD=$BOARD V=1

echo "Build complete"