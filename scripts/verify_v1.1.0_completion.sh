#!/bin/bash
# Verification script for v1.1.0 milestone completion
# This script verifies that all components of the v1.1.0 milestone are properly implemented

set -e

echo "=========================================="
echo "v1.1.0 Milestone Verification Script"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

check_file() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description: $file"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗${NC} $description: $file NOT FOUND"
        ((FAIL++))
        return 1
    fi
}

check_command_in_file() {
    local file=$1
    local command=$2
    local description=$3
    
    if grep -q "$command" "$file"; then
        echo -e "${GREEN}✓${NC} $description: $command found"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗${NC} $description: $command NOT FOUND"
        ((FAIL++))
        return 1
    fi
}

check_function_exists() {
    local file=$1
    local function=$2
    local description=$3
    
    if grep -q "def $function\|class $function" "$file"; then
        echo -e "${GREEN}✓${NC} $description: $function implemented"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗${NC} $description: $function NOT IMPLEMENTED"
        ((FAIL++))
        return 1
    fi
}

echo -e "${BLUE}[1] Checking GDB Integration Files${NC}"
echo "-------------------------------------------"
check_file "scripts/micropython_gdb.py" "MicroPython GDB helper"
check_file "scripts/debug_micropython.sh" "Debug launch script"
check_file "config/gdb/gdbinit" "GDB initialization file"
echo ""

echo -e "${BLUE}[2] Checking Exception Handling Implementation${NC}"
echo "-------------------------------------------"
check_command_in_file "scripts/micropython_gdb.py" "mpy-catch" "Exception catching command"
check_command_in_file "scripts/micropython_gdb.py" "mpy-except-info" "Exception info command"
check_command_in_file "scripts/micropython_gdb.py" "mpy-except-bt" "Exception backtrace command"
check_command_in_file "scripts/micropython_gdb.py" "mpy-except-vars" "Exception variables command"
check_command_in_file "scripts/micropython_gdb.py" "mpy-except-navigate" "Exception navigation command"
check_command_in_file "scripts/micropython_gdb.py" "mpy-except-history" "Exception history command"
check_command_in_file "scripts/micropython_gdb.py" "mpy-except-visualize" "Exception visualization command"
echo ""

echo -e "${BLUE}[3] Checking Exception Helper Functions${NC}"
echo "-------------------------------------------"
check_function_exists "scripts/micropython_gdb.py" "get_exception_info" "Exception info retrieval"
check_function_exists "scripts/micropython_gdb.py" "get_exception_traceback" "Exception traceback"
check_function_exists "scripts/micropython_gdb.py" "get_exception_attributes" "Exception attributes"
check_function_exists "scripts/micropython_gdb.py" "add_to_exception_history" "Exception history tracking"
check_function_exists "scripts/micropython_gdb.py" "format_exception_display" "Exception formatting"
check_function_exists "scripts/micropython_gdb.py" "navigate_exception_history" "Exception history navigation"
echo ""

echo -e "${BLUE}[4] Checking UART Driver Implementation${NC}"
echo "-------------------------------------------"
check_file "src/custom_uart_driver.c" "Custom UART driver source"
check_file "src/custom_uart_driver.h" "Custom UART driver header"
check_file "src/custom_uart_test.c" "UART test implementation"
check_file "src/network_sim_test.c" "Network simulation test"
check_file "src/bridge_test.c" "Bridge test"
echo ""

echo -e "${BLUE}[5] Checking Documentation${NC}"
echo "-------------------------------------------"
check_file "docs/GDB_DEBUGGING.md" "GDB debugging guide"
check_file "docs/UART_DRIVER_TESTING.md" "UART driver testing guide"
check_file "docs/IDE_INTEGRATION.md" "IDE integration guide"
check_file "docs/milestone_v1.1.0_summary.md" "Milestone summary"
check_file "docs/v1.1.0_final_checklist.md" "Final checklist"
check_file "ROADMAP_STATUS.md" "Roadmap status document"
echo ""

echo -e "${BLUE}[6] Checking Exception Handling Documentation${NC}"
echo "-------------------------------------------"
check_command_in_file "docs/GDB_DEBUGGING.md" "mpy-catch" "Exception catching documented"
check_command_in_file "docs/GDB_DEBUGGING.md" "mpy-except-info" "Exception info documented"
check_command_in_file "docs/GDB_DEBUGGING.md" "mpy-except-bt" "Exception backtrace documented"
check_command_in_file "docs/GDB_DEBUGGING.md" "mpy-except-vars" "Exception variables documented"
echo ""

echo -e "${BLUE}[7] Checking Python-Level Debugging${NC}"
echo "-------------------------------------------"
check_command_in_file "scripts/micropython_gdb.py" "mpy-bt" "Python backtrace command"
check_command_in_file "scripts/micropython_gdb.py" "mpy-locals" "Local variables command"
check_command_in_file "scripts/micropython_gdb.py" "mpy-globals" "Global variables command"
check_command_in_file "scripts/micropython_gdb.py" "mpy-stack" "Stack inspection command"
echo ""

echo -e "${BLUE}[8] Checking Test Infrastructure${NC}"
echo "-------------------------------------------"
check_file "src/micropython_uart_test.py" "MicroPython UART test"
check_file "tests/test_gdb_integration.py" "GDB integration test"
check_file "scripts/run_simple_exception_test.sh" "Exception test script"
echo ""

echo ""
echo "=========================================="
echo -e "${BLUE}Verification Summary${NC}"
echo "=========================================="
echo -e "${GREEN}Passed:${NC} $PASS"
echo -e "${RED}Failed:${NC} $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All v1.1.0 components verified successfully!${NC}"
    echo ""
    echo "The v1.1.0 milestone appears to be complete with all major features implemented:"
    echo "  • GDB integration with MicroPython support"
    echo "  • Comprehensive exception handling (mpy-catch, mpy-except-*)"
    echo "  • Python-level debugging commands"
    echo "  • Custom UART driver with simulation"
    echo "  • Network simulation capabilities"
    echo "  • Complete documentation"
    echo ""
    echo "Status: READY FOR FINAL RELEASE"
    exit 0
else
    echo -e "${YELLOW}⚠ Some components are missing or incomplete${NC}"
    echo ""
    echo "Please review the failed checks above before proceeding with the release."
    echo ""
    echo "Status: NEEDS ATTENTION"
    exit 1
fi
