# Build System Guide

## 1. Introduction

This guide provides an overview of the build system used in the `qemu-micropython` project. Understanding the build system is essential for compiling the main MicroPython firmware, as well as building and running the various unit test suites.

The build system is primarily based on `make`, with different Makefiles responsible for specific components of the project. A root `Makefile` provides convenience targets for common operations.

## 2. Prerequisites

Before you can build any part of this project, ensure you have the following tools installed and accessible in your system's PATH:

*   **`make`**: The GNU Make utility for orchestrating builds.
*   **`gcc`**: A C compiler for your host system (e.g., Linux, macOS). Used for compiling host-based C unit tests.
*   **ARM GCC Toolchain**: Specifically `arm-none-eabi-gcc` and its related utilities (`arm-none-eabi-ld`, `arm-none-eabi-objcopy`, etc.). This is required for compiling the MicroPython firmware and on-target C unit tests.
*   **Python 3**: Required for running Python unit tests and various automation scripts (e.g., `scripts/run_qemu_c_tests.py`). Version 3.7+ is recommended.
*   **Ruby**: Required for CMock, the C mocking framework. Version 2.7+ is generally suitable.
*   **CMock Gem**: After installing Ruby, install CMock: `gem install cmock`.

The `scripts/setup_env.sh` script (if used) may assist in setting up some of these dependencies, particularly QEMU and potentially the ARM toolchain on certain systems.

## 3. Overall Build Structure

The project's build tasks are managed by a hierarchy of Makefiles:

*   **Root `Makefile`**: Located at the project root. It provides high-level targets that often delegate to other, more specific Makefiles or scripts. This is the recommended entry point for most common build and test operations.
*   **MicroPython Firmware Build System**: Located within the MicroPython source directory (e.g., `firmware/micropython/`). This is MicroPython's standard build system, used to compile the core MicroPython interpreter and STM32 port.
*   **Host C Unit Test Makefile (`test/host/Makefile`):** Manages the compilation and execution of C unit tests that run directly on your host machine.
*   **Target C Unit Test Makefile (`test/target/Makefile`):** Manages the compilation of C unit tests into firmware binaries that can be run on the QEMU emulated STM32 target.

## 4. Building the Main MicroPython Firmware

The main MicroPython firmware, which includes the interpreter, STM32 port, and any project-specific custom C modules, is built using MicroPython's own build system.

*   **Location of MicroPython Source:** Assumed to be in `firmware/micropython/` (this might be a git submodule).
*   **Build Command:**
    The typical command to build the firmware for the QEMU target involves navigating to the STM32 port directory and invoking `make`. The `BOARD` variable is critical for selecting the correct configuration.
    ```bash
    # From the project root directory:
    make -C firmware/micropython/ports/stm32 BOARD=STM32F4DISC_QEMU CROSS_COMPILE=arm-none-eabi- clean
    make -C firmware/micropython/ports/stm32 BOARD=STM32F4DISC_QEMU CROSS_COMPILE=arm-none-eabi- -j$(nproc)
    ```
    *   Replace `STM32F4DISC_QEMU` with the actual board name used for QEMU in this project if it's different.
    *   `CROSS_COMPILE=arm-none-eabi-` specifies the toolchain prefix.
    *   `-j$(nproc)` enables parallel compilation.
    *   A project-specific script like `scripts/build_firmware.sh` (if it exists and performs the full build) might wrap these commands. *Note: The current `scripts/build.sh` appears to be for QEMU run preparation rather than a full firmware build from scratch.*
*   **Board Configuration:** The `BOARD=` argument selects board-specific configuration files (like `mpconfigboard.h`, `stm32f4xx_hal_conf.h`) located in `firmware/micropython/ports/stm32/boards/<BOARD_NAME>/`. These files tailor the firmware build for the specific hardware target or, in this case, the QEMU emulated environment.
*   **Output:**
    *   The primary outputs are usually found in a directory like `firmware/micropython/ports/stm32/build-STM32F4DISC_QEMU/`.
    *   Key files: `firmware.elf` (for debugging) and `firmware.bin` (for flashing or QEMU's `-kernel` option).
    *   The `scripts/run_qemu.sh` script typically expects `firmware.bin` (or handles split `firmware0.bin`/`firmware1.bin` files) in the project's `firmware/build/` directory, so a copy step might be part of the project's full build process.

## 5. Building and Running Host C Unit Tests

Host C unit tests are designed to test C modules in isolation on your development machine using `gcc`.

*   **Makefile:** `test/host/Makefile`
*   **Frameworks Used:** Unity (for test structure and assertions) and CMock (for generating mocks of dependencies).
*   **Key `make` Targets (run from `test/host/` directory, or via root `Makefile`):**
    *   `make all` (or `make`): Builds all host test suite executables (e.g., `test_string_utils.out`).
    *   `make run_tests`: Builds (if necessary) and executes all test suites, printing a summary and exiting with an error code if any test fails. **This is the recommended target for running host C tests.**
    *   `make generate_mocks`: Explicitly generates all mocks defined in `HEADERS_TO_MOCK`. This is usually an automatic prerequisite for building test executables.
    *   `make clean`: Removes compiled test executables, object files, and the `build/mocks/` directory.
*   **Adding a New Test Suite (e.g., for `my_module`):**
    1.  Refer to `docs/UNIT_TESTING_C_HOST.md` for details on writing tests.
    2.  In `test/host/Makefile`:
        *   Add `my_module` to the `TEST_SUITES` list.
        *   Define `SRC_my_module = ../../src/path/to/my_module.c [other_project_sources_needed ...]`
        *   If `my_module`'s tests require mocks for `path/to/dependency.h`:
            *   Add `src/path/to/dependency.h` to the `HEADERS_TO_MOCK` list.
            *   Define `MOCKS_FOR_my_module = $(MOCKS_OUTPUT_DIR)/mock_dependency.c`.

## 6. Building Target C Unit Tests (for QEMU)

Target C unit tests are compiled for the ARM architecture and run as standalone firmware inside QEMU.

*   **Makefile:** `test/target/Makefile`
*   **Framework Used:** Unity.
*   **Compiler:** `arm-none-eabi-gcc`.
*   **Key Components:** Uses custom startup code (`startup_qemu_tests.c`) and a linker script (`stm32f4_qemu.ld`) tailored for a minimal QEMU environment.
*   **Key `make` Targets (run from `test/target/` directory, or via root `Makefile`):**
    *   `make all` (or `make`): Builds all defined target test suite binaries (e.g., `test_string_utils_qemu.bin`).
    *   `make clean`: Cleans build artifacts.
*   **Adding a New Test Suite (e.g., for `my_module`):**
    1.  Refer to `docs/UNIT_TESTING_C_QEMU.md` for details on adapting test runners for QEMU.
    2.  In `test/target/Makefile`:
        *   Add `my_module` to the `TEST_SUITES` list.
        *   Define `SRC_my_module = $(SRC_DIR)/path/to/my_module.c [other_project_sources_needed ...]`.
        *   (Mocking is typically done for host tests. Target tests usually link against real or stubbed dependencies suitable for the target environment).
*   **Running Tests:**
    *   These compiled `.bin` files are executed using the `scripts/run_qemu_c_tests.py` script:
        ```bash
        python3 scripts/run_qemu_c_tests.py test/target/test_mysuite_qemu.bin
        ```

## 7. Running Python Unit Tests

Python unit tests verify utility scripts and other Python code in the project.

*   **Makefile:** Root `Makefile`.
*   **Target:** `make test_python`.
*   **Mechanism:** This target invokes `python3 -m unittest discover -s ./test/python -p "test_*.py" -v`.
*   Refer to `docs/UNIT_TESTING_PYTHON.md` for details on writing Python tests.

## 8. Root `Makefile` Overview

The `Makefile` in the project root provides convenient top-level targets to manage various build and test operations:

*   `make all`: Default target (currently informational).
*   `make help`: Displays a list of available main targets.
*   `make test_c_host`: Builds and runs all host C unit tests.
*   `make clean_c_host`: Cleans host C unit test artifacts.
*   `make build_c_target_tests`: Builds all target C unit test binaries for QEMU.
*   `make clean_c_target_tests`: Cleans target C unit test artifacts.
*   `make test_python`: Runs all Python unit tests.
*   `make clean`: A master clean target that invokes `clean_c_host`, `clean_c_target_tests`, and potentially other project-wide clean operations.

## 9. Build Customization & Troubleshooting

*   **Compiler Flags:** `CFLAGS`, `LDFLAGS` can be modified in the respective Makefiles for specific needs.
*   **Toolchain Path:** Ensure `arm-none-eabi-gcc` and `gcc` (and Ruby for CMock) are in your system's PATH. The CI environment installs these.
*   **Missing Dependencies:** If `apt-get` or `gem install` steps were missed during setup, builds might fail.
*   **Linker Errors (Target):** Often related to memory layout in `stm32f4_qemu.ld` or missing symbols if `nano.specs`/`rdimon.specs` are not used correctly for semihosting.
*   **Verbosity:** Most `make` commands can be run with `V=1` (e.g., `make V=1 -C firmware/...`) for more verbose output from the underlying build system if supported by that Makefile.

This guide should help you navigate and utilize the project's build system effectively.
