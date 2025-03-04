#!/bin/bash
# Test the enhanced exception visualization features in GDB

set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
GDB_SCRIPT="$PROJECT_DIR/tests/exception_visualization_gdb_commands.txt"

# Create a GDB script with commands to test exception visualization
cat > "$GDB_SCRIPT" << EOL
# Test the enhanced exception visualization features

# Set up exception catching
mpy-catch ZeroDivisionError all
continue

# Test basic exception info
mpy-except-info

# Test detailed exception info
mpy-except-info -d

# Test exception visualization
mpy-except-visualize

# Test exception history
mpy-except-history

# Test frame navigation
mpy-except-navigate
mpy-except-navigate 0

# Continue to next exception
mpy-catch IndexError all
continue

# Test exception history again
mpy-except-history
mpy-except-info -i 0
mpy-except-info -i 1

# Exit GDB
quit
EOL

# Run the debug script with our GDB commands
echo "Starting debug session with exception visualization test..."
echo "This will run a series of GDB commands to test the enhanced exception visualization features."
echo "Press Enter to continue..."
read

# Run the debug script
"$PROJECT_DIR/scripts/debug_micropython.sh" -x "$GDB_SCRIPT"

# Clean up
rm "$GDB_SCRIPT"

echo "Test completed. Check the output above for the enhanced exception visualization features." 