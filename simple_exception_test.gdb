# Simple GDB script to test exception handling

# Print a message to confirm the script is running
echo "Starting simple exception test..."

# Set GDB to not ask for confirmation
set confirm off

# Set GDB to not paginate output
set pagination off

# Load the firmware file first
echo "Loading firmware file..."
file firmware/build/firmware.elf

# Try to connect to the target
echo "Connecting to target..."
target remote localhost:1235

# Print target information
echo "Target information:"
info target

# Source the MicroPython GDB helper script if it exists
echo "Trying to source MicroPython GDB helper script..."
python
import os
script_path = os.path.join(os.getcwd(), "scripts/micropython_gdb.py")
if os.path.exists(script_path):
    try:
        gdb.execute(f"source {script_path}")
        print(f"Successfully loaded MicroPython GDB helper from {script_path}")
    except Exception as e:
        print(f"Error loading MicroPython GDB helper: {e}")
else:
    print(f"MicroPython GDB helper script not found at {script_path}")
end

# Set breakpoints on exception-related functions
echo "Setting breakpoints on exception-related functions..."
break mp_raise_msg
break mp_raise_ValueError
break mp_raise_TypeError
info breakpoints

# Set up exception catching if the mpy-catch command is available
echo "Setting up exception catching..."
python
try:
    gdb.execute("mpy-catch ZeroDivisionError all")
    gdb.execute("mpy-catch IndexError all")
    gdb.execute("mpy-catch AttributeError all")
    print("Exception catching set up successfully")
except Exception as e:
    print(f"Error setting up exception catching: {e}")
end

# Continue execution until a breakpoint is hit
echo "Continuing execution..."
continue

# When a breakpoint is hit, print information about the exception
echo "Breakpoint hit on exception function"
backtrace

# Try to use MicroPython GDB helper commands if available
echo "Trying MicroPython GDB helper commands..."
python
try:
    gdb.execute("mp_print_backtrace")
    print("mp_print_backtrace executed successfully")
except Exception as e:
    print(f"Error with mp_print_backtrace: {e}")

try:
    gdb.execute("mpy-except-info")
    print("mpy-except-info executed successfully")
except Exception as e:
    print(f"Error with mpy-except-info: {e}")
end

# Exit GDB
echo "Exiting GDB..."
quit 