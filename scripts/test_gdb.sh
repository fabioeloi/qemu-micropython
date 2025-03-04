#!/bin/bash
# Run GDB integration tests
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEST_DIR="$PROJECT_DIR/tests"
BUILD_DIR="$PROJECT_DIR/firmware/build"
LOG_DIR="$PROJECT_DIR/test_results"

echo "Running GDB integration tests..."

# Create test results directory
mkdir -p "$LOG_DIR"

# Make sure we have the test firmware
if [ ! -f "$BUILD_DIR/firmware.elf" ]; then
    echo "Building test firmware..."
    "$PROJECT_DIR/scripts/build.sh"
fi

# Run the exception handling test
echo "Running exception handling tests..."
python3 "$TEST_DIR/test_gdb_exception_handling.py" 2>&1 | tee "$LOG_DIR/exception_test.log"

# Run the basic test script
echo "Running basic GDB test..."
python3 "$TEST_DIR/test_gdb_integration.py" 2>&1 | tee "$LOG_DIR/basic_test.log"

# Check test results
if grep -q "FAILED" "$LOG_DIR/exception_test.log" || grep -q "FAILED" "$LOG_DIR/basic_test.log"; then
    echo "Some tests failed. Check logs for details:"
    echo "  - $LOG_DIR/exception_test.log"
    echo "  - $LOG_DIR/basic_test.log"
    exit 1
fi

echo "All GDB integration tests passed!" 