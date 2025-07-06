# MicroPython Application Development Guide for QEMU STM32

## 1. Introduction

This guide is designed to help you develop, structure, build, and run your MicroPython applications within this project's QEMU-based STM32 virtual environment. Utilizing QEMU allows for rapid prototyping, iterative development, and testing of your application logic without immediate access to physical STM32 hardware.

While QEMU is a powerful tool, it's important to remember it's an emulator with certain limitations regarding precise hardware peripheral behavior. This guide will also touch upon considerations for writing applications that can transition more smoothly between the QEMU environment and physical hardware.

**Prerequisites:**
It's assumed you have successfully set up the project environment as per the main `README.md` and possess a basic understanding of MicroPython programming.

## 2. Project Structure for Your Application

Your MicroPython application code primarily resides in the `src/` directory:

*   **`src/main.py`**: This is the main entry point for your application. When the MicroPython firmware boots in QEMU (or on hardware), it will typically execute `main.py` automatically if it exists in the filesystem or is frozen into the firmware.
*   **`src/lib/`**: This directory is the recommended place for your custom Python libraries or modules that support `main.py`.
    *   You can create subdirectories within `src/lib/` for better organization.
    *   **Example:** If you have a utility module `my_utils.py`, place it in `src/lib/my_utils.py`. You can then import it in `main.py` as `from lib import my_utils` or `import lib.my_utils`.

### Incorporating Your Python Files into the Firmware (Manifest System)

For your Python scripts (`main.py`, library modules) to be available to MicroPython when it runs, they usually need to be "frozen" into the firmware image as bytecode or included in a filesystem image. This project typically uses MicroPython's manifest system to include files during the firmware build process.

*   **Manifest File:** A Python script (e.g., `manifest.py`) tells the MicroPython build system which files or directories to include. This project might use a global manifest (e.g., `config/micropython/manifest.py`) or a board-specific one (e.g., `firmware/micropython/ports/stm32/boards/STM32F4DISC_QEMU/manifest.py`). Refer to the project's build configuration for the exact manifest file in use.
*   **Adding Your Files:** To include your application files, you'll add entries to this manifest file. Paths are often relative to the manifest file's location or predefined variables like `$(MPY_DIR)`.

    **Example `manifest.py` entries:**
    ```python
    # Assuming manifest.py is in a location where these relative paths make sense
    # Or using variables like $(MPY_DIR) for MicroPython root, $(BOARD_DIR), etc.
    # The exact paths depend on your manifest file's location relative to your sources.
    # These are conceptual paths from project_root/config/micropython/manifest.py
    # to project_root/src/

    include("$(MPY_DIR)/../../../../src/main.py")
    freeze("$(MPY_DIR)/../../../../src/lib") # Freezes all .py files in the lib directory
    # Or freeze individual files:
    # freeze("$(MPY_DIR)/../../../../src/lib/my_utils.py")
    ```
    *   Consult MicroPython's documentation on "manifest files" for detailed syntax.
    *   After adding files to the manifest, you must rebuild the firmware.

## 3. Writing Your MicroPython Application

### Core MicroPython Features
Your application can use standard Python 3 syntax (with MicroPython's variations) and MicroPython's rich set of built-in functions and core modules (e.g., `sys`, `time`, `uctypes`, `ujson`, `ure`, `uzlib`).

### Interacting with Emulated "Hardware" (using `machine` module)
The `machine` module in MicroPython provides APIs to control hardware peripherals.

*   **Import:** `import machine`
*   **Common Peripherals:**
    *   **GPIO (`machine.Pin`):** For controlling digital input/output pins.
        ```python
        from machine import Pin
        # Pin names/numbers depend on the board definition and QEMU model.
        # Example: led = Pin('PA5', Pin.OUT) # STM32F4 Discovery User LED LD4 (Green) is PA13 on some common defs
        # This needs to align with what your MicroPython port/board config for QEMU defines
        # and what QEMU actually emulates for the chosen machine.
        # For a conceptual QEMU LED, check your board definition file.
        # led.on()
        # led.off()
        # print(f"LED (conceptual) value: {led.value()}")
        ```
    *   **UART (`machine.UART`):** For serial communication. UART(0) is often the REPL. Other UART instances might be available.
        ```python
        # from machine import UART
        # uart1 = UART(1, 115200) # Check QEMU guide for availability of UART(1)
        # uart1.write("Hello from UART1\n")
        # if uart1.any(): print(uart1.read())
        ```
    *   **I2C (`machine.I2C`), SPI (`machine.SPI`), Timers (`machine.Timer`), ADC (`machine.ADC`):**
        These modules exist in MicroPython, but their functionality in QEMU is **highly dependent** on the level of emulation provided by the chosen QEMU machine model for these specific peripherals on the STM32F4.

*   **CRITICAL NOTE on QEMU Peripheral Emulation:**
    QEMU does **not** fully emulate all STM32F4 peripherals or all their features. Behavior can differ significantly from physical hardware.
    *   **Always consult the `docs/QEMU_GUIDE_STM32F4.md`** for detailed information on which peripherals are known to work, their limitations, and common issues in this project's QEMU setup.
    *   Do not assume a peripheral will work in QEMU just because MicroPython has an API for it.

### Leveraging Host System Resources via Semihosting (`usemihosting` module)
When running in QEMU, your MicroPython application can interact with your host computer's resources (like the filesystem or console) using semihosting. This project provides the `usemihosting` C module, which makes these features accessible from Python.

*   **Purpose:** Useful for debugging, logging, reading configuration/test data from the host, or controlling the QEMU simulation.
*   **Key Uses:**
    *   Reading files from the host: `usemihosting.open('host_file.txt', 'r')`
    *   Writing files to the host: `usemihosting.open('guest_log.txt', 'w').write(...)`
    *   Printing to the host's GDB console (if debugging) or QEMU's log.
    *   Exiting the QEMU simulation: `usemihosting.exit(0)` (0 for success).
*   **Example:**
    ```python
    import usemihosting

    if usemihosting.is_semihosting_available():
        print("Semihosting operations are available via 'usemihosting'.")
        try:
            with usemihosting.open("host_data_input.txt", "r") as f:
                config_data = f.read()
                print(f"Read from host: {config_data}")

            with usemihosting.open("guest_output_log.txt", "a") as f:
                f.write("Application log entry from QEMU guest.\n")
            print("Appended to guest_output_log.txt on host.")

        except OSError as e:
            print(f"Semihosting file operation error: {e}")
    else:
        print("Semihosting not available via 'usemihosting' module.")
    ```
*   **Full API:** Refer to **`docs/SEMIHOSTING.md`** for detailed documentation of the `usemihosting` module.

### (Optional) Using Other Custom C Modules
If this project includes other custom C modules compiled into the MicroPython firmware (beyond `usemihosting`), they would typically be imported and used like any other Python module. Documentation specific to those modules would explain their API.

## 4. Development Workflow Summary

Here's a typical cycle for developing your MicroPython application:

1.  **Write/Edit Code:**
    *   Modify your Python files in `src/main.py`, `src/lib/`, etc.
    *   If working with custom C modules for MicroPython, edit their C source files.
2.  **Update Manifest (if adding new Python files):**
    *   If you've added new `.py` files or directories that need to be part of the firmware, ensure they are correctly listed in the relevant MicroPython manifest file (e.g., `config/micropython/manifest.py` or the board-specific manifest).
3.  **Build Firmware:**
    *   Recompile the MicroPython firmware to include your latest changes.
    *   Refer to **`docs/BUILD_SYSTEM.md`** for the specific firmware build commands used in this project (typically a `make` command in the MicroPython port directory, e.g., `make -C firmware/micropython/ports/stm32 BOARD=STM32F4DISC_QEMU ...`).
4.  **Run in QEMU:**
    *   Execute your application in the QEMU environment:
        ```bash
        ./scripts/run_qemu.sh
        ```
    *   Observe the output on the console (MicroPython REPL).
5.  **Test and Debug:**
    *   Use `print()` statements in your Python code for simple debugging output to the REPL.
    *   Interact with your application via the REPL if appropriate.
    *   For more advanced debugging (breakpoints, variable inspection, step-through), use GDB with the project's helper scripts:
        ```bash
        ./scripts/debug_micropython.sh
        ```
        Refer to **`docs/GDB_DEBUGGING.md`** for detailed GDB usage.

## 5. Tips for QEMU-Targeted Application Development

*   **Design for Portability:** When possible, structure your code to separate hardware-agnostic application logic from direct hardware interactions. This makes it easier to test core logic in QEMU even if some peripherals are not fully emulated.
*   **Graceful Hardware Failure:** Use `try...except OSError:` (or more specific exceptions) when interacting with `machine` peripherals. This allows your application to handle cases where a peripheral might not be available or behave as expected in QEMU, without crashing.
    ```python
    from machine import I2C
    try:
        i2c = I2C(1, scl=Pin('PB6'), sda=Pin('PB7'))
        # ... use i2c ...
    except OSError as e:
        print(f"I2C(1) initialization failed (may not be fully emulated in QEMU): {e}")
    ```
*   **QEMU for Logic, Hardware for Fidelity:** Use QEMU for rapid development and testing of application flow, algorithms, and Python-level logic. Always perform final validation and testing of features that depend on precise timing, analog behavior, or complex peripheral interactions on actual STM32F4 hardware.
*   **Conditional Code (If Needed):** For features that behave very differently or are unavailable in QEMU, you might use conditional logic if a reliable way to detect the QEMU environment exists (e.g., checking `sys.platform` if MicroPython reports a unique platform string for QEMU, or using a flag set via semihosting). However, aim for code that requires minimal QEMU-specific paths.

## 6. Simple Application Example

This example demonstrates a `main.py` using a custom library and the `usemihosting` module.

**File: `src/lib/app_utils.py`**
```python
# src/lib/app_utils.py
def generate_data_string(counter):
    # Simulates generating some data
    return f"Data packet {counter}: value={counter*10}"

def process_data(data_str):
    print(f"Processing in app_utils: {data_str}")
    return data_str.upper()
```

**File: `src/main.py`**
```python
# src/main.py
import time
import usemihosting
from lib import app_utils # Assuming src/lib/app_utils.py exists

print("--- MicroPython Application Started in QEMU ---")

for i in range(3):
    raw_data = app_utils.generate_data_string(i)
    processed_data = app_utils.process_data(raw_data)
    print(f"Main loop: Processed data = {processed_data}")

    # Conceptual LED blink - actual pin depends on QEMU & board config
    # from machine import Pin
    # led = Pin("PA13", Pin.OUT) # Example, if PA13 is an emulated LED
    # led.on()
    # time.sleep_ms(100)
    # led.off()

    time.sleep_ms(500)

if usemihosting.is_semihosting_available():
    print("Attempting to write completion log to host via semihosting...")
    try:
        with usemihosting.open("qemu_app_completion.log", "w") as f:
            f.write(f"Application completed {time.ticks_ms()}ms ticks.\n")
        print("Log written to qemu_app_completion.log on host.")
    except Exception as e:
        print(f"Semihosting error writing log: {e}")
else:
    print("Semihosting not available, skipping host log.")

print("--- MicroPython Application Finished ---")

# To make QEMU exit automatically after the script (useful for automated tests)
# if usemihosting.is_semihosting_available():
#    usemihosting.exit(0)
```

**To include these in firmware, your manifest (e.g., `config/micropython/manifest.py`) would need:**
```python
# Example manifest entries
include("$(MPY_DIR)/../../../../src/main.py")
freeze("$(MPY_DIR)/../../../../src/lib/") # Or freeze("$(MPY_DIR)/../../../../src/lib/app_utils.py")
```

This guide provides a starting point for developing your MicroPython applications in this QEMU-based STM32 environment. Always refer to the specific documentation for QEMU, MicroPython, and this project's helper modules for more detailed information.
