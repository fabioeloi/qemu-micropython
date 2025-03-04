import gdb
import os
import sys
import json
import re
from datetime import datetime

# Add the scripts directory to the Python path
workspace_folder = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(workspace_folder, "scripts"))

# Import the MicroPython GDB helper
try:
    from micropython_gdb import MicroPythonHelper, Colors, is_color_enabled
except ImportError:
    print("Error: Could not import MicroPython GDB helper")
    print(f"Looking in: {os.path.join(workspace_folder, 'scripts')}")
    print(f"Python path: {sys.path}")
    
    # Create minimal color class as fallback
    class Colors:
        RESET = "\033[0m"
        BOLD = "\033[1m"
        RED = "\033[31m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        BLUE = "\033[34m"
        MAGENTA = "\033[35m"
        CYAN = "\033[36m"
        
    def is_color_enabled():
        return True
    
    class MicroPythonHelper:
        def get_exception_info(self):
            return {"type": "Unknown", "value": "Error loading MicroPython helper"}

class VSCodeExceptionHandler:
    def __init__(self):
        self.mpy = MicroPythonHelper()
        self.output_dir = os.path.join(workspace_folder, ".vscode")
        self.output_file = os.path.join(self.output_dir, "exception_info.json")
        self.history_file = os.path.join(self.output_dir, "exception_history.json")
        self.exception_history = []
        self.load_history()
        self.register_commands()
        
    def load_history(self):
        """Load exception history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r") as f:
                    self.exception_history = json.load(f)
        except Exception as e:
            print(f"Error loading exception history: {e}")
            self.exception_history = []
            
    def save_history(self):
        """Save exception history to file"""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            with open(self.history_file, "w") as f:
                json.dump(self.exception_history, f, indent=2)
        except Exception as e:
            print(f"Error saving exception history: {e}")
        
    def register_commands(self):
        """Register GDB event handlers and commands"""
        # Register a breakpoint handler for exceptions
        gdb.events.stop.connect(self.on_stop)
        
        # Register custom commands
        VSCodeExceptInfoCommand(self)
        VSCodeExceptVisualizeCommand(self)
        
    def on_stop(self, event):
        """Handle GDB stop events"""
        try:
            # Check if we stopped due to an exception
            frame = gdb.selected_frame()
            if frame and "mp_raise" in frame.name():
                # Get exception information
                exc_info = self.mpy.get_exception_info()
                if exc_info:
                    # Add timestamp
                    exc_info["timestamp"] = datetime.now().isoformat()
                    
                    # Format for VSCode
                    self.format_for_vscode(exc_info)
                    
                    # Add to history
                    self.add_to_history(exc_info)
        except Exception as e:
            print(f"Error in exception handler: {e}")
                    
    def format_for_vscode(self, exc_info):
        """Format exception information for VSCode"""
        vscode_info = {
            "type": exc_info.get("type", "Unknown"),
            "value": exc_info.get("value", ""),
            "traceback": exc_info.get("traceback", []),
            "attributes": exc_info.get("attributes", {}),
            "locals": exc_info.get("locals", {}),
            "timestamp": exc_info.get("timestamp", datetime.now().isoformat())
        }
        
        # Write to file for VSCode extension to read
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            with open(self.output_file, "w") as f:
                json.dump(vscode_info, f, indent=2)
            
            # Print notification
            c = Colors if is_color_enabled() else type('obj', (object,), {'BOLD': '', 'RED': '', 'RESET': ''})
            print(f"\n{c.BOLD}Exception detected:{c.RESET}")
            print(f"  Type: {c.RED}{vscode_info['type']}{c.RESET}")
            print(f"  Value: {vscode_info['value']}")
            print(f"  Details saved to: {self.output_file}")
            print(f"  Use {c.BOLD}vscode-except-info{c.RESET} or {c.BOLD}vscode-except-visualize{c.RESET} to view details")
        except Exception as e:
            print(f"Error saving exception info: {e}")
            
    def add_to_history(self, exc_info):
        """Add exception to history"""
        # Limit history size
        MAX_HISTORY = 10
        
        # Add to history
        self.exception_history.append(exc_info)
        
        # Trim history if needed
        if len(self.exception_history) > MAX_HISTORY:
            self.exception_history = self.exception_history[-MAX_HISTORY:]
            
        # Save history
        self.save_history()
        
    def get_exception_history(self):
        """Get exception history"""
        return self.exception_history
        
    def visualize_exception(self, index=-1):
        """Visualize exception at given index"""
        if not self.exception_history:
            print("No exceptions in history")
            return
            
        # Get exception info
        if index < 0 or index >= len(self.exception_history):
            exc_info = self.exception_history[-1]
        else:
            exc_info = self.exception_history[index]
            
        # Create visualization
        c = Colors if is_color_enabled() else type('obj', (object,), {
            'BOLD': '', 'RED': '', 'GREEN': '', 'YELLOW': '', 'BLUE': '', 
            'MAGENTA': '', 'CYAN': '', 'RESET': '', 'BG_RED': '', 'BG_BLUE': ''
        })
        
        # Header
        print("\n" + "=" * 80)
        print(f"{c.BOLD}{c.RED}EXCEPTION: {exc_info.get('type', 'Unknown')}{c.RESET}")
        print("=" * 80)
        
        # Value
        print(f"{c.BOLD}Message:{c.RESET} {exc_info.get('value', '')}")
        
        # Timestamp
        timestamp = exc_info.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
            print(f"{c.BOLD}Time:{c.RESET} {timestamp}")
        
        # Traceback
        print(f"\n{c.BOLD}{c.BLUE}Traceback:{c.RESET}")
        traceback = exc_info.get('traceback', [])
        for i, frame in enumerate(traceback):
            if isinstance(frame, str):
                print(f"  {frame}")
            else:
                func = frame.get('function', 'unknown')
                file = frame.get('file', 'unknown')
                line = frame.get('line', 0)
                print(f"  {c.CYAN}Frame #{i}:{c.RESET} {func} in {file}:{line}")
        
        # Attributes
        attributes = exc_info.get('attributes', {})
        if attributes:
            print(f"\n{c.BOLD}{c.YELLOW}Attributes:{c.RESET}")
            for key, value in attributes.items():
                print(f"  {c.YELLOW}{key}:{c.RESET} {value}")
        
        # Locals
        locals_vars = exc_info.get('locals', {})
        if locals_vars:
            print(f"\n{c.BOLD}{c.GREEN}Local Variables:{c.RESET}")
            for key, value in locals_vars.items():
                print(f"  {c.GREEN}{key}:{c.RESET} {value}")
        
        # Footer
        print("\n" + "=" * 80)
        print(f"Exception {index if index >= 0 else len(self.exception_history) - 1 + 1} of {len(self.exception_history)}")
        print("=" * 80)

class VSCodeExceptInfoCommand(gdb.Command):
    """Display exception information in VSCode format"""
    
    def __init__(self, handler):
        super(VSCodeExceptInfoCommand, self).__init__("vscode-except-info", gdb.COMMAND_USER)
        self.handler = handler
        
    def invoke(self, arg, from_tty):
        """Handle command invocation"""
        args = arg.split()
        index = -1
        
        # Parse arguments
        if args and args[0].isdigit():
            index = int(args[0])
            
        # Get exception history
        history = self.handler.get_exception_history()
        
        if not history:
            print("No exceptions in history")
            return
            
        # Validate index
        if index >= len(history):
            print(f"Invalid index: {index}, max is {len(history) - 1}")
            index = -1
            
        # Show exception info
        exc_info = history[index] if index >= 0 else history[-1]
        
        # Print basic info
        c = Colors if is_color_enabled() else type('obj', (object,), {'BOLD': '', 'RED': '', 'RESET': ''})
        print(f"\n{c.BOLD}Exception Information:{c.RESET}")
        print(f"  Type: {c.RED}{exc_info.get('type', 'Unknown')}{c.RESET}")
        print(f"  Value: {exc_info.get('value', '')}")
        
        # Print traceback summary
        traceback = exc_info.get('traceback', [])
        if traceback:
            print(f"\n{c.BOLD}Traceback Summary:{c.RESET}")
            for i, frame in enumerate(traceback[:3]):  # Show only first 3 frames
                if isinstance(frame, str):
                    print(f"  {frame}")
                else:
                    func = frame.get('function', 'unknown')
                    file = frame.get('file', 'unknown')
                    line = frame.get('line', 0)
                    print(f"  {func} in {file}:{line}")
            
            if len(traceback) > 3:
                print(f"  ... ({len(traceback) - 3} more frames)")
                
        # Print command hint
        print(f"\nUse {c.BOLD}vscode-except-visualize{c.RESET} for detailed view")

class VSCodeExceptVisualizeCommand(gdb.Command):
    """Visualize exception in VSCode format"""
    
    def __init__(self, handler):
        super(VSCodeExceptVisualizeCommand, self).__init__("vscode-except-visualize", gdb.COMMAND_USER)
        self.handler = handler
        
    def invoke(self, arg, from_tty):
        """Handle command invocation"""
        args = arg.split()
        index = -1
        
        # Parse arguments
        if args and args[0].isdigit():
            index = int(args[0])
            
        # Visualize exception
        self.handler.visualize_exception(index)

# Initialize the VSCode exception handler
try:
    vscode_handler = VSCodeExceptionHandler()
    print("VSCode MicroPython Exception Handler initialized")
except Exception as e:
    print(f"Error initializing VSCode exception handler: {e}") 