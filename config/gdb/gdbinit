# GDB initialization file for QEMU-MicroPython debugging

# Basic GDB configuration
set confirm off
set verbose off
set pagination off
set print pretty on
set print array on
set print array-indexes on
set python print-stack full
set history save on
set history filename ~/.gdb_history
set history size 10000
set history remove-duplicates unlimited

# Error handling and output configuration
set complaints 1
set print elements 0
set python print-stack full

# Define connection helper function
define connect_target
    # Attempt to connect to target
    printf "Connecting to QEMU (port 1234)...\n"
    target remote localhost:1234
    if $_isvoid($)
        printf "Error: Failed to connect to QEMU\n"
        printf "Please ensure QEMU is running with GDB server enabled\n"
        return
    end
    printf "Connected successfully\n"
    
    # Load debug symbols
    printf "Loading debug symbols...\n"
    file firmware/build/firmware.elf
    if $_isvoid($)
        printf "Error: Failed to load debug symbols\n"
        printf "Please ensure firmware.elf exists and contains debug info\n"
        return
    end
    printf "Debug symbols loaded\n"
end

# Set up Python pretty-printers
python
import os
import sys

# Add custom pretty printers for MicroPython objects
class MpyObjectPrinter:
    def __init__(self, val):
        self.val = val

    def to_string(self):
        try:
            # Extract MicroPython object type and value
            type_name = self.val['type']['name'].string()
            if type_name == "str":
                return f'mp_obj_str("{self.val["str"]}")'
            elif type_name == "int":
                return f'mp_obj_int({self.val["value"]})'
            return f'mp_obj({type_name})'
        except:
            return "Error printing MicroPython object"

def register_printers(obj):
    if obj is None:
        obj = gdb
    obj.pretty_printers.append(lookup_function)

def lookup_function(val):
    if str(val.type).startswith("mp_obj_"):
        return MpyObjectPrinter(val)
    return None

register_printers(None)
end

# Custom GDB commands for MicroPython debugging
define mpy_bt
    # Print MicroPython backtrace
    printf "MicroPython backtrace:\n"
    printf "====================\n"
    call mp_print_backtrace()
end
document mpy_bt
Print MicroPython backtrace showing Python-level call stack
end

define mpy_locals
    # Print local variables in current Python frame
    printf "Local variables:\n"
    printf "===============\n"
    call mp_print_locals()
end
document mpy_locals
Print local variables in the current Python frame
end

define mpy_globals
    # Print global variables
    printf "Global variables:\n"
    printf "================\n"
    call mp_print_globals()
end
document mpy_globals
Print global variables in the current context
end

define mpy_stack
    # Print Python stack contents
    printf "Python stack:\n"
    printf "============\n"
    call mp_print_stack()
end
document mpy_stack
Print contents of the Python stack
end

# Helper commands for common operations
define reset_target
    monitor system_reset
    printf "Target reset\n"
end
document reset_target
Reset the target device
end

define reload_symbols
    file firmware/build/firmware.elf
    printf "Debug symbols reloaded\n"
end
document reload_symbols
Reload debug symbols from firmware
end

# Set up common breakpoints
break mp_execute_bytecode
break mp_raise

# Show version and configuration info
show version
show configuration

# Print available commands
printf "\nMicroPython Debugging Commands:\n"
printf "============================\n"
printf "mpy_bt      - Show MicroPython backtrace\n"
printf "mpy_locals  - Show local variables\n"
printf "mpy_globals - Show global variables\n"
printf "mpy_stack   - Show Python stack\n"
printf "reset_target - Reset the target device\n"
printf "reload_symbols - Reload debug symbols\n\n"

printf "Common GDB Commands:\n"
printf "==================\n"
printf "continue (c) - Continue execution\n"
printf "step (s)    - Step into function\n"
printf "next (n)    - Step over function\n"
printf "break (b)   - Set breakpoint\n"
printf "print (p)   - Print variable\n"
printf "x           - Examine memory\n"
printf "info break  - List breakpoints\n"
printf "quit (q)    - Exit GDB\n\n"

# Connect to target
connect_target 