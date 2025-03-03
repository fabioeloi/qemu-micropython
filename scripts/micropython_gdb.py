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
from typing import Optional, Dict, List

class MicroPythonHelper:
    def __init__(self):
        self.mp_state_ctx = None
        self.mp_state_vm = None
        self.current_frame = None

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
        
        return f"<{obj_type}>"

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

def register_micropython_commands():
    """Register MicroPython-specific GDB commands"""
    try:
        mpy = MicroPythonHelper()
        MPLocalsCommand(mpy)
        MPGlobalsCommand(mpy)
        MPBacktraceCommand(mpy)
        print("MicroPython GDB helpers loaded successfully")
    except Exception as e:
        print(f"Error registering MicroPython commands: {e}")

if __name__ == '__main__':
    register_micropython_commands() 