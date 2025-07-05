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

# --- Source Code Lookup Helpers ---
# Configuration for source lookup
# Order of search:
# 1. Absolute paths.
# 2. Relative to GDB's current working directory.
# 3. Relative to paths in GDB parameter `mpy-source-path`.
# 4. Relative to paths in environment variable `MPY_SOURCE_PATH`.

class MpySourcePathParameter(gdb.Parameter):
    """Set the source path for MicroPython projects.
    A list of directories separated by os.pathsep (e.g., /path/to/src1:/path/to/src2)."""
    set_doc = "Set MicroPython source lookup paths."
    show_doc = "Show MicroPython source lookup paths."

    def __init__(self):
        super().__init__("mpy-source-path", gdb.COMMAND_SUPPORT, gdb.PARAM_STRING)
        self.value = "" # Default value

# Instantiate the parameter to register it with GDB (if not already defined)
if 'MpySourcePathParameter_registered' not in globals():
    MpySourcePathParameter()
    MpySourcePathParameter_registered = True


def _gdb_resolve_source_path(filename_str):
    """Tries to find the absolute path for a source file."""
    if not filename_str or filename_str.startswith("<"): # Don't try to resolve special names
        return None

    if os.path.isabs(filename_str):
        if os.path.exists(filename_str):
            return filename_str
        return None

    # Try relative to GDB's CWD
    try:
        gdb_cwd_output = gdb.execute("pwd", to_string=True)
        if gdb_cwd_output:
             gdb_cwd = gdb_cwd_output.strip().splitlines()[0]
             path_in_gdb_cwd = os.path.join(gdb_cwd, filename_str)
             if os.path.exists(path_in_gdb_cwd):
                 return path_in_gdb_cwd
    except Exception:
        pass

    # Try paths from GDB parameter 'mpy-source-path'
    try:
        mpy_source_paths_param_val = gdb.parameter("mpy-source-path")
        if mpy_source_paths_param_val: # Check if it's not None or empty string
            # GDB parameters are strings. If it's meant to be a list, it's a pathsep-separated string.
            paths_to_check = str(mpy_source_paths_param_val).split(os.pathsep)
            for p_path in paths_to_check:
                if not p_path: continue # Skip empty paths from splitting "::"
                abs_path = os.path.join(p_path.strip(), filename_str)
                if os.path.exists(abs_path):
                    return abs_path
    except gdb.error:
        pass
    except Exception:
        pass

    # Try paths from environment variable MPY_SOURCE_PATH
    env_path_str = os.environ.get("MPY_SOURCE_PATH")
    if env_path_str:
        for p_path in env_path_str.split(os.pathsep):
            if not p_path: continue
            abs_path = os.path.join(p_path.strip(), filename_str)
            if os.path.exists(abs_path):
                return abs_path

    # Fallback: try filename as is (might be relative and work if GDB started in right dir)
    if os.path.exists(filename_str):
        return filename_str

    return None


def _gdb_helper_get_source_lines(filename_str, lineno_int, context_window_size=0):
    """
    Attempts to read a source line and optional context from a file.
    Returns a list of strings (source lines) or an empty list if not found/error.
    Prepends "    " (4 spaces) to each source line for formatting.
    """
    if not filename_str or filename_str.startswith("<") or lineno_int <= 0:
        return []

    full_path = _gdb_resolve_source_path(filename_str)
    if not full_path:
        # Be less verbose if file not found, as it's common for core/ROM modules
        # return [f"    <Source file '{filename_str}' not found in search paths>"]
        return []


    lines_to_return = []
    try:
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            all_lines = f.readlines()

        # Adjust lineno_int to be 0-indexed for list access
        target_line_idx = lineno_int - 1

        start_idx = max(0, target_line_idx - context_window_size)
        end_idx = min(len(all_lines), target_line_idx + 1 + context_window_size) # +1 because target_line_idx is 0-based

        if target_line_idx < 0 or target_line_idx >= len(all_lines):
             return [f"    <Line {lineno_int} out of range for '{os.path.basename(filename_str)}'>"]

        for i in range(start_idx, end_idx):
            line_prefix = "  -> " if i == target_line_idx else "     "
            # Indent source lines with 4 spaces to align nicely under the "File..." line
            lines_to_return.append(f"    {line_prefix}{all_lines[i].rstrip()}")

    except Exception: # Catch file read errors, etc.
        return [f"    <Error reading source '{os.path.basename(filename_str)}'>"]

    if not lines_to_return and lineno_int > 0:
        return [f"    <Line {lineno_int} not found in '{os.path.basename(filename_str)}' (but file was read)>"]

    return lines_to_return

# --- End Source Code Lookup Helpers ---

class MicroPythonHelper:
    try:
        return gdb.parameter("color") != "off"
    except:
        # If we can't determine, default to enabled
        return True

class MicroPythonHelper:
    def __init__(self):
        self.mp_state_ctx = None
        self.mp_state_vm = None
        # self.current_frame = None # Replaced by get_current_frame() logic
        self.exception_breakpoints = {}
        self.last_exception = None # For the most recent exception object
        self.exception_history = []  # Track exception history
        self.max_history = 10  # Maximum number of exceptions to track

        self.live_call_stack_frames = [] # Stores context of live frames for 'mpy-frame'
        self.selected_live_frame_index = -1 # Index for 'mpy-frame'

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

    def get_locals(self, frame_ptr_val: Optional[gdb.Value] = None) -> Dict[str, str]:
        """Get local variables from a given frame_ptr_val or the currently selected live frame."""
        target_frame_ptr = None

        if frame_ptr_val:
            target_frame_ptr = frame_ptr_val
        elif self.selected_live_frame_index != -1 and \
             0 <= self.selected_live_frame_index < len(self.live_call_stack_frames):
            target_frame_ptr = self.live_call_stack_frames[self.selected_live_frame_index]['frame_ptr_val']
        else:
            target_frame_ptr = self.get_current_frame()

        if not target_frame_ptr or target_frame_ptr.address == 0:
            return {}
        
        locals_dict = {}
        try:
            # This primarily handles dict-based locals (modules, classes, etc.)
            # Stack-based locals for functions are not fully handled here yet.
            locals_map_ptr = target_frame_ptr['locals_dict'] # Common member name for such dicts
            is_function_frame = False
            if hasattr(target_frame_ptr, 'locals_dict'):
                locals_map_ptr = target_frame_ptr['locals_dict']
                if locals_map_ptr and locals_map_ptr.address != 0:
                    locals_map = locals_map_ptr.dereference()
                    map_table = locals_map['table']
                    map_alloc = int(locals_map['alloc'])
                    sentinel_addr = 0
                    try:
                        sentinel_val = gdb.lookup_global_symbol('mp_const_map_elem_is_value_sentinel')
                        if sentinel_val: sentinel_addr = sentinel_val.value().address
                    except gdb.error: pass

                    for i in range(map_alloc):
                        entry = map_table[i]
                        key_obj = entry['key']
                        if key_obj != 0 and (sentinel_addr == 0 or key_obj.address != sentinel_addr):
                            name = self.get_qstr(key_obj)
                            value_obj = entry['value']
                            value_str = self.format_mp_obj(value_obj)
                            locals_dict[name] = value_str
                    if locals_dict: # Successfully got locals from a dict
                        return locals_dict
                is_function_frame = True # No locals_dict or it was empty, try stack
            else:
                is_function_frame = True # No 'locals_dict' field, assume stack locals

            if is_function_frame:
                fun_bc_ptr = target_frame_ptr['fun_bc']
                if fun_bc_ptr and fun_bc_ptr.address != 0:
                    fun_bc_obj = fun_bc_ptr.dereference()
                    num_pos_args = int(fun_bc_obj['n_pos_args'])
                    num_kwonly_args = int(fun_bc_obj['n_kwonly_args'])
                    num_total_args = num_pos_args + num_kwonly_args

                    # Attempt to get a pointer to the base of the stack area for this frame's locals
                    stack_locals_base_ptr = None
                    try:
                        if 'code_state' in target_frame_ptr.type.fields():
                            code_state_val = target_frame_ptr['code_state']
                            code_state_obj = None
                            if code_state_val.type.code == gdb.TYPE_CODE_PTR and code_state_val.address != 0:
                                code_state_obj = code_state_val.dereference()
                            elif code_state_val.type.code != gdb.TYPE_CODE_PTR: # Is a struct
                                code_state_obj = code_state_val

                            if code_state_obj:
                                if 'state' in code_state_obj.type.fields():
                                    stack_locals_base_ptr = code_state_obj['state']
                                elif 'state_v' in code_state_obj.type.fields(): # Another common name
                                    stack_locals_base_ptr = code_state_obj['state_v']
                                # TODO: Could also check target_frame_ptr['sp'] and work backwards if n_state is known
                    except gdb.error: pass # Silently ignore if fields are not there

                    if stack_locals_base_ptr and stack_locals_base_ptr.address != 0:
                        # Try to determine number of locals on stack from n_state if possible
                        # This is highly dependent on n_state encoding (see py/bc.h)
                        # For now, we will just display up to num_total_args
                        # A more complete solution would parse n_state for total locals.
                        # unsigned int n_state_val = fun_bc_obj['n_state'];
                        # unsigned int n_locals_from_state = (n_state_val >> MP_BC_NUM_STATE_LOCAL_SHIFT) & MP_BC_NUM_STATE_LOCAL_MASK;
                        # The above shifts/masks are from C, need to be known for GDB.
                        # Let's assume num_locals_to_display = num_total_args for now.
                        # If a field like fun_bc_obj['n_locals_on_stack'] existed, it would be used.

                        for i in range(num_total_args): # Only show arguments for now
                            try:
                                local_obj = stack_locals_base_ptr[i] # mp_obj_t
                                # Argument names are still hard. Using generic names.
                                locals_dict[f"<arg{i}>"] = self.format_mp_obj(local_obj)
                            except Exception as e_val:
                                locals_dict[f"<arg{i}>"] = f"<error: {e_val}>"

                        # If we wanted to show other stack slots (non-arg locals) without names:
                        # num_all_stack_slots = ... (from n_state)
                        # for i in range(num_total_args, num_all_stack_slots):
                        #    try:
                        #        local_obj = stack_locals_base_ptr[i]
                        #        locals_dict[f"<stack_var{i-num_total_args}>"] = self.format_mp_obj(local_obj)
                        #    except Exception as e_val:
                        #        locals_dict[f"<stack_var{i-num_total_args}>"] = f"<error: {e_val}>"

                    else: # Could not determine stack_locals_base_ptr
                        if not locals_dict and num_total_args > 0:
                            for i in range(num_total_args):
                                locals_dict[f"<arg{i}>"] = "<stack base unknown>"

                    if not locals_dict: # If still empty after trying stack
                         locals_dict["<info>"] = "<function frame: no dict locals, stack locals not fully resolved>"

        except gdb.error: # Catches GDB errors from field access etc.
            # locals_dict might be partially filled or empty
            if not locals_dict: locals_dict["<error>"] = "<GDB error accessing frame details>"
        except Exception as e_py: # Catches Python errors in this script
            if not locals_dict: locals_dict["<error>"] = f"<Python error: {type(e_py).__name__}>"
        
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
        # It starts from MP_STATE_VM(thread)['frame']
        frame_ptr = self.get_current_frame() # This gets self.mp_state_vm['frame']

        # Clear previous stack info and reset selected frame
        self.live_call_stack_frames = []
        self.selected_live_frame_index = -1

        if not frame_ptr or frame_ptr.address == 0: # Check address too for null pointers
            return ["<No live Python stack frames>"]

        formatted_backtrace_display_list = []
        try:
            frame_idx = 0
            while frame_ptr and frame_ptr.address != 0: # Ensure frame_ptr itself is not null
                fun_name = "<module>" # Default if no function context (e.g., top level module code)
                source_file_str = "<unknown_file>"
                line_num_str = "<unknown_line>"

                # mp_frame_t has 'fun_bc' which is mp_obj_fun_bc_t*
                fun_bc_ptr = frame_ptr['fun_bc']
                if fun_bc_ptr and fun_bc_ptr.address != 0:
                    try:
                        fun_bc_obj = fun_bc_ptr.dereference()

                        # Get function name
                        qstr_name = fun_bc_obj['name']
                        if qstr_name != 0: # qstr 0 can mean anonymous/lambda etc.
                            fun_name = self.get_qstr(qstr_name)

                        # Get source file
                        qstr_file = fun_bc_obj['source_file']
                        if qstr_file != 0:
                            source_file_str = self.get_qstr(qstr_file)

                        # Get start line of the function.
                        # Getting precise current IP's line number is complex from GDB python.
                        # mp_bytecode_get_source_line_from_ip would be needed.
                        # Using function's start_line as an approximation.
                        start_line = int(fun_bc_obj['start_line'])
                        line_num_str = str(start_line)
                        if source_file_str == "?" and fun_name == "<module>": # often means REPL
                             source_file_str = "<stdin>" # Or <REPL>

                    except gdb.error as e:
                        # Handle cases where fun_bc_ptr might be invalid or fields missing
                        fun_name = f"<error reading fun_bc: {e}>"

                frame_line_str = f"  File \"{source_file_str}\", line {line_num_str}, in {fun_name}"
                formatted_backtrace.append(frame_line_str)

                current_line_int = 0
                if line_num_str.isdigit():
                    current_line_int = int(line_num_str)

                if current_line_int > 0:
                    source_context_lines = _gdb_helper_get_source_lines(source_file_str, current_line_int, 0)
                    formatted_backtrace.extend(source_context_lines)

                # Store context for mpy-frame command
                line_num_int = 0
                if line_num_str.isdigit():
                    line_num_int = int(line_num_str)

                frame_context = {
                    'frame_ptr_val': frame_ptr,
                    'source_file': source_file_str,
                    'line_num': line_num_int, # Store as int
                    'func_name': fun_name,
                    'display_str': frame_line_str # The string already formatted for display
                }
                self.live_call_stack_frames.append(frame_context)

                # Add source context lines to the display list
                if current_line_int > 0: # current_line_int was from int(line_num_str)
                    source_context_lines = _gdb_helper_get_source_lines(source_file_str, current_line_int, 0)
                    formatted_backtrace_display_list.extend(source_context_lines)

                if frame_ptr['prev_frame'] == frame_ptr: # Avoid infinite loop on bad frame linkage
                     formatted_backtrace_display_list.append("  <Error: Frame points to itself>")
                     break
                frame_ptr = frame_ptr['prev_frame'] # mp_frame_t has 'prev_frame'
                frame_idx += 1
                if frame_idx > 50: # Safety break for very deep or corrupt stacks
                    formatted_backtrace_display_list.append("  <Backtrace truncated due to depth limit>")
                    break

        except Exception as e:
            formatted_backtrace_display_list.append(f"<Error during live backtrace generation: {e}>")

        if not formatted_backtrace_display_list:
            return ["<No live Python stack frames processed>"]
        return formatted_backtrace_display_list

    def get_exception_traceback(self, exc_obj: gdb.Value) -> List[str]:
        """Get the stored traceback from an exception object."""
        # exc_obj is mp_obj_exception_t*
        frames = []
        try:
            # mp_obj_exception_t has 'traceback' member, which is mp_exc_stack_t*
            tb_data_ptr = exc_obj["traceback"]

            if not tb_data_ptr or tb_data_ptr.address == 0:
                # Some exceptions might not have a traceback (e.g. raised from C, or very early)
                return ["  <No stored traceback available for this exception>"]

            frame_idx = 0
            while tb_data_ptr and tb_data_ptr.address != 0:
                # mp_exc_stack_t has 'file' (qstr), 'line' (mp_uint_t), 'next' (mp_exc_stack_t*)
                file_name_qstr = tb_data_ptr["file"]
                line_num = int(tb_data_ptr["line"])

                file_name_str = self.get_qstr(file_name_qstr)
                if file_name_str == "?":
                    file_name_str = "<unknown_file_in_traceback>"

                # Function name is not available in mp_exc_stack_t
                # So, we use the simpler format here.
                frame_line_str = f"  File \"{file_name_str}\", line {line_num}"
                frames.append(frame_line_str)

                if line_num > 0:
                    source_context_lines = _gdb_helper_get_source_lines(file_name_str, line_num, 0)
                    frames.extend(source_context_lines)

                if tb_data_ptr['next'] == tb_data_ptr: # Avoid infinite loop
                    frames.append("  <Error: Traceback frame points to itself>")
                    break
                tb_data_ptr = tb_data_ptr["next"]
                frame_idx +=1
                if frame_idx > 50:
                    frames.append("  <Stored traceback truncated due to depth limit>")
                    break

        except Exception as e:
            frames.append(f"<Error getting stored traceback: {e}>")

        if not frames:
             return ["  <No valid frames in stored traceback>"]
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
            # Standard attributes are often part of the 'args' tuple.
            # For specific exception types, we can parse 'args' more intelligently.
            exc_type_str = self.get_obj_type(exc_obj["base"]["type"]) # Get type name as string

            if args_obj and args_obj['len'] > 0: # If there are args
                if exc_type_str == "OSError":
                    if args_obj['len'] >= 1:
                        try:
                            errno_val = args_obj['items'][0]
                            attributes["errno"] = self.format_mp_obj(errno_val)
                        except:
                            attributes["errno"] = "<error parsing>"
                    if args_obj['len'] >= 2:
                        try:
                            # strerror is often not directly part of OSError args in MPy,
                            # but os.strerror(errno) is used.
                            # If it's present, it's usually the second arg for some custom OSErrors.
                            # For now, we'll just show what's in args.
                            # A more advanced version could call os.strerror if available.
                            pass # Not adding strerror directly from args unless sure of format
                        except:
                            pass
                    # filename could be args[2] for some OSErrors
                elif exc_type_str == "SyntaxError":
                    # args for SyntaxError: (msg, (filename, lineno, offset, text))
                    if args_obj['len'] >= 1:
                        attributes["msg"] = self.format_mp_obj(args_obj['items'][0])
                    if args_obj['len'] >= 2:
                        details_tuple = args_obj['items'][1]
                        if self.get_obj_type(details_tuple) == "tuple" and details_tuple['len'] == 4:
                            try:
                                attributes["filename"] = self.format_mp_obj(details_tuple['items'][0])
                                attributes["lineno"] = self.format_mp_obj(details_tuple['items'][1])
                                attributes["offset"] = self.format_mp_obj(details_tuple['items'][2])
                                attributes["text"] = self.format_mp_obj(details_tuple['items'][3])
                            except:
                                attributes["details_tuple"] = "<error parsing>"
                # Add other specific exception types here if needed

            # Fallback for other common attributes if not specifically parsed (less likely to work directly)
            # common_attrs_fallback = ["message"] # "errno", "strerror", etc. are usually not direct members
            # for attr_name in common_attrs_fallback:
            #     try:
            #         # This direct member access is unlikely to work for mp_obj_exception_t
            #         # but kept for conceptual completeness if some exceptions have direct fields.
            #         attr_gdb_val = exc_obj[attr_name]
            #         if attr_gdb_val: # Check if the gdb.Value itself is non-null/valid
            #             attributes[attr_name] = self.format_mp_obj(attr_gdb_val)
            #     except gdb.error: # Catch GDB errors if member doesn't exist
            #         pass
            #     except Exception: # Catch other Python errors during formatting
            #         pass

        except Exception as e:
            # This catches errors from the specific type parsing (OSError, SyntaxError)
            attributes["error_parsing_typed_attributes"] = str(e)

        # Now, try to get instance members if it's an mp_obj_instance_t
        # This applies to user-defined exceptions and potentially some built-ins if they use the instance layout.
        try:
            # The mp_obj_exception_t is the base for exception instances.
            # If it's a user-defined class, it's an mp_obj_instance_t.
            # We attempt to access its 'members' map.
            # A gdb.error will be raised if 'members' is not a field of the concrete type of exc_obj.

            # First, ensure exc_obj is not a NULL pointer before trying to cast and dereference.
            if exc_obj.address == 0:
                pass # Cannot get members from a NULL object
            else:
                # Attempt to cast to mp_obj_instance_t* and access members.
                # This assumes the layout of mp_obj_exception_t for user classes
                # is compatible with mp_obj_instance_t at least up to the 'members' field.
                instance_obj_ptr = exc_obj.cast(gdb.lookup_type('mp_obj_instance_t').pointer())
                instance_members_map_ptr = instance_obj_ptr['members']

                if instance_members_map_ptr and instance_members_map_ptr.address != 0:
                    members_map = instance_members_map_ptr.dereference() # mp_map_t
                    map_table = members_map['table']
                    map_alloc = int(members_map['alloc'])

                    # Sentinel value for mp_map_elem_t.key when slot is deleted
                    # mp_const_map_elem_is_value_sentinel is not directly accessible as a gdb symbol easily
                    # but deleted keys are often specific non-NULL pointers.
                    # However, active keys are just not MP_OBJ_NULL.

                    for i in range(map_alloc):
                        map_elem = map_table[i]
                        key_obj = map_elem['key']

                        # Valid keys are not MP_OBJ_NULL (0) and not MP_OBJ_SENTINEL (a specific marker)
                        # For simplicity here, checking against 0 is a good first pass for active slots.
                        # A more robust check would involve knowing MP_OBJ_SENTINEL's value.
                        if key_obj != 0 : # If key is not MP_OBJ_NULL
                            # Further check to ensure it's not MP_OBJ_SENTINEL if its value is known
                            # if key_obj.address == address_of_mp_const_sentinel: continue

                            try:
                                attr_name_str = self.get_qstr(key_obj)
                                value_obj = map_elem['value']
                                attr_val_str = self.format_mp_obj(value_obj)

                                # Prefix to distinguish from args-derived attributes, or handle potential overwrite.
                                # For now, add directly. If key exists from args parsing, it might be overwritten.
                                attributes[f"{attr_name_str}"] = attr_val_str
                            except Exception:
                                # Skip this member if there's an error formatting it
                                pass
        except gdb.error:
            # This gdb.error can occur if 'members' field doesn't exist for exc_obj's actual type,
            # or if the cast to mp_obj_instance_t* was inappropriate for this specific exception object.
            # This is a silent fallback: means no instance members were found or accessible this way.
            pass
        except Exception as e_outer:
            # Catch other Python errors during this process
            attributes["error_parsing_instance_members"] = str(e_outer)
        
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
        processed_traceback_lines = []
        for frame_line_or_source in exc_info['traceback']:
            # Check if it's a main frame descriptor line
            if frame_line_or_source.strip().startswith("File \""):
                # Try to match format with optional 'in function_name' part
                match = re.match(r'  File "(.*)", line ([^,]+)(?:, in (.*))?', frame_line_or_source.strip())
                if match:
                    file_name, line_num, func_name = match.groups() # func_name can be None
                    func_name_part = f", in {Colors.colorize(func_name, Colors.YELLOW)}" if func_name else ""
                    formatted_frame = f"  File \"{Colors.colorize(file_name, Colors.GREEN)}\", line {Colors.colorize(line_num, Colors.MAGENTA)}{func_name_part}"
                    processed_traceback_lines.append(formatted_frame)
                else:
                    # Fallback if regex doesn't match complex frame string (should not happen ideally)
                    processed_traceback_lines.append(frame_line_or_source)
            else:
                # This is a source code line or an error/info message from traceback generation
                processed_traceback_lines.append(frame_line_or_source)
        
        # Format attributes if available and detailed mode is on
        attributes_section = ""
        if detailed and exc_info.get('attributes'):
            attributes_header = Colors.colorize("\nException Attributes:", Colors.CYAN, bold=True)
            attributes_lines = []
            # Sort attributes by key for consistent display
            for key, value in sorted(exc_info['attributes'].items()):
                attributes_lines.append(f"  {Colors.colorize(key, Colors.GREEN)}: {value}")

            if attributes_lines:
                attributes_section = f"{attributes_header}\n" + "\n".join(attributes_lines)
            else:
                # Only show header if detailed view was requested, even if no attributes found
                attributes_section = f"{attributes_header}\n  {Colors.colorize('<No specific attributes found>', Colors.YELLOW)}"
        
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
        # get_locals() will now use the selected frame if available,
        # or fallback to current VM frame.
        locals_dict = self.mpy.get_locals() # No args, uses selected_live_frame_index internally

        header_printed = False
        if self.mpy.selected_live_frame_index != -1 and \
           0 <= self.mpy.selected_live_frame_index < len(self.mpy.live_call_stack_frames):
            selected_frame_info = self.mpy.live_call_stack_frames[self.mpy.selected_live_frame_index]
            print(Colors.colorize(f"Locals for selected MicroPython frame #{self.mpy.selected_live_frame_index}:", Colors.CYAN))
            print(f"{selected_frame_info['display_str']}")
            source_lines = _gdb_helper_get_source_lines(selected_frame_info['source_file'], selected_frame_info['line_num'], 0)
            for line in source_lines:
                print(line)
            header_printed = True
        else:
            # Check if get_locals() fell back to current VM frame and got something
            if locals_dict:
                 print(Colors.colorize("Locals for current MicroPython VM frame:", Colors.CYAN))
                 # Optionally display current VM frame info if easily accessible and not redundant
                 header_printed = True

        if locals_dict:
            if not header_printed:
                 print(Colors.colorize("Locals for current MicroPython VM frame:", Colors.CYAN))
            for name, value in sorted(locals_dict.items()):
                print(f"  {Colors.colorize(name, Colors.GREEN)} = {value}")

            has_generic_names = any(k.startswith("<arg") or k.startswith("<local") or k.startswith("<stack_var") for k in locals_dict.keys())
            is_info_only = all(k.startswith(("<info", "<error")) for k in locals_dict.keys())

            if has_generic_names:
                print(Colors.colorize("  (Note: Some argument/local names are generic placeholders. Full name resolution for stack variables is complex.)", Colors.YELLOW))
            elif not locals_dict or (len(locals_dict) == 1 and is_info_only and not has_generic_names): # Empty or only contains info/error
                 # This condition needs to be careful not to suppress valid info/error messages if locals_dict only contains them
                 if not is_info_only : # if it's truly empty of vars, not just an info message
                    print(Colors.colorize("  <No specific local variables found for this frame>", Colors.YELLOW))

        elif header_printed:
            print(Colors.colorize("  <No locals available for this frame type/selection>", Colors.YELLOW))
            # Check if the only content is an info/error message from get_locals
            is_info_only_for_empty = all(k.startswith(("<info", "<error")) for k in locals_dict.keys()) if locals_dict else True
            if not (locals_dict and is_info_only_for_empty): # if not just an error/info message explaining why it's empty
                print(Colors.colorize("  (Attempted stack variable retrieval; full name/value support is work-in-progress.)", Colors.YELLOW))
        else:
            print(Colors.colorize("No valid MicroPython frame context or no locals found.", Colors.YELLOW))


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
        # get_backtrace populates self.mpy.live_call_stack_frames
        # and returns a list of strings already formatted with source for direct display.
        # For mpy-bt, we want to show the frame numbers and selection marker based on live_call_stack_frames.
        self.mpy.get_backtrace() # This call refreshes self.mpy.live_call_stack_frames

        if self.mpy.live_call_stack_frames:
            print(Colors.colorize("Python backtrace (live):", Colors.CYAN, bold=True))
            for idx, frame_ctx in enumerate(self.mpy.live_call_stack_frames):
                # frame_ctx is like {'frame_ptr_val': ..., 'source_file': ..., 'line_num': ...,
                #                    'func_name': ..., 'display_str': ...}
                selector = Colors.colorize(" =>", Colors.YELLOW) if idx == self.mpy.selected_live_frame_index else f"#{idx}:"

                # Print the main frame display string (already starts with "  File...")
                print(f"{selector}{frame_ctx['display_str']}")

                # Print associated source lines for this frame
                # These are now fetched again here to ensure correct association if context_window changes
                source_lines = _gdb_helper_get_source_lines(frame_ctx['source_file'], frame_ctx['line_num'], 0)
                for srcline in source_lines:
                    # _gdb_helper_get_source_lines already prepends "    " and "  -> " or "     "
                    # We might want a bit more indentation under the frame selector line.
                    # Let's assume _gdb_helper_get_source_lines provides sufficient leading spaces.
                    print(srcline)
        else:
            # Check if get_backtrace returned an info string like ["<No live Python stack frames>"]
            # The list might be empty if get_current_frame() was None initially.
            # live_call_stack_frames would be empty in that case.
            print(Colors.colorize("No Python backtrace available (or an error occurred during generation).", Colors.YELLOW))


class MPyFrameCommand(gdb.Command):
    """Select and display a MicroPython live stack frame.
Usage: mpy-frame [index]
If no index, shows current selection. If index is provided, selects that frame.
Shows frame details and its local variables."""

    def __init__(self, mpy_helper: MicroPythonHelper):
        super().__init__("mpy-frame", gdb.COMMAND_STACK, gdb.COMPLETE_NONE)
        self.mpy = mpy_helper

    def invoke(self, arg: str, from_tty: bool) -> None:
        if not self.mpy.live_call_stack_frames:
            # Try to generate it if it's empty, in case mpy-bt wasn't run first
            self.mpy.get_backtrace()
            if not self.mpy.live_call_stack_frames:
                print(Colors.colorize("No live call stack captured. Use 'mpy-bt' first if stack is empty.", Colors.YELLOW))
                return

        if not arg: # No argument, print current selection
            if self.mpy.selected_live_frame_index == -1 or \
               self.mpy.selected_live_frame_index >= len(self.mpy.live_call_stack_frames):
                print(Colors.colorize("No frame currently selected.", Colors.YELLOW))
                print(f"Use 'mpy-bt' to see frames, then 'mpy-frame <index>' to select one.")
            else:
                frame_context = self.mpy.live_call_stack_frames[self.mpy.selected_live_frame_index]
                print(Colors.colorize(f"Currently selected MicroPython frame #{self.mpy.selected_live_frame_index}:", Colors.CYAN))
                print(frame_context['display_str']) # Already starts with "  "
                source_lines = _gdb_helper_get_source_lines(frame_context['source_file'], frame_context['line_num'], 0)
                for line in source_lines:
                    print(line) # Already formatted with leading spaces

                print(Colors.colorize("\nLocals for this frame:", Colors.CYAN))
                frame_ptr_val = frame_context['frame_ptr_val']
                locals_dict = self.mpy.get_locals(frame_ptr_val=frame_ptr_val)
                if locals_dict:
                    for name, value in sorted(locals_dict.items()):
                        print(f"  {Colors.colorize(name, Colors.GREEN)} = {value}")
                else:
                    print(Colors.colorize("  <No locals available or applicable for this frame type>", Colors.YELLOW))
            return

        try:
            index = int(arg)
            if not (0 <= index < len(self.mpy.live_call_stack_frames)):
                print(Colors.colorize(f"Error: Frame index {index} is out of bounds (0-{len(self.mpy.live_call_stack_frames)-1}).", Colors.RED))
                return

            self.mpy.selected_live_frame_index = index
            selected_frame_context = self.mpy.live_call_stack_frames[index]

            print(Colors.colorize(f"Selected MicroPython frame #{index}:", Colors.CYAN))
            # display_str already starts with "  File..."
            print(selected_frame_context['display_str'])
            source_lines = _gdb_helper_get_source_lines(selected_frame_context['source_file'], selected_frame_context['line_num'], 0)
            for line in source_lines:
                print(line) # Already has leading spaces

            print(Colors.colorize("\nLocals for this frame:", Colors.CYAN))
            frame_ptr_val = selected_frame_context['frame_ptr_val']
            locals_dict = self.mpy.get_locals(frame_ptr_val=frame_ptr_val)
            if locals_dict:
                for name, value in sorted(locals_dict.items()):
                    print(f"  {Colors.colorize(name, Colors.GREEN)} = {value}")

                has_generic_names = any(k.startswith("<arg") or k.startswith("<local") or k.startswith("<stack_var") for k in locals_dict.keys())
                is_info_only = all(k.startswith(("<info", "<error")) for k in locals_dict.keys())

                if has_generic_names:
                    print(Colors.colorize("  (Note: Some argument/local names are generic placeholders. Full name resolution for stack variables is complex.)", Colors.YELLOW))
                elif not any(locals_dict) or (len(locals_dict) == 1 and is_info_only and not has_generic_names) :
                     if not is_info_only :
                        print(Colors.colorize("  <No specific local variables found for this frame>", Colors.YELLOW))
            else: # locals_dict is empty from the start
                print(Colors.colorize("  <No locals available or applicable for this frame type>", Colors.YELLOW))
                print(Colors.colorize("  (Attempted stack variable retrieval; full name/value support is work-in-progress.)", Colors.YELLOW))

        except ValueError:
            print(Colors.colorize(f"Error: Invalid frame index '{arg}'. Must be an integer.", Colors.RED))
        except Exception as e:
            print(Colors.colorize(f"Error selecting/displaying frame: {e}", Colors.RED))


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
            base_condition = f"exc != 0 && mp_obj_get_type(exc) == mp_type_{exc_type}"
            if catch_type == "uncaught":
                base_condition += " && mp_state_ctx.thread.state.exc_state.handler == 0"

            final_condition = base_condition
            if custom_cond_str: # custom_cond_str is built by the new parsing logic
                final_condition += f" && {custom_cond_str}"

            bp.condition = final_condition
            self.mpy.exception_breakpoints[exc_type] = bp # Assuming self.mpy exists
            print(Colors.colorize(f"Will break on {catch_type} {exc_type} if: {final_condition}", Colors.GREEN))
        except Exception as e:
            print(Colors.colorize(f"Error setting exception breakpoint: {e}", Colors.RED))
            if 'final_condition' in locals():
                 print(Colors.colorize(f"Generated condition was: {final_condition}", Colors.YELLOW))

# Helper functions for GDB conditions (module level)
# These are called by GDB's 'python' command in breakpoint conditions.
# 'exc_addr' is expected to be the address of the mp_obj_exception_t * (i.e., the mp_obj_t value of the exception)

def _gdb_helper_get_mp_obj_as_int(mp_obj_addr):
    if mp_obj_addr == 0: return None
    mp_obj = gdb.Value(mp_obj_addr)
    if (int(mp_obj) & 1): # MP_OBJ_IS_SMALL_INT
        return int(mp_obj) >> 1
    # Add more for full int objects if necessary, for now only small int
    return None

def _gdb_helper_get_mp_obj_as_str(mp_obj_addr):
    if mp_obj_addr == 0: return None
    mp_obj = gdb.Value(mp_obj_addr)

    # Simplified string fetching - this needs to be robust like in MicroPythonHelper.format_mp_obj
    # This is a placeholder and likely needs the full qstr/str object handling
    try:
        # Assuming mp_obj is a pointer to mp_obj_base_t if it's not a small int
        if not (int(mp_obj) & 1): # Not a small int
            base = mp_obj.cast(gdb.lookup_type('mp_obj_base_t').pointer())
            obj_type = base['type']
            type_name_qstr = obj_type['name'] # This is a qstr value

            # This is a very simplified way to compare type_name_qstr with mp_type_str's name qstr
            # A proper way would be to get string from type_name_qstr and compare
            # Or compare the type pointer directly: obj_type == gdb.lookup_type('mp_type_str').pointer()
            # For now, let's assume if we need a string, we try to cast and access.
            # This part is complex because we don't have the full mpy_helper context here.

            # Attempt to cast to mp_obj_str_t and get data
            # This check for type is crucial and hard to do generically here
            # For demonstration, let's assume if it's not other known immediate types, it might be a str ptr.
            # A real implementation would need to call something like mpy_helper.get_qstr or format_mp_obj.
            # This is a significant simplification:
            if obj_type.address == gdb.lookup_type("mp_type_str").pointer().address:
                 str_obj = mp_obj.cast(gdb.lookup_type('mp_obj_str_t').pointer())
                 str_len = int(str_obj['len'])
                 str_data_ptr = str_obj['data'] # This is const byte*
                 # GDB's string() method might not work directly on const byte* if it expects char*
                 # Fetch byte by byte or use gdb.Value.string() if available and works
                 # For now, returning raw pointer for GDB to handle or further process
                 # This is insufficient for direct regex in python.
                 # Let's assume we can fetch it as bytes.
                 # py_bytes = str_data_ptr.lazy_string(length=str_len) # GDB 7.7+
                 # return py_bytes.decode('utf-8', errors='replace')
                 # The above is too modern. Let's try simpler read.
                 return str_data_ptr.string(length=str_len) # Hope this works
    except Exception:
        return None
    return None


def _gdb_helper_get_exc_arg_obj_addr(exc_addr, arg_idx):
    """Gets the mp_obj_t address of an argument from the exception object."""
    if exc_addr == 0: return 0
    try:
        exc_val = gdb.Value(exc_addr).cast(gdb.lookup_type('mp_obj_exception_t').pointer())
        args_tuple_ptr = exc_val['args']
        if not args_tuple_ptr or args_tuple_ptr.address == 0: return 0

        args_tuple_obj = args_tuple_ptr.dereference()
        if arg_idx >= int(args_tuple_obj['len']): return 0

        return int(args_tuple_obj['items'][arg_idx]) # Return the mp_obj_t value (address or tagged int)
    except Exception:
        return 0


def gdb_helper_compare_exc_arg_int(exc_obj_addr, arg_idx_int, expected_val_int, op_str):
    arg_obj_addr = _gdb_helper_get_exc_arg_obj_addr(exc_obj_addr, arg_idx_int)
    if arg_obj_addr == 0: return False

    actual_val = _gdb_helper_get_mp_obj_as_int(arg_obj_addr)
    if actual_val is None: return False

    if op_str == "==": return actual_val == expected_val_int
    if op_str == "!=": return actual_val != expected_val_int
    if op_str == ">": return actual_val > expected_val_int
    if op_str == "<": return actual_val < expected_val_int
    if op_str == ">=": return actual_val >= expected_val_int
    if op_str == "<=": return actual_val <= expected_val_int
    return False

def gdb_helper_match_exc_arg_str(exc_obj_addr, arg_idx_int, pattern_str, match_type_str):
    arg_obj_addr = _gdb_helper_get_exc_arg_obj_addr(exc_obj_addr, arg_idx_int)
    if arg_obj_addr == 0: return False

    actual_str = _gdb_helper_get_mp_obj_as_str(arg_obj_addr)
    if actual_str is None: return False

    try:
        if match_type_str == "matches":
            return bool(re.search(pattern_str, actual_str))
        if match_type_str == "contains":
            return pattern_str in actual_str
    except Exception: # e.g. regex error
        return False
    return False


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
        MPyFrameCommand(mpy) # Register new command
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