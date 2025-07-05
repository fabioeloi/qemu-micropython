# Continuous Integration (CI) Setup

This project uses GitHub Actions for its Continuous Integration (CI) pipeline to automatically build and test the codebase upon pushes and pull requests to main development branches.

## Workflow Overview

The CI workflow is defined in the file `.github/workflows/ci.yml`. It performs the following key steps:

1.  **Environment Setup:**
    *   Runs on an `ubuntu-latest` GitHub-hosted runner.
    *   Checks out the repository code.
    *   Sets up Python (version 3.10 or as specified in the workflow).
    *   Installs the ARM GCC cross-compiler toolchain (`arm-none-eabi-gcc`, `binutils`, `newlib`) using `apt-get`.
    *   Installs QEMU for ARM (`qemu-system-arm`) using `apt-get`.
    *   Installs `make`.

2.  **Build Phase:**
    *   **Main Firmware:** Attempts to build the main MicroPython firmware for the project (the exact command depends on project scripts like `scripts/build.sh` or a root Makefile target). This ensures the core project remains buildable.
    *   **Host C Unit Tests:** Compiles all C unit tests designed to run on the host machine using `make -C test/host all`. These tests use the Unity framework and `gcc`.
    *   **Target C Unit Test Binaries:** Compiles C unit tests (Unity-based) for the ARM target architecture, producing separate `.bin` files for each test suite (e.g., `test_string_utils_qemu.bin`). This is done via `make -C test/target all`.

3.  **Test Execution Phase:**
    *   **Host C Unit Tests:** Executes the compiled host tests using `make -C test/host run_tests`. The Makefile target is responsible for running all test executables and exiting with a non-zero status if any test fails.
    *   **Target C Unit Tests (QEMU):**
        *   The workflow iterates through all `test/target/test_*_qemu.bin` files.
        *   For each test binary, it runs `python3 scripts/run_qemu_c_tests.py <test_binary_path>`.
        *   The `run_qemu_c_tests.py` script launches QEMU, executes the test firmware, captures its console output (which contains parseable test results from the C/Unity test runner), and determines pass/fail status.
        *   If any test suite run via the Python script indicates a failure (by the script exiting non-zero), the entire CI step (and thus the job) will fail.

## Triggers

The CI workflow is automatically triggered on:
*   Pushes to main development branches (e.g., `main`, `master`, `develop` - check `ci.yml` for exact list).
*   Pull requests targeting these main development branches.
*   It can also be manually triggered from the "Actions" tab in the GitHub repository.

## Viewing CI Results

*   Navigate to the "Actions" tab in the GitHub repository.
*   You will see a list of workflow runs. Click on a specific run to see its details.
*   Each job (e.g., `build-and-test`) can be expanded to see the logs for each step.
*   If a step fails, its log output will usually contain error messages indicating the cause (e.g., compilation error, test assertion failure).
*   A green checkmark next to a commit or Pull Request indicates the CI pipeline passed. A red cross indicates a failure.

## CI Status Badge

The current build and test status is displayed by a badge at the top of the `README.md` file.
Example badge markdown:
`[![Build and Test CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci.yml)`
(Replace OWNER and REPO with actual values).

---

This CI setup helps ensure code quality and stability by automatically verifying that the project builds correctly and that its unit tests pass on both host and the QEMU target environment.
