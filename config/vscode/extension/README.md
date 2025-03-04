# MicroPython Debugger Extension

This VSCode extension enhances the debugging experience for MicroPython applications by providing advanced exception visualization and navigation capabilities.

## Features

### Exception Visualization

- **Rich Exception Display**: View exceptions with syntax highlighting and formatted traceback
- **Exception History**: Browse through previous exceptions
- **Interactive Navigation**: Navigate through exception frames and jump to source code
- **Variable Inspection**: Examine local variables at the exception point

### Dedicated Views

- **Exceptions View**: Shows current exception and exception history
- **Variables View**: Shows local variables at the exception point

### Commands

- **Visualize Exception**: Display the current exception in a rich webview
- **Show Exception History**: Browse through previous exceptions
- **Navigate Exception Frames**: Jump to source code locations in the exception traceback

## Requirements

- Visual Studio Code 1.60.0 or later
- [Cortex-Debug](https://marketplace.visualstudio.com/items?itemName=marus25.cortex-debug) extension
- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) extension
- ARM GDB (arm-none-eabi-gdb)
- QEMU-MicroPython project with GDB integration

## Installation

1. Copy the extension files to your `.vscode/extensions/micropython-debugger` directory:
   ```bash
   mkdir -p ~/.vscode/extensions/micropython-debugger
   cp -r config/vscode/extension/* ~/.vscode/extensions/micropython-debugger/
   ```

2. Restart VSCode to load the extension

## Usage

### Starting a Debug Session

1. Open your MicroPython project in VSCode
2. Start a debug session using the "MicroPython Debug (QEMU)" configuration
3. When an exception occurs, the extension will automatically visualize it

### Using the Exception Views

- **Exceptions View**: Shows the current exception and exception history
  - Click on an exception to view its details
  - Click on a frame to navigate to the source code

- **Variables View**: Shows local variables at the exception point
  - Click on a variable to view its details

### Using the Commands

- **Visualize Exception**: `Ctrl+Shift+E` - Display the current exception in a rich webview
- **Show Exception History**: `Ctrl+Shift+H` - Browse through previous exceptions
- **Navigate Exception Frames**: `Ctrl+Shift+N` - Jump to source code locations in the exception traceback

## Configuration

The extension provides the following configuration options:

- **micropythonDebugger.exceptionHistorySize**: Maximum number of exceptions to keep in history (default: 10)
- **micropythonDebugger.autoVisualizeExceptions**: Automatically visualize exceptions when they occur (default: true)
- **micropythonDebugger.colorOutput**: Use colors in exception visualization (default: true)

## How It Works

The extension works by monitoring the `.vscode/exception_info.json` and `.vscode/exception_history.json` files, which are created by the GDB integration script. When an exception occurs, the GDB script writes the exception information to these files, and the extension reads and visualizes the data.

## Troubleshooting

### Common Issues

- **No exception information available**: Make sure the GDB integration script is properly loaded and the debug session is active
- **Exception visualization not working**: Check that the `.vscode/exception_info.json` file is being created when an exception occurs
- **Source code navigation not working**: Ensure that the file paths in the exception traceback are correct and the files exist in the workspace

### Logs

The extension logs information to the VSCode output panel. To view the logs:

1. Open the Output panel (`Ctrl+Shift+U`)
2. Select "MicroPython Debugger" from the dropdown menu

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This extension is licensed under the MIT License.

## Acknowledgments

- MicroPython project: https://micropython.org/
- QEMU project: https://www.qemu.org/
- VSCode Cortex-Debug extension: https://github.com/Marus/cortex-debug 