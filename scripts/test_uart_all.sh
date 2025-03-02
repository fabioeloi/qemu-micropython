#!/bin/bash
# Run all UART driver tests to ensure no regressions
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Running UART driver regression tests..."
echo "======================================"

# Make all test scripts executable
chmod +x "$PROJECT_DIR/scripts/test_uart.sh"
chmod +x "$PROJECT_DIR/scripts/test_uart_network.sh"
chmod +x "$PROJECT_DIR/scripts/test_uart_stress.sh"
chmod +x "$PROJECT_DIR/scripts/test_uart_bindings.sh"

# Run basic test
echo -e "\n\n==== Running Basic UART Test ===="
"$PROJECT_DIR/scripts/test_uart.sh"

# Run network simulation test
echo -e "\n\n==== Running Network Simulation Test ===="
"$PROJECT_DIR/scripts/test_uart_network.sh"

# Run stress test
echo -e "\n\n==== Running UART Stress Test ===="
"$PROJECT_DIR/scripts/test_uart_stress.sh"

# Run MicroPython bindings test
echo -e "\n\n==== Running MicroPython Bindings Test ===="
"$PROJECT_DIR/scripts/test_uart_bindings.sh"

echo -e "\n\n======================================"
echo "All tests passed. No regressions detected." 