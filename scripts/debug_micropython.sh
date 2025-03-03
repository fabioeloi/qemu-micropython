#!/bin/bash
# Debug MicroPython in QEMU with GDB support

set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS_DIR="$PROJECT_DIR/tools"
QEMU_DIR="$TOOLS_DIR/qemu"
CONFIG_DIR="$PROJECT_DIR/config"
BUILD_DIR="$PROJECT_DIR/firmware/build"
FIRMWARE="$BUILD_DIR/firmware.elf"  # Use ELF file directly for better debugging
GDB_PORT=1234
LOG_FILE="$PROJECT_DIR/debug_log.txt"
GDB_LOG="$PROJECT_DIR/gdb.log"

# Check dependencies
if ! command -v arm-none-eabi-gdb &> /dev/null; then
    echo "Error: arm-none-eabi-gdb not found. Please install ARM toolchain."
    exit 1
fi

# Find QEMU executable
if [ -f "$QEMU_DIR/build/arm-softmmu/qemu-system-arm" ]; then
    QEMU_PATH="$QEMU_DIR/build/arm-softmmu/qemu-system-arm"
elif [ -f "$QEMU_DIR/build/qemu-system-arm" ]; then
    QEMU_PATH="$QEMU_DIR/build/qemu-system-arm"
else
    echo "Error: QEMU executable not found in:"
    echo "  - $QEMU_DIR/build/arm-softmmu/qemu-system-arm"
    echo "  - $QEMU_DIR/build/qemu-system-arm"
    echo "Please run setup_env.sh first."
    exit 1
fi

# Check if firmware exists
if [ ! -f "$FIRMWARE" ]; then
    echo "Error: Firmware file not found at $FIRMWARE"
    echo "Please build the firmware first using:"
    echo "  ./scripts/build.sh"
    exit 1
fi

# Create debug directory if it doesn't exist
mkdir -p "$PROJECT_DIR/debug"

# Copy GDB init file to debug directory
cp "$CONFIG_DIR/gdb/gdbinit" "$PROJECT_DIR/debug/.gdbinit"

# Function to check if port is available
check_port() {
    local port=$1
    if command -v nc >/dev/null 2>&1; then
        nc -z localhost $port >/dev/null 2>&1
        return $?
    elif command -v lsof >/dev/null 2>&1; then
        lsof -i :$port >/dev/null 2>&1
        return $?
    else
        return 0
    fi
}

# Check if port is already in use
if check_port $GDB_PORT; then
    echo "Error: Port $GDB_PORT is already in use"
    echo "Please ensure no other QEMU or GDB instances are running"
    exit 1
fi

# Kill any existing QEMU processes
pkill -f qemu-system-arm || true
sleep 1

# Start QEMU with enhanced debug options
echo "Starting QEMU with GDB server on port $GDB_PORT..."
$QEMU_PATH \
    -machine netduino2 \
    -cpu cortex-m3 \
    -m 128K \
    -kernel "$FIRMWARE" \
    -serial stdio \
    -monitor none \
    -nographic \
    -S \
    -gdb tcp::$GDB_PORT \
    -d guest_errors,unimp,exec,in_asm \
    -D "$LOG_FILE" \
    -semihosting-config enable=on,target=native \
    -semihosting \
    2>"$LOG_FILE" &

QEMU_PID=$!

# Give QEMU a moment to start
echo "Waiting for QEMU to initialize..."
for i in {1..5}; do
    if kill -0 $QEMU_PID 2>/dev/null; then
        if check_port $GDB_PORT; then
            echo "QEMU started successfully (PID: $QEMU_PID)"
            break
        fi
    fi
    sleep 1
    if [ $i -eq 5 ]; then
        echo "Error: QEMU failed to start properly. Check $LOG_FILE for details."
        kill $QEMU_PID 2>/dev/null || true
        exit 1
    fi
    echo -n "."
done

echo "Starting GDB with MicroPython helpers..."

# Load Python GDB helpers
PYTHON_HELPER="$PROJECT_DIR/scripts/micropython_gdb.py"
if [ ! -f "$PYTHON_HELPER" ]; then
    echo "Warning: MicroPython GDB helper not found at $PYTHON_HELPER"
    echo "Some debugging features may not be available"
fi

# Start GDB with our init file and Python helpers
cd "$PROJECT_DIR"
arm-none-eabi-gdb \
    -x debug/.gdbinit \
    -ex "set logging file $GDB_LOG" \
    -ex "set logging on" \
    -ex "source $PYTHON_HELPER" \
    -ex "target remote localhost:$GDB_PORT" \
    -ex "monitor system_reset" \
    -ex "set confirm off" \
    -ex "set pagination off" \
    "$FIRMWARE"

# Clean up QEMU when GDB exits
kill $QEMU_PID 2>/dev/null || true

echo "Debug session ended."
echo "Debug logs available at:"
echo "  QEMU log: $LOG_FILE"
echo "  GDB log:  $GDB_LOG" 