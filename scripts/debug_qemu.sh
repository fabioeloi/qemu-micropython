#!/bin/bash
# Debug QEMU output
set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="$PROJECT_DIR/qemu_log.txt"

echo "Analyzing QEMU log file at $LOG_FILE..."

# Check if the log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "Log file not found. Run run_qemu.sh first."
    exit 1
fi

# Count occurrences of common error messages
echo "Common error messages:"
echo "---------------------"
grep -c "stm32_rcc_write" "$LOG_FILE" || echo "No RCC write errors"
grep -c "unimplemented device" "$LOG_FILE" || echo "No unimplemented device errors"

# Check for any Python output
echo ""
echo "Looking for Python output:"
echo "-------------------------"
grep -i "micropython" "$LOG_FILE" || echo "No MicroPython output found"
grep -i "hello" "$LOG_FILE" || echo "No 'hello' messages found"
grep -i "python" "$LOG_FILE" || echo "No Python-related output found"

# Check for UART activity
echo ""
echo "UART activity:"
echo "-------------"
grep -i "uart" "$LOG_FILE" || echo "No UART activity found"

# Check for semihosting activity
echo ""
echo "Semihosting activity:"
echo "--------------------"
grep -i "semihosting" "$LOG_FILE" || echo "No semihosting activity found"

echo ""
echo "Last 20 lines of the log:"
echo "------------------------"
tail -20 "$LOG_FILE"

echo ""
echo "Debug analysis complete." 