# QEMU for STM32F4 Development and Testing: A Guide

## 1. Introduction

This guide provides an overview of using QEMU (Quick Emulator) for developing and testing MicroPython applications on an emulated STM32F4 microcontroller within this project. QEMU allows for rapid iteration, debugging, and automated testing without requiring physical hardware for many development tasks.

This document covers the current QEMU setup, considerations for machine model selection, key QEMU features utilized, known emulation limitations, and best practices.

## 2. Current Default QEMU Configuration

The project primarily uses the following QEMU setup, typically launched via scripts like `scripts/run_qemu.sh` or `scripts/debug_micropython.sh`:

*   **QEMU Command:** `qemu-system-arm`
*   **Machine Model:** `-machine olimex-stm32-h405`
    *   This model is based on the Olimex STM32-H405 board, which features an STM32F405RGT6 (Cortex-M4F) microcontroller. It's chosen for its general Cortex-M4 compatibility.
*   **CPU:** `-cpu cortex-m4`
*   **Memory:** `-m 128K` (This QEMU option typically specifies RAM size for the model).
*   **Firmware Loading:** `-kernel firmware.bin` (The main MicroPython firmware).
*   **Serial Console:** `-serial stdio` (Redirects the primary emulated UART to the host's standard input/output, used for the MicroPython REPL).
*   **GDB Debugging:** `-gdb tcp::1234 -S` (Starts QEMU with a GDB server paused, waiting for a GDB client to connect).
*   **Semihosting:** `-semihosting-config enable=on,target=native,chardev=stdio -semihosting` (Enables semihosting for host I/O operations from the guest and allows test runners to signal QEMU to exit).
*   **QEMU Internal Debugging:** `-d guest_errors,unimp` (Logs guest CPU errors and access to unimplemented hardware features).

The full set of options can be found in the project's launch scripts and `config/qemu/stm32f4.cfg`.

## 3. Understanding QEMU Machine Choices

The choice of QEMU machine model impacts the available peripherals and their behavior.

*   **Current Default (`olimex-stm32-h405`):** As described above.
*   **Alternative (`netduinoplus2`):**
    *   Also based on the STM32F405RGT6 SoC.
    *   It's a common alternative and can be tested by changing the `-machine` flag (e.g., `scripts/run_qemu.sh -m netduinoplus2`).
    *   It is unlikely to offer dramatically different peripheral emulation from `olimex-stm32-h405` due to shared underlying QEMU peripheral models for STM32 but may have subtle differences in default peripheral mappings or stability.
*   **Other STM32F4 Models (e.g., `stm32f4-discovery`, `stm32f429i-disco`):**
    *   Models for specific ST Discovery boards would be ideal if they offer better peripheral fidelity and are available in the QEMU version being used.
    *   Availability and quality of these models vary significantly between QEMU versions and forks. You can check available machines in your QEMU build by running `qemu-system-arm -M help`.
    *   Using a machine for a different SoC (like STM32F429 for `stm32f429i-disco`) may require significant firmware adaptations (memory map, clocks).
*   Refer to the [QEMU STM32F4 Machine Exploration Report](qemu_stm32f4_machine_exploration.md) for a more detailed historical analysis (though its key recommendations are incorporated here).

## 4. Core QEMU Features Utilized

This project leverages several key QEMU features:

*   **Serial Port for REPL:** The `-serial stdio` option is fundamental for interacting with the MicroPython REPL and seeing standard output from MicroPython scripts.
*   **Semihosting:** This allows the MicroPython firmware (both C code and Python scripts via the `usemihosting` module) to perform I/O operations using the host system's resources. This is used for:
    *   Console output/input beyond the primary serial REPL if needed.
    *   File access on the host (e.g., for tests or configuration).
    *   Allowing on-target C unit test runners to signal QEMU to exit with a status code.
    *   See the [Semihosting with `usemihosting` Guide](SEMIHOSTING.md) for details on its use from MicroPython.
*   **GDB Stub:** QEMU's built-in GDB stub (enabled with `-gdb ...`) allows `arm-none-eabi-gdb` to connect, control, and debug the execution of the MicroPython firmware running inside QEMU. This is essential for both C-level firmware debugging and Python-level debugging facilitated by the project's GDB helper scripts. See the [GDB Debugging Guide](GDB_DEBUGGING.md).

## 5. Running Code in QEMU

*   **Main MicroPython Firmware:** Typically run using `./scripts/run_qemu.sh`. This script handles finding the firmware binary and launching QEMU with the standard configuration.
*   **Target C Unit Tests:** Individual C unit test suites compiled as standalone firmware binaries are run using the `python3 scripts/run_qemu_c_tests.py <path_to_test.bin>` script. See [On-Target C Unit Testing Guide](UNIT_TESTING_C_QEMU.md).

## 6. Known Limitations of QEMU's STM32F4 Emulation

It's crucial to be aware that QEMU's emulation of STM32F4 peripherals is not complete and has known limitations:

*   **Incomplete Peripheral Models:**
    *   **RCC (Reset and Clock Control):** Emulation is often simplified. Detailed clock configurations or controls for specific peripheral clocks might not behave as on physical hardware. You may see messages like `stm32_rcc_write: The RCC peripheral only supports enable and reset in QEMU`.
    *   **Flash Memory Interface:** Internal Flash controller operations (programming, erasing, option bytes) are typically not fully emulated. Firmware is loaded directly via QEMU's `-kernel` option.
    *   **GPIOs:** Basic I/O might work for some ports/pins. Advanced features (alternate functions, speeds, detailed interrupt configs) or all GPIOs may not be available or accurately emulated.
    *   **Timers:** Emulation of general-purpose, advanced, and basic timers is often very limited, possibly only supporting a basic system tick. Complex PWM, capture/compare, or inter-timer synchronization are usually not supported.
    *   **ADC/DAC & Other Complex Peripherals:** Analog features and specialized peripherals (CAN, I2S, SDIO, FSMC, etc.) generally have minimal or no emulation.
*   **UART Emulation:** Beyond the primary serial console (usually one UART), other UART instances or advanced features (hardware flow control, specific interrupt behaviors) might be limited or behave differently from hardware.
*   **MicroPython Board Configuration for QEMU:** The project may use a specific MicroPython board configuration (e.g., `STM32F4DISC_QEMU` or similar) that disables or stubs out features not well-supported by QEMU to allow the firmware to run.

## 7. Best Practices for QEMU-Based Development

To work effectively with QEMU's limitations:

*   **Start Simple:** When troubleshooting, use minimal C or MicroPython programs to verify basic QEMU operations before running complex applications.
*   **Prefer Semihosting for I/O:** For debug output or simple host file interaction from C code or test runners, semihosting is often more reliable than emulated UARTs or file systems within the guest.
*   **Focus QEMU Testing:** Use QEMU for testing core MicroPython scripts, algorithms, C module logic, and features that don't depend on precise or complex hardware interactions.
*   **Test on Hardware:** Always perform final validation and comprehensive testing of hardware drivers, timing-sensitive code, analog features, and intricate peripheral interactions on actual STM32F4 hardware.
*   **MicroPython Script Design:** When writing MicroPython scripts intended to run in QEMU:
    *   Abstract hardware interactions where possible.
    *   Be mindful that peripherals might not behave identically to physical hardware.
    *   Consider using the `usemihosting` module for host interactions where appropriate.

## 8. Basic QEMU Troubleshooting

*   **QEMU Fails to Start:** Check paths to QEMU executable and firmware binary. Ensure the machine model is supported by your QEMU version.
*   **No REPL/Output:** Verify `-serial stdio` is used. Check if MicroPython firmware booted correctly (QEMU debug logs might show errors).
*   **"Unimplemented device" messages:** These are common (see Limitations section). They indicate your code tried to access a part of a peripheral that QEMU doesn't model. This may or may not be critical depending on what your code was doing.
*   **GDB Connection Issues:** Ensure QEMU was started with `-gdb tcp::1234` (and `-S` if you want it to wait). Check for port conflicts.

By understanding QEMU's capabilities and limitations for STM32F4 emulation, it can be a powerful accelerator for MicroPython development and testing.
