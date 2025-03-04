#!/bin/bash
# Test the MicroPython Debugger VSCode extension

set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EXTENSION_DIR="$PROJECT_DIR/config/vscode/extension"
TEST_DIR="$PROJECT_DIR/tests/vscode_extension"
TEST_LOG="$PROJECT_DIR/vscode_extension_test.log"

# Create test directory if it doesn't exist
mkdir -p "$TEST_DIR"

# Check if extension files exist
echo "Checking extension files..."
for file in "package.json" "extension.js" "README.md" "tsconfig.json"; do
    if [ -f "$EXTENSION_DIR/$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file does not exist"
        exit 1
    fi
done

# Create a test exception info file
echo "Creating test exception info file..."
mkdir -p "$TEST_DIR/.vscode"
cat > "$TEST_DIR/.vscode/exception_info.json" << EOL
{
    "type": "ZeroDivisionError",
    "value": "division by zero",
    "traceback": [
        {
            "function": "test_zero_division",
            "file": "src/main.py",
            "line": 10
        },
        {
            "function": "main",
            "file": "src/main.py",
            "line": 50
        }
    ],
    "attributes": {},
    "locals": {
        "a": "10",
        "b": "0",
        "result": "None"
    },
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOL

# Create a test exception history file
echo "Creating test exception history file..."
cat > "$TEST_DIR/.vscode/exception_history.json" << EOL
[
    {
        "type": "ZeroDivisionError",
        "value": "division by zero",
        "traceback": [
            {
                "function": "test_zero_division",
                "file": "src/main.py",
                "line": 10
            },
            {
                "function": "main",
                "file": "src/main.py",
                "line": 50
            }
        ],
        "attributes": {},
        "locals": {
            "a": "10",
            "b": "0",
            "result": "None"
        },
        "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    },
    {
        "type": "IndexError",
        "value": "list index out of range",
        "traceback": [
            {
                "function": "test_index_error",
                "file": "src/main.py",
                "line": 20
            },
            {
                "function": "main",
                "file": "src/main.py",
                "line": 51
            }
        ],
        "attributes": {},
        "locals": {
            "lst": "[1, 2, 3]",
            "index": "5"
        },
        "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%NZ")"
    }
]
EOL

# Create a test source file
echo "Creating test source file..."
mkdir -p "$TEST_DIR/src"
cat > "$TEST_DIR/src/main.py" << EOL
"""
Test file for MicroPython Debugger VSCode extension
"""

def test_zero_division():
    """Test division by zero"""
    a = 10
    b = 0
    result = None
    result = a / b  # This will raise ZeroDivisionError
    return result

def test_index_error():
    """Test index error"""
    lst = [1, 2, 3]
    index = 5
    return lst[index]  # This will raise IndexError

def test_attribute_error():
    """Test attribute error"""
    class TestClass:
        def __init__(self):
            self.value = 42
    
    obj = TestClass()
    return obj.nonexistent_attribute  # This will raise AttributeError

def main():
    """Main function"""
    try:
        test_zero_division()
    except ZeroDivisionError as e:
        print(f"Caught ZeroDivisionError: {e}")
    
    try:
        test_index_error()
    except IndexError as e:
        print(f"Caught IndexError: {e}")
    
    try:
        test_attribute_error()
    except AttributeError as e:
        print(f"Caught AttributeError: {e}")

if __name__ == "__main__":
    main()
EOL

# Test extension.js syntax
echo "Testing extension.js syntax..."
node --check "$EXTENSION_DIR/extension.js" > "$TEST_LOG" 2>&1 || {
    echo "✗ extension.js has syntax errors:"
    cat "$TEST_LOG"
    exit 1
}
echo "✓ extension.js syntax is valid"

# Test package.json syntax
echo "Testing package.json syntax..."
cat "$EXTENSION_DIR/package.json" | node -e "JSON.parse(require('fs').readFileSync(0, 'utf8'))" > "$TEST_LOG" 2>&1 || {
    echo "✗ package.json has syntax errors:"
    cat "$TEST_LOG"
    exit 1
}
echo "✓ package.json syntax is valid"

# Clean up
rm -f "$TEST_LOG"

echo "All tests passed!"
echo "The VSCode extension is ready to use."
echo ""
echo "To install the extension, run:"
echo "  ./scripts/install_vscode_extension.sh"
echo ""
echo "For more information, see the extension README at:"
echo "  $EXTENSION_DIR/README.md" 