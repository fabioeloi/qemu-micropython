#!/bin/bash
# Test the VSCode integration for exception visualization

set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VSCODE_CONFIG_DIR="$PROJECT_DIR/config/vscode"
CONFIG_DIR="$PROJECT_DIR/config"
SVD_DIR="$CONFIG_DIR/svd"
TEST_LOG="$PROJECT_DIR/vscode_integration_test.log"

# Create necessary directories
mkdir -p "$SVD_DIR"

# Check if VSCode configuration files exist
echo "Checking VSCode configuration files..."
for file in "launch.json" "tasks.json" "keybindings.json" "gdb_micropython.py" "README.md"; do
    if [ -f "$VSCODE_CONFIG_DIR/$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file does not exist"
        exit 1
    fi
done

# Check if SVD file exists, download if not
if [ ! -f "$SVD_DIR/STM32F407.svd" ]; then
    echo "Downloading STM32F407.svd file..."
    curl -s https://raw.githubusercontent.com/posborne/cmsis-svd/master/data/STMicro/STM32F407.svd -o "$SVD_DIR/STM32F407.svd"
    if [ $? -ne 0 ]; then
        echo "Failed to download SVD file"
        exit 1
    fi
    echo "✓ Downloaded STM32F407.svd"
else
    echo "✓ STM32F407.svd exists"
fi

# Check if IDE integration documentation exists
if [ -f "$PROJECT_DIR/docs/IDE_INTEGRATION.md" ]; then
    echo "✓ IDE integration documentation exists"
else
    echo "✗ IDE integration documentation does not exist"
    exit 1
fi

# Test GDB Python script syntax
echo "Testing GDB Python script syntax..."
python3 -m py_compile "$VSCODE_CONFIG_DIR/gdb_micropython.py" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ GDB Python script syntax is valid"
else
    echo "✗ GDB Python script has syntax errors"
    python3 -m py_compile "$VSCODE_CONFIG_DIR/gdb_micropython.py"
    exit 1
fi

# Create a test GDB script
GDB_SCRIPT="$PROJECT_DIR/tests/vscode_integration_test.gdb"
echo "Creating test GDB script..."
cat > "$GDB_SCRIPT" << EOL
# Test VSCode integration
source $PROJECT_DIR/scripts/micropython_gdb.py
source $VSCODE_CONFIG_DIR/gdb_micropython.py

# Print test message
echo "VSCode integration test script loaded"

# Test commands
help vscode-except-info
help vscode-except-visualize

# Exit GDB
quit
EOL

# Run GDB with the test script
echo "Running GDB with test script..."
arm-none-eabi-gdb -batch -x "$GDB_SCRIPT" > "$TEST_LOG" 2>&1 || true

# Check if the test was successful
if grep -q "VSCode integration test script loaded" "$TEST_LOG"; then
    echo "✓ GDB loaded the test script successfully"
else
    echo "✗ GDB failed to load the test script"
    cat "$TEST_LOG"
    exit 1
fi

if grep -q "vscode-except-info" "$TEST_LOG" && grep -q "vscode-except-visualize" "$TEST_LOG"; then
    echo "✓ VSCode commands are registered"
else
    echo "✗ VSCode commands are not registered"
    cat "$TEST_LOG"
    exit 1
fi

# Create .vscode directory and copy configuration files
echo "Setting up VSCode configuration..."
mkdir -p "$PROJECT_DIR/.vscode"
cp "$VSCODE_CONFIG_DIR/launch.json" "$VSCODE_CONFIG_DIR/tasks.json" "$PROJECT_DIR/.vscode/"
echo "✓ VSCode configuration files copied to .vscode directory"

# Clean up
rm -f "$GDB_SCRIPT"
rm -f "$TEST_LOG"

echo "All tests passed!"
echo "VSCode integration is ready to use."
echo ""
echo "To use the VSCode integration:"
echo "1. Open this project in VSCode"
echo "2. Run the 'create-svd-directory' task if you haven't already"
echo "3. Start debugging with the 'MicroPython Debug (QEMU)' configuration"
echo "4. Use the keyboard shortcuts to visualize exceptions:"
echo "   - Ctrl+Shift+E: Visualize exception"
echo "   - Ctrl+Shift+I: Show exception information"
echo "   - Ctrl+Shift+H: Show exception history"
echo "   - Ctrl+Shift+N: Navigate exception frames"
echo ""
echo "For more information, see the documentation in docs/IDE_INTEGRATION.md" 