#!/bin/bash
# Test the custom UART driver
set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC_DIR="$PROJECT_DIR/src"
BUILD_DIR="$PROJECT_DIR/firmware/build"

echo "Building and testing the custom UART driver..."

# Create build directory if it doesn't exist
mkdir -p "$BUILD_DIR"

# Compile our custom UART driver test with debugging flags
gcc -I"$SRC_DIR" -g -Wall -Wno-unused-variable -o "$BUILD_DIR/uart_test" \
    "$SRC_DIR/custom_uart_driver.c" "$SRC_DIR/custom_uart_test.c" -lm

echo "Compiled custom UART driver test. Running..."

# Run the test
"$BUILD_DIR/uart_test" 