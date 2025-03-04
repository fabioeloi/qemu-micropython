# IDE Integration for MicroPython GDB Debugging

This guide explains how to integrate the enhanced exception visualization features with popular IDEs, particularly Visual Studio Code.

## Visual Studio Code Integration

### Prerequisites

- Visual Studio Code (1.60.0 or later)
- [Cortex-Debug](https://marketplace.visualstudio.com/items?itemName=marus25.cortex-debug) extension
- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) extension
- ARM GDB (arm-none-eabi-gdb)

### Setup

1. **Install Required Extensions**

   Open VSCode and install the required extensions:
   - Cortex-Debug
   - Python

2. **Configure Launch Configuration**

   Create or update your `.vscode/launch.json` file with the following configuration:

   ```json
   {
       "version": "0.2.0",
       "configurations": [
           {
               "name": "MicroPython Debug (QEMU)",
               "type": "cortex-debug",
               "request": "launch",
               "servertype": "external",
               "gdbPath": "arm-none-eabi-gdb",
               "gdbTarget": "localhost:1234",
               "cwd": "${workspaceFolder}",
               "executable": "${workspaceFolder}/firmware/build/firmware.elf",
               "runToEntryPoint": "main",
               "preLaunchTask": "start-qemu-gdb",
               "postDebugTask": "stop-qemu",
               "svdFile": "${workspaceFolder}/config/svd/STM32F407.svd",
               "showDevDebugOutput": "raw",
               "gdbStartupCommands": [
                   "source ${workspaceFolder}/scripts/micropython_gdb.py",
                   "source ${workspaceFolder}/.vscode/gdb_micropython.py",
                   "set print pretty on",
                   "set print array on",
                   "set print array-indexes on"
               ],
               "customLaunchSetupCommands": [
                   { "text": "target remote localhost:1234" },
                   { "text": "monitor reset" },
                   { "text": "load" }
               ]
           }
       ]
   }
   ```

3. **Create Tasks Configuration**

   Create or update your `.vscode/tasks.json` file with the following configuration:

   ```json
   {
       "version": "2.0.0",
       "tasks": [
           {
               "label": "start-qemu-gdb",
               "type": "shell",
               "command": "${workspaceFolder}/scripts/debug_micropython.sh --no-gdb",
               "isBackground": true,
               "problemMatcher": {
                   "pattern": {
                       "regexp": ".",
                       "file": 1,
                       "location": 2,
                       "message": 3
                   },
                   "background": {
                       "activeOnStart": true,
                       "beginsPattern": "Starting QEMU with GDB server",
                       "endsPattern": "QEMU is running with GDB server on port"
                   }
               }
           },
           {
               "label": "stop-qemu",
               "type": "shell",
               "command": "pkill -f qemu-system-arm || true",
               "presentation": {
                   "reveal": "never"
               }
           }
       ]
   }
   ```

4. **Create Custom GDB Commands Extension**

   To integrate the enhanced exception visualization with VSCode, create a file named `.vscode/gdb_micropython.py` with the following content:

   ```python
   import gdb
   import os
   import sys
   import json

   # Add the scripts directory to the Python path
   workspace_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   sys.path.append(os.path.join(workspace_folder, "scripts"))

   # Import the MicroPython GDB helper
   try:
       from micropython_gdb import MicroPythonHelper, Colors
   except ImportError:
       print("Error: Could not import MicroPython GDB helper")
       sys.exit(1)

   class VSCodeExceptionHandler:
       def __init__(self):
           self.mpy = MicroPythonHelper()
           self.output_file = os.path.join(workspace_folder, ".vscode", "exception_info.json")
           self.register_commands()
           
       def register_commands(self):
           # Register a breakpoint handler for exceptions
           gdb.events.stop.connect(self.on_stop)
           
       def on_stop(self, event):
           # Check if we stopped due to an exception
           frame = gdb.selected_frame()
           if frame and "mp_raise" in frame.name():
               # Get exception information
               exc_info = self.mpy.get_exception_info()
               if exc_info:
                   # Format for VSCode
                   self.format_for_vscode(exc_info)
                   
       def format_for_vscode(self, exc_info):
           """Format exception information for VSCode"""
           vscode_info = {
               "type": exc_info.get("type", "Unknown"),
               "value": exc_info.get("value", ""),
               "traceback": exc_info.get("traceback", []),
               "attributes": exc_info.get("attributes", {}),
               "locals": exc_info.get("locals", {})
           }
           
           # Write to file for VSCode extension to read
           with open(self.output_file, "w") as f:
               json.dump(vscode_info, f, indent=2)
           
           # Print notification
           print(f"\nException information saved to {self.output_file}")
           print(f"Type: {vscode_info['type']}")
           print(f"Value: {vscode_info['value']}")

   # Initialize the VSCode exception handler
   vscode_handler = VSCodeExceptionHandler()
   print("VSCode MicroPython Exception Handler initialized")
   ```

5. **Update GDB Startup Commands**

   Modify your `launch.json` to include the VSCode integration script:

   ```json
   "gdbStartupCommands": [
       "source ${workspaceFolder}/scripts/micropython_gdb.py",
       "source ${workspaceFolder}/.vscode/gdb_micropython.py",
       "set print pretty on",
       "set print array on",
       "set print array-indexes on"
   ]
   ```

### Using the Integration

1. **Start Debugging**

   Press F5 or click the "Run and Debug" button in VSCode to start debugging.

2. **View Exception Information**

   When an exception occurs:
   
   - GDB will stop at the exception point
   - Exception information will be saved to `.vscode/exception_info.json`
   - The Debug Console will show basic exception information
   - You can use the GDB console to run the enhanced exception visualization commands:
     - `mpy-except-info`
     - `mpy-except-visualize`
     - `mpy-except-navigate`

3. **Custom VSCode Commands**

   You can add custom VSCode commands to your `keybindings.json` to trigger GDB commands:

   ```json
   {
       "key": "ctrl+shift+e",
       "command": "workbench.action.terminal.sendSequence",
       "args": { "text": "mpy-except-visualize\n" },
       "when": "debugSessionActive"
   }
   ```

## PyCharm Integration

PyCharm Professional supports GDB debugging with custom GDB scripts. Here's how to set it up:

1. **Configure GDB**

   - Go to File > Settings > Build, Execution, Deployment > Embedded Development > GDB
   - Add your GDB path (e.g., `/usr/bin/arm-none-eabi-gdb`)
   - In "GDB Startup Commands", add:
     ```
     source /path/to/your/project/scripts/micropython_gdb.py
     ```

2. **Create Run Configuration**

   - Go to Run > Edit Configurations
   - Add a new "Embedded GDB Server" configuration
   - Set 'Target' to your firmware.elf file
   - Set 'GDB Server' to 'External'
   - Set 'GDB Server Port' to 1234
   - In "Before Launch", add a task to run your QEMU script

3. **Start Debugging**

   - Start your QEMU GDB server
   - Run the debug configuration
   - Use the GDB console to run the enhanced exception visualization commands

## Eclipse Integration

Eclipse with the Embedded CDT plugin supports GDB debugging:

1. **Install Embedded CDT**

   - Help > Install New Software
   - Add the Embedded CDT update site
   - Install the Embedded CDT plugins

2. **Configure GDB**

   - Create a new debug configuration
   - Set the GDB command to your arm-none-eabi-gdb
   - In the "Startup" tab, add:
     ```
     source /path/to/your/project/scripts/micropython_gdb.py
     ```

3. **Start Debugging**

   - Start your QEMU GDB server
   - Launch the debug configuration
   - Use the GDB console for enhanced exception visualization

## Customizing the Integration

You can customize the IDE integration by:

1. **Creating Custom Views**

   For VSCode, you can create a custom webview extension that reads the exception information from the JSON file and displays it in a more interactive way.

2. **Adding Syntax Highlighting**

   Add syntax highlighting for the exception visualization output in your IDE's terminal.

3. **Creating Custom Commands**

   Define custom IDE commands that map to the GDB commands for exception visualization.

## Troubleshooting

### VSCode Integration Issues

- **Problem**: GDB fails to connect to QEMU
  - **Solution**: Ensure QEMU is running with GDB server enabled on port 1234

- **Problem**: Exception visualization commands not found
  - **Solution**: Verify that the micropython_gdb.py script is being loaded correctly

- **Problem**: Colors not displaying in VSCode terminal
  - **Solution**: Enable ANSI colors in VSCode settings:
    ```json
    "terminal.integrated.allowChords": true,
    "terminal.integrated.gpuAcceleration": "on",
    "terminal.integrated.defaultProfile.linux": "bash",
    "terminal.integrated.profiles.linux": {
        "bash": {
            "path": "bash",
            "args": ["--login"],
            "env": {
                "TERM": "xterm-256color"
            }
        }
    }
    ```

### PyCharm Integration Issues

- **Problem**: GDB script not loading
  - **Solution**: Use absolute paths in the GDB startup commands

- **Problem**: Colors not displaying
  - **Solution**: Enable ANSI color support in PyCharm terminal settings

## Next Steps

- Create a dedicated VSCode extension for MicroPython debugging
- Add support for interactive exception visualization in the IDE
- Implement exception analysis tools integrated with the IDE 