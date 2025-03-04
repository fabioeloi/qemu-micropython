#!/usr/bin/env python3
"""
MicroPython GDB Helper

This script extends GDB with MicroPython-specific debugging capabilities,
allowing inspection of Python-level state from GDB.
"""

import gdb
import re
import sys
import os
from typing import Optional, Dict, List, Any

# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    
    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    @staticmethod
    def colorize(text, color, bold=False):
        """Apply color to text"""
        if not is_color_enabled():
            return text
        bold_code = Colors.BOLD if bold else ""
        return f"{color}{bold_code}{text}{Colors.RESET}"

# Check if color output is enabled
def is_color_enabled():
    """Check if color output is enabled in GDB"""
    try:
        return gdb.parameter("color") != "off"
    except:
        # If we can't determine, default to enabled
        return True

class MicroPythonHelper:
    def __init__(self):
        self.mp_state_ctx = None
        self.mp_state_vm = None
        self.current_frame = None
        self.exception_breakpoints = {}
        self.last_exception = None
        self.exception_history = []  # Track exception history
        self.max_history = 10  # Maximum number of exceptions to track

    def get_mp_state(self) -> None:
        """Get MicroPython state from GDB"""
        try:
            self.mp_state_ctx = gdb.parse_and_eval('MP_STATE_CTX()')
            self.mp_state_vm = gdb.parse_and_eval('MP_STATE_VM(thread)')
        except gdb.error as e:
            print(f"Error accessing MicroPython state: {e}")
            return None

    def get_current_frame(self) -> Optional[gdb.Value]:
        """Get current Python frame"""
        if not self.mp_state_vm:
            self.get_mp_state()
        if self.mp_state_vm:
            return self.mp_state_vm['frame']
        return None

    def get_qstr(self, qstr_val: gdb.Value) -> str:
        """Convert QSTR value to string"""
        try:
            # Get QSTR pool
            pool = gdb.parse_and_eval('MP_STATE_VM(qstr_pool)')
            # Extract string from pool
            str_data = pool['entries'][int(qstr_val)]['str']
            str_len = int(str_data['len'])
            str_ptr = str_data['data'].cast(gdb.lookup_type('char').pointer())
            return str_ptr.string(length=str_len)
        except Exception as e:
            return f"<qstr:{int(qstr_val)}>"

    def get_obj_type(self, obj: gdb.Value) -> str:
        """Get MicroPython object type"""
        try:
            type_ptr = obj['type']
            if type_ptr:
                type_name = self.get_qstr(type_ptr['name'])
                return type_name
        except Exception:
            pass
        return "<unknown>"

    def format_mp_obj(self, obj: gdb.Value) -> str:
        """Format MicroPython object for display"""
        obj_type = self.get_obj_type(obj)
        
        if obj_type == "str":
            # Handle string objects
            try:
                str_data = obj['str']
                str_len = int(str_data['len'])
                str_ptr = str_data['data'].cast(gdb.lookup_type('char').pointer())
                return f'"{str_ptr.string(length=str_len)}"'
            except:
                return "<str:error>"
        elif obj_type == "int":
            # Handle integer objects
            try:
                return str(int(obj['value']))
            except:
                return "<int:error>"
        elif obj_type == "float":
            # Handle float objects
            try:
                return str(float(obj['value']))
            except:
                return "<float:error>"
        elif obj_type == "list":
            # Handle list objects
            try:
                items = []
                for i in range(int(obj['len'])):
                    item = obj['items'][i]
                    items.append(self.format_mp_obj(item))
                return f"[{', '.join(items)}]"
            except:
                return "<list:error>"
        elif obj_type == "dict":
            # Handle dict objects
            try:
                items = []
                table = obj['map']['table']
                for i in range(int(table['alloc'])):
                    if table['table'][i]['key'] != 0:
                        key = self.format_mp_obj(table['table'][i]['key'])
                        value = self.format_mp_obj(table['table'][i]['value'])
                        items.append(f"{key}: {value}")
                return f"{{{', '.join(items)}}}"
            except:
                return "<dict:error>"
        elif obj_type == "exception":
            return self.format_exception(obj)
        else:
            return f"<{obj_type} object at {obj.address}>"

    def format_exception(self, exc_obj: gdb.Value) -> str:
        """Format an exception object for display"""
        try:
            exc_type = self.get_obj_type(exc_obj["base"]["type"])
            exc_args = self.format_mp_obj(exc_obj["args"])
            return f"{exc_type}({exc_args})"
        except:
            return "<error formatting exception>"

    def get_locals(self) -> Dict[str, str]:
        """Get local variables from current frame"""
        frame = self.get_current_frame()
        if not frame:
            return {}
        
        locals_dict = {}
        try:
            # Get locals dict
            locals_ptr = frame['locals']
            if locals_ptr:
                for i in range(int(locals_ptr['map']['alloc'])):
                    entry = locals_ptr['map']['table'][i]
                    if entry['key'] != 0:
                        name = self.get_qstr(entry['key'])
                        value = self.format_mp_obj(entry['value'])
                        locals_dict[name] = value
        except Exception as e:
            print(f"Error getting locals: {e}")
        
        return locals_dict

    def get_globals(self) -> Dict[str, str]:
        """Get global variables from current frame"""
        frame = self.get_current_frame()
        if not frame:
            return {}
        
        globals_dict = {}
        try:
            # Get globals dict
            globals_ptr = frame['globals']
            if globals_ptr:
                for i in range(int(globals_ptr['map']['alloc'])):
                    entry = globals_ptr['map']['table'][i]
                    if entry['key'] != 0:
                        name = self.get_qstr(entry['key'])
                        value = self.format_mp_obj(entry['value'])
                        globals_dict[name] = value
        except Exception as e:
            print(f"Error getting globals: {e}")
        
        return globals_dict

    def get_backtrace(self) -> List[str]:
        """Get Python-level backtrace"""
        frame = self.get_current_frame()
        if not frame:
            return []
        
        backtrace = []
        try:
            while frame:
                # Get function name
                fun_name = "<unknown>"
                if frame['fun']:
                    fun_name = self.get_qstr(frame['fun']['name'])
                
                # Get source info
                source = "<unknown>"
                if frame['ip']:
                    source_info = frame['ip'].dereference()['source_file']
                    if source_info:
                        source = self.get_qstr(source_info)
                        line_no = int(source_info['line_number'])
                        source = f"{source}:{line_no}"
                
                backtrace.append(f"{fun_name} at {source}")
                frame = frame['back']
        except Exception as e:
            print(f"Error getting backtrace: {e}")
        
        return backtrace

    def get_exception_info(self) -> Dict[str, Any]:
        """Get information about the current exception"""
        try:
            state = self.get_mp_state()
            if not state:
                return None
            
            exc = state["thread"]["state"]["exc_state"]["cur_exception"]
            if not exc:
                return None
            
            # Get exception details
            exc_type = self.get_obj_type(exc)
            exc_value = self.format_mp_obj(exc)
            traceback = self.get_exception_traceback(exc)
            
            # Get exception attributes
            attributes = self.get_exception_attributes(exc)
            
            # Get local variables at exception point
            locals_dict = self.get_locals()
            
            # Create exception info dictionary
            exception_info = {
                "type": exc_type,
                "value": exc_value,
                "traceback": traceback,
                "attributes": attributes,
                "locals": locals_dict,
                "address": str(exc.address)
            }
            
            # Store in history
            self.add_to_exception_history(exception_info)
            
            return exception_info
        except Exception as e:
            print(f"Error getting exception info: {e}")
            return None

    def get_exception_traceback(self, exc_obj: gdb.Value) -> List[str]:
        """Get the traceback for an exception"""
        frames = []
        try:
            frame = exc_obj["traceback"]
            while frame:
                file_name = self.get_qstr(frame["file"])
                line_num = int(frame["line"])
                frames.append(f"  File \"{file_name}\", line {line_num}")
                frame = frame["next"]
        except:
            frames.append("<error getting traceback>")
        return frames

    def get_exception_attributes(self, exc_obj: gdb.Value) -> Dict[str, str]:
        """Get attributes of an exception object"""
        attributes = {}
        try:
            # Get the exception args
            args_obj = exc_obj["args"]
            if args_obj:
                attributes["args"] = self.format_mp_obj(args_obj)
            
            # Try to get common exception attributes
            common_attrs = ["message", "errno", "strerror", "filename", "lineno", "offset", "text"]
            for attr in common_attrs:
                try:
                    # This is a simplification - in reality, we'd need to search the exception's
                    # locals dictionary for these attributes
                    attr_val = exc_obj[attr]
                    if attr_val:
                        attributes[attr] = self.format_mp_obj(attr_val)
                except:
                    pass
        except:
            pass
        
        return attributes

    def add_to_exception_history(self, exception_info: Dict[str, Any]) -> None:
        """Add exception to history"""
        # Check if this exception is already in history (by address)
        for exc in self.exception_history:
            if exc.get("address") == exception_info.get("address"):
                return
        
        # Add to history
        self.exception_history.append(exception_info)
        
        # Trim history if needed
        if len(self.exception_history) > self.max_history:
            self.exception_history.pop(0)

    def format_exception_display(self, exc_info: Dict[str, Any], detailed: bool = False) -> str:
        """Format exception information for display with colors and structure"""
        if not exc_info:
            return Colors.colorize("No active exception", Colors.YELLOW)
        
        # Format the exception header
        header = Colors.colorize(f"Exception: {exc_info['type']}", Colors.RED, bold=True)
        value = Colors.colorize(exc_info['value'], Colors.YELLOW)
        
        # Format the traceback
        traceback_header = Colors.colorize("Traceback (most recent call last):", Colors.CYAN, bold=True)
        traceback_lines = []
        for frame in exc_info['traceback']:
            # Extract file and line information
            match = re.match(r'  File "(.*)", line (\d+)', frame)
            if match:
                file_name, line_num = match.groups()
                # Highlight the file and line number
                formatted_frame = f"  File \"{Colors.colorize(file_name, Colors.GREEN)}\", line {Colors.colorize(line_num, Colors.MAGENTA)}"
                traceback_lines.append(formatted_frame)
            else:
                traceback_lines.append(frame)
        
        # Format attributes if available and detailed mode is on
        attributes_section = ""
        if detailed and exc_info.get('attributes'):
            attributes_header = Colors.colorize("\nException Attributes:", Colors.CYAN, bold=True)
            attributes_lines = []
            for key, value in exc_info['attributes'].items():
                attributes_lines.append(f"  {Colors.colorize(key, Colors.GREEN)}: {value}")
            attributes_section = f"{attributes_header}\n" + "\n".join(attributes_lines)
        
        # Format locals if available and detailed mode is on
        locals_section = ""
        if detailed and exc_info.get('locals'):
            locals_header = Colors.colorize("\nLocal Variables at Exception Point:", Colors.CYAN, bold=True)
            locals_lines = []
            for key, value in exc_info['locals'].items():
                locals_lines.append(f"  {Colors.colorize(key, Colors.GREEN)}: {value}")
            locals_section = f"{locals_header}\n" + "\n".join(locals_lines)
        
        # Combine all sections
        return f"{header}: {value}\n{traceback_header}\n" + "\n".join(traceback_lines) + attributes_section + locals_section

    def navigate_exception_history(self, index: int = -1) -> Dict[str, Any]:
        """Navigate through exception history"""
        if not self.exception_history:
            return None
        
        # Ensure index is within bounds
        if index < -len(self.exception_history) or index >= len(self.exception_history):
            index = -1  # Default to most recent
        
        # Convert negative indices
        if index < 0:
            index = len(self.exception_history) + index
        
        return self.exception_history[index]

class MPLocalsCommand(gdb.Command):
    """Print local variables in current Python frame"""
    def __init__(self, mpy):
        super().__init__("mpy-locals", gdb.COMMAND_STACK)
        self.mpy = mpy

    def invoke(self, arg, from_tty):
        locals_dict = self.mpy.get_locals()
        if locals_dict:
            print("Local variables:")
            for name, value in locals_dict.items():
                print(f"  {name} = {value}")
        else:
            print("No local variables found")

class MPGlobalsCommand(gdb.Command):
    """Print global variables in current Python frame"""
    def __init__(self, mpy):
        super().__init__("mpy-globals", gdb.COMMAND_STACK)
        self.mpy = mpy

    def invoke(self, arg, from_tty):
        globals_dict = self.mpy.get_globals()
        if globals_dict:
            print("Global variables:")
            for name, value in globals_dict.items():
                print(f"  {name} = {value}")
        else:
            print("No global variables found")

class MPBacktraceCommand(gdb.Command):
    """Print Python-level backtrace"""
    def __init__(self, mpy):
        super().__init__("mpy-bt", gdb.COMMAND_STACK)
        self.mpy = mpy

    def invoke(self, arg, from_tty):
        backtrace = self.mpy.get_backtrace()
        if backtrace:
            print("Python backtrace:")
            for i, frame in enumerate(backtrace):
                print(f"#{i}: {frame}")
        else:
            print("No Python backtrace available")

class MPCatchCommand(gdb.Command):
    """Configure exception catching and breakpoints"""
    
    def __init__(self, mpy: MicroPythonHelper):
        super().__init__("mpy-catch", gdb.COMMAND_USER)
        self.mpy = mpy
    
    def invoke(self, arg: str, from_tty: bool) -> None:
        args = arg.split()
        if not args:
            print("Usage: mpy-catch <exception_type> [all|uncaught]")
            return
        
        exc_type = args[0]
        catch_type = args[1] if len(args) > 1 else "uncaught"
        
        # Set breakpoint on exception handling
        try:
            bp = gdb.Breakpoint("mp_raise", internal=True)
            bp.condition = f"mp_obj_get_type(exc) == mp_type_{exc_type}"
            if catch_type == "uncaught":
                bp.condition += " && !mp_state_ctx.thread.state.exc_state.handler"
            
            self.mpy.exception_breakpoints[exc_type] = bp
            print(Colors.colorize(f"Will break on {catch_type} {exc_type} exceptions", Colors.GREEN))
        except Exception as e:
            print(Colors.colorize(f"Error setting exception breakpoint: {e}", Colors.RED))

class MPExceptInfoCommand(gdb.Command):
    """Show information about the current exception"""
    
    def __init__(self, mpy: MicroPythonHelper):
        super().__init__("mpy-except-info", gdb.COMMAND_USER)
        self.mpy = mpy
    
    def invoke(self, arg: str, from_tty: bool) -> None:
        args = arg.split()
        detailed = "-d" in args or "--detailed" in args
        
        # Check if we're navigating history
        index = -1
        for i, a in enumerate(args):
            if a.startswith("-i") or a.startswith("--index"):
                if i + 1 < len(args) and args[i + 1].isdigit():
                    index = int(args[i + 1])
                    break
                elif "=" in a:
                    idx_str = a.split("=")[1]
                    if idx_str.isdigit():
                        index = int(idx_str)
                        break
        
        # Get exception info
        if index != -1:
            exc_info = self.mpy.navigate_exception_history(index)
            if not exc_info:
                print(Colors.colorize(f"No exception at index {index} in history", Colors.YELLOW))
                return
        else:
            exc_info = self.mpy.get_exception_info()
        
        # Display formatted exception
        print(self.mpy.format_exception_display(exc_info, detailed))

class MPExceptBTCommand(gdb.Command):
    """Show exception backtrace"""
    
    def __init__(self, mpy: MicroPythonHelper):
        super().__init__("mpy-except-bt", gdb.COMMAND_USER)
        self.mpy = mpy
    
    def invoke(self, arg: str, from_tty: bool) -> None:
        exc_info = self.mpy.get_exception_info()
        if not exc_info:
            print(Colors.colorize("No active exception", Colors.YELLOW))
            return
        
        print(Colors.colorize("Exception Traceback:", Colors.CYAN, bold=True))
        for frame in exc_info['traceback']:
            print(frame)

class MPExceptVarsCommand(gdb.Command):
    """Show variables at exception point"""
    
    def __init__(self, mpy: MicroPythonHelper):
        super().__init__("mpy-except-vars", gdb.COMMAND_USER)
        self.mpy = mpy
    
    def invoke(self, arg: str, from_tty: bool) -> None:
        exc_info = self.mpy.get_exception_info()
        if not exc_info or not exc_info.get('locals'):
            print(Colors.colorize("No local variables at exception point", Colors.YELLOW))
            return
        
        print(Colors.colorize("Local variables at exception point:", Colors.CYAN, bold=True))
        for name, value in exc_info['locals'].items():
            print(f"  {Colors.colorize(name, Colors.GREEN)} = {value}")

class MPExceptNavigateCommand(gdb.Command):
    """Navigate through exception frames"""
    
    def __init__(self, mpy: MicroPythonHelper):
        super().__init__("mpy-except-navigate", gdb.COMMAND_USER)
        self.mpy = mpy
    
    def invoke(self, arg: str, from_tty: bool) -> None:
        exc_info = self.mpy.get_exception_info()
        if not exc_info:
            print(Colors.colorize("No active exception", Colors.YELLOW))
            return
        
        args = arg.split()
        if not args:
            print("Usage: mpy-except-navigate <frame_number>")
            print("Available frames:")
            for i, frame in enumerate(exc_info['traceback']):
                print(f"  {i}: {frame}")
            return
        
        try:
            frame_num = int(args[0])
            if frame_num < 0 or frame_num >= len(exc_info['traceback']):
                print(Colors.colorize(f"Invalid frame number: {frame_num}", Colors.RED))
                return
            
            # Display the selected frame
            frame = exc_info['traceback'][frame_num]
            print(Colors.colorize(f"Frame {frame_num}:", Colors.CYAN, bold=True))
            print(frame)
            
            # TODO: In a real implementation, we would navigate to this frame
            # and show variables at that point in the traceback
            print(Colors.colorize("Note: Frame navigation is limited in the current implementation", Colors.YELLOW))
        except ValueError:
            print(Colors.colorize(f"Invalid frame number: {args[0]}", Colors.RED))

class MPExceptHistoryCommand(gdb.Command):
    """Show exception history"""
    
    def __init__(self, mpy: MicroPythonHelper):
        super().__init__("mpy-except-history", gdb.COMMAND_USER)
        self.mpy = mpy
    
    def invoke(self, arg: str, from_tty: bool) -> None:
        if not self.mpy.exception_history:
            print(Colors.colorize("No exceptions in history", Colors.YELLOW))
            return
        
        print(Colors.colorize("Exception History:", Colors.CYAN, bold=True))
        for i, exc in enumerate(self.mpy.exception_history):
            print(f"{i}: {Colors.colorize(exc['type'], Colors.RED)}: {Colors.colorize(exc['value'], Colors.YELLOW)}")

class MPExceptVisualizeCommand(gdb.Command):
    """Visualize exception information"""
    
    def __init__(self, mpy: MicroPythonHelper):
        super().__init__("mpy-except-visualize", gdb.COMMAND_USER)
        self.mpy = mpy
    
    def invoke(self, arg: str, from_tty: bool) -> None:
        exc_info = self.mpy.get_exception_info()
        if not exc_info:
            print(Colors.colorize("No active exception", Colors.YELLOW))
            return
        
        # Create a visual representation of the exception
        width = 80
        print("╔" + "═" * (width - 2) + "╗")
        print("║" + Colors.colorize(" EXCEPTION VISUALIZATION ", Colors.RED, bold=True).center(width - 2) + "║")
        print("╠" + "═" * (width - 2) + "╣")
        
        # Exception type and value
        type_line = f" Type: {Colors.colorize(exc_info['type'], Colors.RED, bold=True)}"
        print("║" + type_line.ljust(width - 2) + "║")
        value_line = f" Value: {Colors.colorize(exc_info['value'], Colors.YELLOW)}"
        print("║" + value_line.ljust(width - 2) + "║")
        print("╠" + "═" * (width - 2) + "╣")
        
        # Traceback
        print("║" + Colors.colorize(" TRACEBACK ", Colors.CYAN, bold=True).center(width - 2) + "║")
        print("╠" + "─" * (width - 2) + "╣")
        for frame in exc_info['traceback']:
            # Wrap long frames
            while len(frame) > width - 4:
                print("║ " + frame[:width - 4] + " ║")
                frame = "  " + frame[width - 4:]
            print("║ " + frame.ljust(width - 4) + " ║")
        print("╠" + "═" * (width - 2) + "╣")
        
        # Attributes if available
        if exc_info.get('attributes'):
            print("║" + Colors.colorize(" ATTRIBUTES ", Colors.CYAN, bold=True).center(width - 2) + "║")
            print("╠" + "─" * (width - 2) + "╣")
            for key, value in exc_info['attributes'].items():
                attr_line = f" {Colors.colorize(key, Colors.GREEN)}: {value}"
                # Wrap long attributes
                while len(attr_line) > width - 4:
                    print("║ " + attr_line[:width - 4] + " ║")
                    attr_line = "  " + attr_line[width - 4:]
                print("║ " + attr_line.ljust(width - 4) + " ║")
            print("╠" + "═" * (width - 2) + "╣")
        
        # Close the box
        print("╚" + "═" * (width - 2) + "╝")

def register_micropython_commands():
    """Register MicroPython-specific GDB commands"""
    try:
        mpy = MicroPythonHelper()
        MPLocalsCommand(mpy)
        MPGlobalsCommand(mpy)
        MPBacktraceCommand(mpy)
        MPCatchCommand(mpy)
        MPExceptInfoCommand(mpy)
        MPExceptBTCommand(mpy)
        MPExceptVarsCommand(mpy)
        MPExceptNavigateCommand(mpy)
        MPExceptHistoryCommand(mpy)
        MPExceptVisualizeCommand(mpy)
        print("MicroPython GDB helpers loaded successfully")
        print(Colors.colorize("Enhanced exception handling commands available:", Colors.GREEN))
        print("  mpy-catch <type> [all|uncaught] - Configure exception catching")
        print("  mpy-except-info [-d|--detailed] [-i N|--index=N] - Show exception information")
        print("  mpy-except-bt - Show exception backtrace")
        print("  mpy-except-vars - Show variables at exception point")
        print("  mpy-except-navigate <frame_number> - Navigate through exception frames")
        print("  mpy-except-history - Show exception history")
        print("  mpy-except-visualize - Visual representation of exception")
    except Exception as e:
        print(f"Error registering MicroPython commands: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    register_micropython_commands()

"""
MicroPython GDB Helper Script

This script provides enhanced debugging capabilities for MicroPython,
particularly focused on exception handling and state inspection.

Usage:
  In GDB: source scripts/micropython_gdb.py
"""

import gdb
import re
import sys
import traceback

class MpyState:
    """Helper class to access MicroPython VM state"""
    
    @staticmethod
    def get_mp_state_ctx():
        try:
            return gdb.parse_and_eval('MP_STATE_VM(mp_loaded_modules_dict)')
        except gdb.error:
            print("Error: Cannot access MicroPython VM state.")
            print("Make sure you're debugging a MicroPython firmware with symbols.")
            return None
    
    @staticmethod
    def is_mp_obj(val):
        """Check if a value is a MicroPython object (mp_obj_t)"""
        type_str = str(val.type)
        return type_str in ('mp_obj_t', 'mp_obj_base_t*', 'mp_obj_type_t*')

    @staticmethod
    def get_obj_type(obj):
        """Get type information of a MicroPython object"""
        if MpyState.is_mp_obj(obj):
            try:
                # Get object's type based on its tag
                tag = int(obj) & 0x3
                if tag == 0:  # QSTR object
                    return "str-qstr"
                elif tag == 1:  # Integer
                    return "small-int"
                elif tag == 2:  # Immediate object
                    return "immediate"
                else:  # Pointer to an object structure
                    base_ptr = int(obj) & ~0x3
                    base = gdb.Value(base_ptr).cast(gdb.lookup_type('mp_obj_base_t').pointer())
                    type_ptr = base['type']
                    if type_ptr:
                        type_name = type_ptr['name'].string()
                        return type_name
            except Exception as e:
                print(f"Error getting object type: {e}")
        return "unknown"

class MPrintBacktraceCommand(gdb.Command):
    """Print MicroPython backtrace"""
    
    def __init__(self):
        super(MPrintBacktraceCommand, self).__init__("mp_print_backtrace", gdb.COMMAND_USER)
    
    def invoke(self, arg, from_tty):
        try:
            # Find the MicroPython exception object if available
            exc = gdb.parse_and_eval('MP_STATE_THREAD(mp_pending_exception)')
            if exc != 0:  # If there's a pending exception
                print("Current exception: ", end='')
                print(self.format_exception(exc))
            
            # Get the MicroPython call stack
            frame = gdb.parse_and_eval('MP_STATE_THREAD(mp_curr_frame)')
            
            if frame == 0:
                print("No Python frames on stack")
                return
                
            print("\nPython call stack:")
            print("==================")
            frame_num = 0
            
            while frame != 0:
                try:
                    code_info = frame['code_info']
                    code_info_str = "<no source info>"
                    if code_info != 0:
                        code_info_str = code_info.string()
                    
                    fun_name = "<unknown>"
                    codeobj = frame['code_state']['fun_bc']
                    if codeobj != 0:
                        fun_bc = codeobj.dereference()
                        if 'qstr_obj' in fun_bc.type:
                            fun_name = fun_bc['qstr_obj']['qstr']
                            # Convert QSTR to string if possible
                            try:
                                qstr_pool = gdb.parse_and_eval('MP_STATE_VM(qstr_pool)')
                                qstr_idx = int(fun_name) >> 2
                                if qstr_idx < int(qstr_pool['len']):
                                    qstr_entry = qstr_pool['qstrs'][qstr_idx]
                                    fun_name = qstr_entry['data'].string()
                            except:
                                fun_name = f"<qstr {int(fun_name):#x}>"
                    
                    print(f"#{frame_num} {fun_name} at {code_info_str}")
                    frame_num += 1
                    
                except Exception as e:
                    print(f"Error processing frame: {e}")
                    break
                    
                frame = frame['prev']
                if frame_num > 20:  # Limit stack depth to avoid infinite loops
                    print("... (stack trace truncated)")
                    break
                
        except Exception as e:
            print(f"Error while printing MicroPython backtrace: {e}")
            traceback.print_exc()
    
    def format_exception(self, exc):
        """Format a MicroPython exception object as string"""
        try:
            if int(exc) & 0x3 == 0:  # Pointer to an object
                base_ptr = int(exc) & ~0x3
                base = gdb.Value(base_ptr).cast(gdb.lookup_type('mp_obj_base_t').pointer())
                type_ptr = base['type']
                if type_ptr:
                    type_name = type_ptr['name'].string()
                    return f"Exception {type_name}"
            return f"Exception <{exc}>"
        except:
            return f"<exception {exc:#x}>"

class MPrintLocalsCommand(gdb.Command):
    """Print local variables in current MicroPython frame"""
    
    def __init__(self):
        super(MPrintLocalsCommand, self).__init__("mp_print_locals", gdb.COMMAND_USER)
    
    def invoke(self, arg, from_tty):
        try:
            frame = gdb.parse_and_eval('MP_STATE_THREAD(mp_curr_frame)')
            if frame == 0:
                print("No active MicroPython frame")
                return
            
            locals_dict = frame['code_state']['locals']
            if locals_dict == 0:
                print("No local variables available")
                return
                
            n_state = frame['code_state']['n_state']
            n_locals = int(n_state) >> 8  # Extract number of locals from n_state
            
            if n_locals == 0:
                print("No local variables in current frame")
                return
                
            print(f"Local variables ({n_locals} total):")
            for i in range(n_locals):
                try:
                    var_obj = locals_dict[i]
                    var_type = MpyState.get_obj_type(var_obj)
                    print(f"  [{i}]: {var_obj} (type: {var_type})")
                except Exception as e:
                    print(f"  [{i}]: Error: {e}")
                    
        except Exception as e:
            print(f"Error while printing locals: {e}")
            traceback.print_exc()

class MPrintGlobalsCommand(gdb.Command):
    """Print global variables in current MicroPython context"""
    
    def __init__(self):
        super(MPrintGlobalsCommand, self).__init__("mp_print_globals", gdb.COMMAND_USER)
    
    def invoke(self, arg, from_tty):
        try:
            modules_dict = MpyState.get_mp_state_ctx()
            if not modules_dict:
                return
                
            print("Global modules:")
            # This is a simplified implementation - full implementation would iterate
            # through the modules dict and print each module's globals
            print("  __main__ (current module)")
            
            # Try to find current module's globals
            frame = gdb.parse_and_eval('MP_STATE_THREAD(mp_curr_frame)')
            if frame != 0:
                code_state = frame['code_state']
                if code_state != 0 and code_state['module_globals'] != 0:
                    print("  Current module globals available")
            
            print("\nNote: Full globals inspection requires additional dictionary traversal")
            print("which is not implemented in this version of the helper.")
                    
        except Exception as e:
            print(f"Error while printing globals: {e}")
            traceback.print_exc()

class MPrintStackCommand(gdb.Command):
    """Print MicroPython value stack"""
    
    def __init__(self):
        super(MPrintStackCommand, self).__init__("mp_print_stack", gdb.COMMAND_USER)
    
    def invoke(self, arg, from_tty):
        try:
            frame = gdb.parse_and_eval('MP_STATE_THREAD(mp_curr_frame)')
            if frame == 0:
                print("No active MicroPython frame")
                return
            
            code_state = frame['code_state']
            if code_state == 0:
                print("No code state available")
                return
                
            sp = code_state['sp']
            stack = code_state['stack']
            
            if sp == 0 or stack == 0:
                print("Stack pointer or stack base not available")
                return
                
            # Calculate number of items on stack
            sp_offset = int(sp) - int(stack)
            if sp_offset <= 0:
                print("Stack is empty")
                return
                
            n_stack = sp_offset // gdb.lookup_type('mp_obj_t').sizeof
            
            print(f"Python value stack ({n_stack} items):")
            for i in range(n_stack):
                try:
                    idx = n_stack - i - 1  # Display in reverse order (top of stack first)
                    val = stack[idx]
                    val_type = MpyState.get_obj_type(val)
                    print(f"  [{idx}]: {val} (type: {val_type})")
                except Exception as e:
                    print(f"  [{idx}]: Error: {e}")
                    
        except Exception as e:
            print(f"Error while printing stack: {e}")
            traceback.print_exc()

class MPyBreakpointCommand(gdb.Command):
    """Set breakpoint on MicroPython function by name"""
    
    def __init__(self):
        super(MPyBreakpointCommand, self).__init__("mp_break", gdb.COMMAND_USER)
    
    def invoke(self, arg, from_tty):
        if not arg:
            print("Usage: mp_break <function_name>")
            return
            
        try:
            # Try setting breakpoint on Python-level function
            # This is a simplified implementation - a full implementation would
            # need to find the bytecode for the given function name
            print(f"Setting breakpoint on MicroPython function '{arg}'...")
            print("Note: This is not fully implemented in this helper version.")
            print("Try setting a breakpoint on mp_execute_bytecode instead,")
            print("then inspect the function name to find your target function.")
            
        except Exception as e:
            print(f"Error: {e}")

# Register commands
MPrintBacktraceCommand()
MPrintLocalsCommand()
MPrintGlobalsCommand()
MPrintStackCommand()
MPyBreakpointCommand()

print("MicroPython GDB helper loaded successfully")
print("Available commands:")
print("  mp_print_backtrace - Show MicroPython call stack")
print("  mp_print_locals    - Show local variables in current frame")
print("  mp_print_globals   - Show global modules and variables")
print("  mp_print_stack     - Show MicroPython value stack")
print("  mp_break <func>    - Set breakpoint on MicroPython function")