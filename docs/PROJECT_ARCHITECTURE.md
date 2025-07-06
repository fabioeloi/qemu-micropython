# Project Architecture Overview

## 1. Introduction

The `qemu-micropython` project aims to provide a comprehensive virtual development and testing environment for MicroPython applications targeted at STM32 microcontrollers. By leveraging QEMU for hardware emulation, developers can write, test, and debug MicroPython code without requiring physical STM32 hardware, facilitating rapid iteration and automated testing.

This document provides a high-level overview of the project's architecture, detailing its major components and how they interact to create this virtualized environment.

## 2. High-Level Architectural Diagram (Conceptual)

The project can be visualized as interactions across three main zones: the Host System (developer's machine or CI runner), the QEMU Emulated Environment, and the MicroPython Guest running within QEMU.

*   **Host System:**
    *   **Developer:** Interacts with source code, build tools, and debuggers.
    *   **Build Tools:** `make`, `gcc` (for host C tests), `arm-none-eabi-gcc` (for firmware and target C tests), Python 3 (for scripts and Python unit tests), Ruby & CMock (for C mocking).
    *   **GDB Client (`arm-none-eabi-gdb`):** Connects to QEMU for debugging.
    *   **Automation Scripts:** Python scripts like `run_qemu_c_tests.py` manage QEMU execution for tests. Shell scripts (`run_qemu.sh`, `build.sh`, etc.) simplify common tasks.
    *   **CI Runner (e.g., GitHub Actions):** Automates the setup, build, and test execution.

*   **QEMU Process Boundary (Host <-> Emulator Interface):**
    *   QEMU provides interfaces like TCP for GDB, stdio redirection for serial, and semihosting syscalls.

*   **QEMU Emulated Environment:**
    *   **`qemu-system-arm` Process:** The emulator itself.
    *   **Machine Model:** (e.g., `olimex-stm32-h405`) Defines the virtual STM32F4-like hardware.
    *   **Emulated CPU:** ARM Cortex-M4.
    *   **Emulated Memory:** RAM and Flash regions.
    *   **GDB Stub:** Built into QEMU, allows GDB client to connect and control the guest.
    *   **Semihosting Interface:** Allows guest code to perform I/O via the host system.
    *   **Emulated Serial Port:** Typically connected to the host's `stdio`, providing a console for the MicroPython REPL.

*   **MicroPython Guest (running inside QEMU):**
    *   **MicroPython Firmware (`firmware.bin`):**
        *   **Core Interpreter & Runtime:** The MicroPython engine.
        *   **STM32 Port:** Hardware Abstraction Layer (HAL) and drivers for STM32 peripherals (adapted for QEMU's emulated capabilities). Includes a specific board configuration (e.g., `STM32F4DISC_QEMU`).
        *   **Custom C Modules:** Extensions like `usemihosting` for Python-level access to semihosting.
    *   **User Application:** `main.py` and associated MicroPython libraries developed by the user.

**Key Interactions:**
*   The GDB client communicates with QEMU's GDB stub over TCP to debug the MicroPython firmware.
*   The MicroPython firmware uses QEMU's semihosting interface for operations like file access on the host or signaling program termination (especially in test runners).
*   The emulated serial port provides REPL access and standard output from MicroPython.
*   Build tools on the host compile source code into firmware or test binaries that are then loaded into QEMU.

## 3. Core Components Deep Dive

### 3.1. QEMU Environment

*   **Role:** Provides the virtual hardware platform for executing and testing the MicroPython firmware.
*   **Executable:** `qemu-system-arm`.
*   **Machine Model:** Typically `-machine olimex-stm32-h405`. This choice is based on its use of an STM32F405 series Cortex-M4 CPU. For further details on machine model considerations, see the [QEMU STM32F4 Machine Exploration Report](qemu_stm32f4_machine_exploration.md).
*   **CPU Emulation:** Faithfully emulates an ARM Cortex-M4 processor.
*   **Emulated Services:**
    *   **GDB Stub:** Enabled via the `-gdb tcp::1234` QEMU option, allowing remote debugging.
    *   **Semihosting:** Enabled via `-semihosting-config enable=on,target=native` and `-semihosting`. This is critical for test automation (e.g., `qemu_exit()`) and can be used for host file I/O from the guest.
    *   **Serial Port:** The `-serial stdio` option redirects the first emulated UART to the host's standard input/output, providing the MicroPython REPL.
*   **Configuration:** Key QEMU settings are managed in `config/qemu/stm3f4.cfg` and applied by launch scripts like `scripts/run_qemu.sh`. General notes on QEMU's STM32 behavior are in [QEMU STM32 General Notes](../QEMU-STM32-NOTES.md).

### 3.2. MicroPython Firmware

*   **Structure:** Comprises the core MicroPython interpreter, the STM32 hardware port (which includes HAL drivers and board-specific configurations like pin definitions), and any custom C modules developed for the project (e.g., `usemihosting`).
*   **Board Configuration:** A specific MicroPython board configuration (e.g., `STM32F4DISC_QEMU` or similar, found within the MicroPython build system) tailors the firmware to the known capabilities and limitations of the QEMU emulated environment.
*   **User Application:** This is the Python code (`main.py`, other `.py` modules) that runs on the MicroPython interpreter.
*   **Execution:** The compiled `firmware.bin` is loaded by QEMU using the `-kernel` option and runs as the guest operating system/application.

### 3.3. Debugging Infrastructure

*   **GDB (`arm-none-eabi-gdb`):** The primary tool for low-level debugging of the C code (firmware) and, with helpers, Python code.
*   **`scripts/micropython_gdb.py`:** A collection of Python scripts loaded into GDB. These scripts extend GDB with commands (`mpy-*`) to understand MicroPython's internal structures, providing features like Python-level backtraces, local variable inspection, and enhanced exception analysis.
*   **`config/gdb/gdbinit`:** This GDB script is automatically loaded when GDB starts. It sets up useful GDB defaults, loads `micropython_gdb.py`, and may define initial breakpoints.
*   **Interaction Flow:** GDB (Client) -> TCP Connection -> QEMU GDB Stub (Server embedded in QEMU) -> Control/Inspect MicroPython Guest.
*   Refer to the [GDB Debugging Guide](GDB_DEBUGGING.md) for comprehensive details.

### 3.4. Build System(s)

The project employs a `make`-based build system with different components:

*   **Main MicroPython Firmware:** Built using the MicroPython port's Makefiles (typically found in `firmware/micropython/ports/stm32/`). This process is usually orchestrated by a top-level project script like `scripts/build.sh`, which configures the correct board and builds the `firmware.bin`.
*   **Host C Unit Tests:** Built using `test/host/Makefile`. This uses the host's `gcc` compiler to compile C test files, the Unity framework, CMock-generated mocks, and the C modules under test into native host executables.
*   **Target C Unit Tests (for QEMU):** Built using `test/target/Makefile`. This uses the `arm-none-eabi-gcc` cross-compiler to produce small, self-contained `.bin` firmware images. Each image includes Unity, a specific test suite, the C module(s) under test, and minimal STM32 startup code.
*   **Root `Makefile`:** Provides top-level convenience targets (e.g., `make test_python`, `make test_c_host`, `make build_c_target_tests`) that delegate to the more specific Makefiles or scripts.

### 3.5. Testing Infrastructure

A multi-layered testing approach is used to ensure code quality:

*   **C Unit Testing (Host):**
    *   Framework: Unity (for assertions and test structure) and CMock (for generating mock dependencies).
    *   Location: `test/host/`
    *   Execution: Runs directly on the host machine.
    *   Details: [Host-Based C Unit Testing Guide](UNIT_TESTING_C_HOST.md).
*   **C Unit Testing (Target/QEMU):**
    *   Framework: Unity.
    *   Location: Test sources often reused from `test/host/`, compiled by `test/target/Makefile`.
    *   Execution: Runs as firmware inside QEMU, managed by `scripts/run_qemu_c_tests.py`.
    *   Details: [On-Target C Unit Testing in QEMU Guide](UNIT_TESTING_C_QEMU.md).
*   **Python Unit Testing:**
    *   Framework: Python's built-in `unittest` module.
    *   Location: `test/python/`.
    *   Execution: Runs on the host machine using the host Python interpreter.
    *   Details: [Python Unit Testing Guide](UNIT_TESTING_PYTHON.md).
*   **QEMU Test Automation Script (`scripts/run_qemu_c_tests.py`):**
    *   Manages the execution of target C unit test binaries in QEMU, captures their parseable output, and reports pass/fail status.

### 3.6. Continuous Integration (CI/CD)

*   **Platform:** GitHub Actions.
*   **Workflow:** Defined in `.github/workflows/ci.yml`.
*   **Process:** Automatically on pushes/pull_requests, the CI workflow:
    1.  Sets up the environment (ARM toolchain, QEMU, Python, Ruby/CMock, Make).
    2.  Builds the main MicroPython firmware.
    3.  Builds all host C unit tests.
    4.  Builds all target C unit test binaries.
    5.  Executes host C unit tests.
    6.  Executes target C unit tests (using `run_qemu_c_tests.py`).
    7.  Executes Python unit tests.
*   **Goal:** Ensure code changes maintain build integrity and pass all automated tests.
*   Details: [Continuous Integration (CI) Guide](CONTINUOUS_INTEGRATION.md).

## 4. Key Operational Workflows

This architecture supports several key developer workflows:

*   **Application Development:**
    1.  Edit Python code in `src/main.py` or associated libraries.
    2.  If custom C modules are involved, edit C code in `src/` or the MicroPython firmware source.
    3.  Build firmware: `./scripts/build.sh` (or equivalent `make` target).
    4.  Run in QEMU: `./scripts/run_qemu.sh` for interactive REPL and application execution.
*   **Debugging:**
    1.  Start a debug session: `./scripts/debug_micropython.sh`.
    2.  Connect GDB and use standard GDB commands along with custom `mpy-*` helpers for MicroPython-specific inspection.
*   **Host C Unit Testing:**
    1.  Write/edit C module and its test in `test/host/test_*.c`.
    2.  Update `test/host/Makefile` if adding a new suite or changing dependencies/mocks.
    3.  Run: `make -C test/host run_tests`.
*   **Target C Unit Testing:**
    1.  Write/adapt C module and tests (often reusing from host tests).
    2.  Update `test/target/Makefile` if adding a new suite.
    3.  Build target test: `make -C test/target test_mysuite_qemu.bin`.
    4.  Run automated test: `python3 scripts/run_qemu_c_tests.py test/target/test_mysuite_qemu.bin`.
*   **Python Unit Testing:**
    1.  Write/edit Python script and its test in `test/python/`.
    2.  Run: `make test_python`.
*   **CI Validation:** Pushing code or creating a Pull Request automatically triggers the full suite of builds and tests via GitHub Actions.

## 5. Directory Structure Overview

A brief overview of key top-level directories:

*   `.github/`: GitHub-specific files, including Actions workflows.
*   `config/`: Configurations for QEMU, GDB, and MicroPython builds.
*   `docs/`: Project documentation (guides, reports, notes).
*   `firmware/`: Contains the MicroPython source (e.g., as a submodule) and build outputs (`firmware.bin`).
*   `scripts/`: Utility and automation scripts for building, running, debugging, and testing.
*   `src/`: Source code for the main MicroPython application and any custom C modules for the project.
*   `test/`: Contains all testing-related files:
    *   `test/frameworks/`: Testing frameworks like Unity, CMock.
    *   `test/host/`: Host-based C unit tests and their Makefile.
    *   `test/target/`: Target-based C unit tests (for QEMU) and their Makefile, startup code, linker script.
    *   `test/python/`: Python unit tests.
*   `tools/`: May contain auxiliary development tools, including potentially a local build of QEMU.

For a more detailed list, refer to the "Directory Structure" section in the main [../README.md](../README.md).

## 6. Pointers to Detailed Documentation

This architecture document provides a high-level view. For specific details, please refer to:

*   Main Project README: [../README.md](../README.md)
*   GDB Debugging: [docs/GDB_DEBUGGING.md](GDB_DEBUGGING.md)
*   Semihosting: [docs/SEMIHOSTING.md](SEMIHOSTING.md)
*   Host C Unit Testing: [docs/UNIT_TESTING_C_HOST.md](UNIT_TESTING_C_HOST.md)
*   Target C Unit Testing (QEMU): [docs/UNIT_TESTING_C_QEMU.md](UNIT_TESTING_C_QEMU.md)
*   Python Unit Testing: [docs/UNIT_TESTING_PYTHON.md](UNIT_TESTING_PYTHON.md)
*   Continuous Integration: [docs/CONTINUOUS_INTEGRATION.md](CONTINUOUS_INTEGRATION.md)
*   QEMU Machine Exploration: [docs/qemu_stm32f4_machine_exploration.md](qemu_stm32f4_machine_exploration.md)
*   QEMU STM32 Notes: [../QEMU-STM32-NOTES.md](../QEMU-STM32-NOTES.md)

(Adjust paths as needed if this file is moved or if linked files are at different relative locations.)
