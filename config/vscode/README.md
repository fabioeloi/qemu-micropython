# VSCode Integration for MicroPython Debugging

This directory contains configuration files for Visual Studio Code integration with MicroPython debugging in QEMU.

## Files

- `launch.json`: Debug launch configurations
- `tasks.json`: Task definitions for debugging
- `keybindings.json`: Custom keyboard shortcuts for debugging commands
- `gdb_micropython.py`: GDB Python script for VSCode integration

## Setup

1. Install the required extensions:
   - [Cortex-Debug](https://marketplace.visualstudio.com/items?itemName=marus25.cortex-debug)
   - [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

2. Copy the configuration files to your `.vscode` directory:
   ```bash
   mkdir -p .vscode
   cp config/vscode/launch.json config/vscode/tasks.json .vscode/
   ```

3. Run the `create-svd-directory` task to download the STM32F407 SVD file for peripheral debugging.

4. Copy the keybindings from `keybindings.json` to your VSCode keybindings file:
   - Press `Ctrl+Shift+P` and type "Open Keyboard Shortcuts (JSON)"
   - Add the keybindings from this file

## Usage

### Debug Configurations

- **MicroPython Debug (QEMU)**: Standard debugging configuration
- **MicroPython Exception Test**: Configuration with exception catching enabled

### Tasks

- **start-qemu-gdb**: Starts QEMU with GDB server
- **stop-qemu**: Stops QEMU
- **run-exception-test**: Runs the exception visualization test script
- **create-svd-directory**: Downloads the SVD file for peripheral debugging
- **setup-vscode-config**: Copies the VSCode configuration files to the `.vscode` directory

### Keyboard Shortcuts

- `Ctrl+Shift+E`: Visualize current exception
- `Ctrl+Shift+I`: Show exception information
- `Ctrl+Shift+H`: Show exception history
- `Ctrl+Shift+N`: Navigate exception frames

## Exception Visualization

The VSCode integration enhances exception visualization with:

1. **Automatic Exception Detection**: Automatically detects and captures exceptions
2. **JSON Export**: Exports exception information to `.vscode/exception_info.json`
3. **History Tracking**: Maintains exception history in `.vscode/exception_history.json`
4. **Custom Commands**:
   - `vscode-except-info`: Shows basic exception information
   - `vscode-except-visualize`: Shows detailed exception visualization

## Customization

You can customize the integration by:

1. Modifying `gdb_micropython.py` to change the visualization format
2. Adding custom commands to `keybindings.json`
3. Updating `launch.json` to add more debug configurations

## Troubleshooting

- If colors don't display correctly, ensure your terminal supports ANSI colors
- If GDB fails to connect, ensure QEMU is running with the GDB server enabled
- If the SVD file is missing, run the `create-svd-directory` task

For more information, see the main documentation in `docs/IDE_INTEGRATION.md`. 