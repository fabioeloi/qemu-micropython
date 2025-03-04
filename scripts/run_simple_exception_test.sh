#!/bin/bash
# Run a simple exception test with GDB

set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
GDB_SCRIPT="$PROJECT_DIR/simple_exception_test.gdb"
LOG_FILE="$PROJECT_DIR/simple_exception_test.log"
GDB_PORT=1235
QEMU_LOG="$PROJECT_DIR/qemu_test.log"
MPY_GDB_SCRIPT="$PROJECT_DIR/scripts/micropython_gdb.py"

# Check if the MicroPython GDB helper script exists
if [ ! -f "$MPY_GDB_SCRIPT" ]; then
    echo "Warning: MicroPython GDB helper script not found at: $MPY_GDB_SCRIPT"
    echo "Some debugging features may not be available."
else
    echo "Found MicroPython GDB helper script at: $MPY_GDB_SCRIPT"
fi

# Update the GDB script to use the new port
sed -i '' "s/localhost:[0-9]*/localhost:$GDB_PORT/g" "$GDB_SCRIPT"

# Kill any existing QEMU processes
pkill -f qemu-system-arm || true
sleep 1

# Start QEMU with GDB server
echo "Starting QEMU with GDB server on port $GDB_PORT..."
"$PROJECT_DIR/tools/qemu/build/qemu-system-arm" \
    -machine olimex-stm32-h405 \
    -cpu cortex-m4 \
    -m 128K \
    -kernel "$PROJECT_DIR/firmware/build/firmware.elf" \
    -serial stdio \
    -monitor none \
    -nographic \
    -gdb tcp::$GDB_PORT \
    -S \
    -d guest_errors,unimp \
    -semihosting-config enable=on,target=native \
    -semihosting \
    > "$QEMU_LOG" 2>&1 &

QEMU_PID=$!

# Give QEMU a moment to start
echo "Waiting for QEMU to initialize..."
sleep 2

# Check if QEMU started successfully
if ! ps -p $QEMU_PID > /dev/null; then
    echo "Failed to start QEMU."
    exit 1
fi

# Check if QEMU is listening on the specified port
if ! lsof -i :$GDB_PORT | grep -q LISTEN; then
    echo "QEMU is not listening on port $GDB_PORT."
    kill $QEMU_PID 2>/dev/null || true
    exit 1
fi

echo "QEMU started successfully with PID $QEMU_PID."

# Run GDB with our test script
echo "Running GDB with test script..."
GDB_CMD="/opt/homebrew/Cellar/arm-none-eabi-gdb/16.2/bin/arm-none-eabi-gdb"
GDB_ARGS="-nx -ex \"set pagination off\""

# Add the MicroPython GDB helper script if it exists
if [ -f "$MPY_GDB_SCRIPT" ]; then
    echo "Adding MicroPython GDB helper script to GDB arguments..."
    $GDB_CMD -nx -ex "set pagination off" -ex "source $MPY_GDB_SCRIPT" -x "$GDB_SCRIPT" > "$LOG_FILE" 2>&1
else
    $GDB_CMD -nx -ex "set pagination off" -x "$GDB_SCRIPT" > "$LOG_FILE" 2>&1
fi

# Check the results
echo "Test completed. Log file: $LOG_FILE"
echo "Contents of log file:"
cat "$LOG_FILE"

# Clean up
echo "Stopping QEMU (PID $QEMU_PID)..."
kill $QEMU_PID 2>/dev/null || true

echo "Test completed." 