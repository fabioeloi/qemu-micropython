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

class MicroPythonHelper:
    def __init__(self):
        self.mp_state_ctx = None
        self.mp_state_vm = None
        self.current_frame = None
        self.exception_breakpoints = {}
        self.last_exception = None

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
            
            return {
                "type": self.get_obj_type(exc),
                "value": self.format_mp_obj(exc),
                "traceback": self.get_exception_traceback(exc)
            }
        except:
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
            print(f"Will break on {catch_type} {exc_type} exceptions")
        except Exception as e:
            print(f"Error setting exception breakpoint: {e}")

class MPExceptInfoCommand(gdb.Command):
    """Show information about the current exception"""
    
    def __init__(self, mpy: MicroPythonHelper):
        super().__init__("mpy-except-info", gdb.COMMAND_USER)
        self.mpy = mpy
    
    def invoke(self, arg: str, from_tty: bool) -> None:
        exc_info = self.mpy.get_exception_info()
        if not exc_info:
            print("No active exception")
            return
        
        print(f"Exception Type: {exc_info['type']}")
        print(f"Exception Value: {exc_info['value']}")
        print("\nTraceback:")
        for frame in exc_info['traceback']:
            print(frame)

class MPExceptBTCommand(gdb.Command):
    """Show exception backtrace"""
    
    def __init__(self, mpy: MicroPythonHelper):
        super().__init__("mpy-except-bt", gdb.COMMAND_USER)
        self.mpy = mpy
    
    def invoke(self, arg: str, from_tty: bool) -> None:
        exc_info = self.mpy.get_exception_info()
        if not exc_info:
            print("No active exception")
            return
        
        print("Exception Traceback:")
        for frame in exc_info['traceback']:
            print(frame)

class MPExceptVarsCommand(gdb.Command):
    """Show variables at exception point"""
    
    def __init__(self, mpy: MicroPythonHelper):
        super().__init__("mpy-except-vars", gdb.COMMAND_USER)
        self.mpy = mpy
    
    def invoke(self, arg: str, from_tty: bool) -> None:
        frame = self.mpy.get_current_frame()
        if not frame:
            print("No active frame")
            return
        
        print("Local variables at exception point:")
        locals_dict = frame["locals"]
        for i in range(int(locals_dict["map"]["alloc"])):
            key = locals_dict["map"]["table"][i]["key"]
            value = locals_dict["map"]["table"][i]["value"]
            if key:
                name = self.mpy.format_mp_obj(key)
                val = self.mpy.format_mp_obj(value)
                print(f"  {name} = {val}")

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
        print("MicroPython GDB helpers loaded successfully")
    except Exception as e:
        print(f"Error registering MicroPython commands: {e}")

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