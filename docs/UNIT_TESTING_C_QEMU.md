# On-Target C Unit Testing in QEMU Guide

## 1. Overview

This guide explains how to set up, write, build, and run C language unit tests directly on the emulated STM32F4 target within the QEMU virtual environment. This complements host-based C unit testing by allowing tests to interact with an environment that is closer to the actual hardware, including emulated peripherals and the MicroPython C API (if linked appropriately).

The primary C unit testing framework used is **Unity**, consistent with the host-based testing setup.

## 2. Key Components

The on-target C unit testing system involves several key parts:

*   **Test Runner Firmware:** Each C unit test suite (a collection of tests for a module or feature) is compiled into a standalone ARM firmware binary (`.bin` file). This binary includes:
    *   The Unity testing framework.
    *   The test case functions.
    *   A dedicated `main()` function (the test runner) that executes the tests.
    *   The C code module(s) being tested.
    *   Minimal STM32 startup code.
*   **QEMU Automation Script (`scripts/run_qemu_c_tests.py`):** A Python script that automates:
    *   Launching QEMU with the specified test runner firmware.
    *   Capturing console output from QEMU.
    *   Implementing a timeout for the test run.
    *   Terminating QEMU.
*   **Parseable Output:** The C test runner firmware is designed to print test results to its console (which QEMU redirects) in a simple, machine-parseable format. This allows the automation script to determine pass/fail status.
*   **Semihosting for Exit:** After completing tests and printing results, the test runner firmware uses a semihosting call to signal QEMU to terminate with an exit code reflecting the test status.

## 3. Writing/Adapting C Unit Tests for QEMU Target

### Test Case Files (e.g., `test/host/test_my_module.c`)

*   Test case files written for host-based Unity tests can often be reused for on-target testing.
*   They should include `unity.h` and the header for the module under test.
*   Standard Unity assertion macros (`TEST_ASSERT_EQUAL_INT`, etc.) are used.
*   Define `setUp(void)` and `tearDown(void)` as needed for test fixtures.

### Test Runner File (e.g., `test/host/test_my_module_runner.c` adapted for target)

The test runner C file contains the `main()` function that orchestrates the test execution on the target. It needs specific adaptations for automated QEMU execution:

1.  **Include Headers:** `unity.h` and any other necessary headers (like `stdio.h` if doing extra prints).
2.  **Forward-Declare Test Functions:** Declare all test case functions from your `test_my_module.c`.
3.  **`qemu_exit()` Declaration:** Ensure `void qemu_exit(int code);` is declared (it's provided in the project's placeholder `unity.h` for target builds, and implemented in `unity.c` using semihosting).
4.  **`main()` Function:**
    ```c
    #include "unity.h"
    #include <stdio.h>

    // Forward declare test functions
    // void test_feature1(void); ...

    // If compiled for ARM target, ensure qemu_exit is available
    #if defined(__arm__) // Or your build system's target macro
    void qemu_exit(int code);
    #endif

    void setUp(void) { /* Optional: per-test setup */ }
    void tearDown(void) { /* Optional: per-test teardown */ }

    // Helper macro for current placeholder Unity to ensure parseable output
    // In full Unity, you might use custom printers or rely on its default verbose output.
    #define RUN_TEST_WITH_PARSABLE_OUTPUT_QEMU(test_func) do { \
        unsigned int current_runner_failures = UnityFailureCount; \
        unsigned int current_runner_ignores = UnityIgnoreCount; \
        UnityDefaultTestRun(test_func, #test_func, (unsigned int)__LINE__); \
        if (UnityIgnoreCount > current_runner_ignores) { \
            /* UnityIgnore() in placeholder unity.c already prints TEST(...):IGNORE */ \
        } else if (UnityFailureCount > current_runner_failures) { \
            /* UnityFailHandler() in placeholder unity.c already prints TEST(...):FAIL */ \
        } else { \
            printf("TEST(%s):PASS\n", #test_func); \
        } \
    } while(0)

    int main(void) {
        UNITY_BEGIN();

        // RUN_TEST_WITH_PARSABLE_OUTPUT_QEMU(test_feature1);
        // ... call for all test functions ...

        int overall_result = UNITY_END(); // Prints SUMMARY:T:F:I line and returns failure count

        #if defined(__arm__) // Or your build system's target macro
            qemu_exit(overall_result); // Signal QEMU to exit with test status
        #endif

        return overall_result; // Should not be reached if qemu_exit works
    }
    ```
    *   The `RUN_TEST_WITH_PARSABLE_OUTPUT_QEMU` macro helps ensure each test's outcome is printed in the format `TEST(test_name):STATUS`. This is specific to the project's current placeholder Unity setup. A full Unity installation might offer different ways to customize output.
    *   The `SUMMARY:Total:Failures:Ignored` line is printed by `UNITY_END()`.
    *   `qemu_exit(overall_result)` is critical for automation.

### Dependencies

*   Ensure that the C module under test and its dependencies can be compiled for the ARM target and function correctly within the QEMU environment (which has limited peripheral emulation).
*   Stubs used for host-based tests might need to be replaced with no-ops, simple emulations, or actual code if the interaction is being tested on target.

## 4. Build Process for Target Test Binaries

On-target C unit tests are built using the Makefile located at `test/target/Makefile`.

*   **Compiler:** `arm-none-eabi-gcc` and associated toolchain utilities.
*   **Key Components Compiled:**
    *   Unity framework (`test/frameworks/unity/unity.c`).
    *   Your test case file(s) (e.g., `test/host/test_string_utils.c`).
    *   Your adapted test runner C file (e.g., `test/host/test_string_utils_runner.c`).
    *   The C module(s) under test from `src/`.
    *   Minimal STM32 startup code (`test/target/startup_qemu_tests.c`).
    *   Linked using a target-specific linker script (`test/target/stm32f4_qemu.ld`).

### Adding a New On-Target Test Suite (e.g., for `helper_module`)

1.  **Write/Adapt Test Cases:** Create or ensure `test/host/test_helper_module.c` exists with Unity tests.
2.  **Write/Adapt Test Runner:** Create or ensure `test/host/test_helper_module_runner.c` exists, adapted as described above with parseable output and `qemu_exit()`.
3.  **Update `test/target/Makefile`:**
    *   Add `helper_module` to the `TEST_SUITES` list:
        ```makefile
        TEST_SUITES = string_utils helper_module
        ```
    *   Define the source files under test for this new suite (variable name `SRC_<suite_name>`):
        ```makefile
        SRC_helper_module = $(SRC_DIR)/utils/helper_module.c $(SRC_DIR)/another_dep.c
        ```
4.  **Build:**
    *   Navigate to `test/target/`.
    *   Run `make test_helper_module_qemu.bin` to build just this suite, or `make all` for all suites.

## 5. Running Automated Tests via `run_qemu_c_tests.py`

The Python script `scripts/run_qemu_c_tests.py` executes a compiled test firmware binary in QEMU and reports results.

*   **Syntax:**
    ```bash
    python scripts/run_qemu_c_tests.py <path_to_test_firmware.bin> [options]
    ```
*   **Example:**
    ```bash
    python scripts/run_qemu_c_tests.py test/target/test_string_utils_qemu.bin
    ```
*   **Common Options:**
    *   `--qemu_exe /path/to/qemu-system-arm`: Specify QEMU executable if not found automatically.
    *   `--timeout <seconds>`: Set a custom timeout for QEMU execution (default is 30s).
*   **Output:** The script will show:
    1.  The QEMU command being executed.
    2.  A section `--- QEMU STDOUT ---` containing all console output from your test runner (including `TEST(...)` and `SUMMARY(...)` lines).
    3.  A section `--- QEMU STDERR ---` if QEMU produces any error output (some semihosting messages are normal).
    4.  A final `--- Test Execution Summary ---` from the Python script, showing counts and overall status.
*   **Exit Codes from `run_qemu_c_tests.py`:**
    *   `0`: All tests in the suite passed.
    *   `1`: Test failures occurred, or QEMU reported an error/timeout.
    *   `2`: Script setup error (e.g., QEMU executable or firmware binary not found).

## 6. Troubleshooting Tips

*   **QEMU Timeout:**
    *   The test suite might be taking too long. Increase with `--timeout`.
    *   Ensure `qemu_exit()` is correctly called at the end of your test runner's `main()`.
    *   Check for infinite loops in tests or code under test.
*   **Build Failures (in `test/target/Makefile`):**
    *   Check include paths (`-I`) for all necessary headers.
    *   Verify the linker script (`stm32f4_qemu.ld`) and that all symbols are resolved.
    *   Ensure `arm-none-eabi-gcc` toolchain is in your PATH and working.
    *   Ensure `--specs=rdimon.specs` is used in LDFLAGS for semihosting.
*   **No Parseable Output / Incorrect Summary:**
    *   Double-check the `printf` statements in your C test runner match the exact format expected by `run_qemu_c_tests.py`:
        *   `TEST(test_name):PASS`
        *   `TEST(test_name):FAIL:message at line_number`
        *   `TEST(test_name):IGNORE:message at line_number`
        *   `SUMMARY:total:failures:ignored`
*   **Semihosting Not Working:**
    *   Ensure QEMU command in `run_qemu_c_tests.py` includes `-semihosting-config enable=on,target=native` and `-semihosting`.
    *   Ensure your target firmware (linked with `rdimon.specs`) correctly implements the semihosting `bkpt` instruction for `qemu_exit`.

## 7. Notes on Unity and Parseable Output

The Unity framework files in `test/frameworks/unity/` are representative versions that provide standard macros and functionality. The test runner (e.g., `test_my_module_runner.c`) has been adapted to ensure machine-parseable output for automation:

*   **Individual Test Results:** `TEST(test_name):PASS/FAIL/IGNORE` lines.
    *   `FAIL` and `IGNORE` lines (including messages and line numbers) are typically printed by Unity's assertion macros or `TEST_IGNORE` itself when they detect a failure or ignore directive.
    *   `PASS` lines for individual tests are printed by a custom macro (e.g., `MY_RUN_TEST` in the example `test_string_utils_runner.c`) in the runner after confirming the test did not fail or was not ignored. This ensures every test has a clear status line.
*   **Summary Line:** `UNITY_END()` in the runner prints a final `SUMMARY:Total:Failures:Ignored` line.
*   **QEMU Exit:** The runner's `main()` function calls `qemu_exit(status_code)` using semihosting to terminate QEMU with an exit code reflecting the overall test suite status.

This setup allows the `scripts/run_qemu_c_tests.py` script to correctly parse results. If using a different version of Unity or a different custom runner, ensure this parseable output format is maintained for compatibility with the automation script.
