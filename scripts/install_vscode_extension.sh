#!/bin/bash
# Install the MicroPython Debugger VSCode extension

set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EXTENSION_DIR="$PROJECT_DIR/config/vscode/extension"
VSCODE_EXTENSIONS_DIR="$HOME/.vscode/extensions/micropython-debugger-0.1.0"

# Check if extension directory exists
if [ ! -d "$EXTENSION_DIR" ]; then
    echo "Error: Extension directory not found at $EXTENSION_DIR"
    exit 1
fi

# Create VSCode extensions directory if it doesn't exist
mkdir -p "$VSCODE_EXTENSIONS_DIR"

# Copy extension files
echo "Copying extension files to $VSCODE_EXTENSIONS_DIR..."
cp -r "$EXTENSION_DIR"/* "$VSCODE_EXTENSIONS_DIR/"

# Make sure the extension is executable
chmod +x "$VSCODE_EXTENSIONS_DIR/extension.js"

echo "MicroPython Debugger extension installed successfully!"
echo ""
echo "To use the extension:"
echo "1. Restart VSCode if it's currently running"
echo "2. Open your MicroPython project in VSCode"
echo "3. Start a debug session using the 'MicroPython Debug (QEMU)' configuration"
echo "4. When an exception occurs, the extension will automatically visualize it"
echo ""
echo "For more information, see the extension README at $VSCODE_EXTENSIONS_DIR/README.md" 