# Host-Based C Unit Testing Guide

## 1. Overview

This guide describes how to write, build, and run host-based unit tests for C modules in this project. Host-based testing allows for rapid testing of C code logic on the development machine (Linux, macOS, etc.) without needing to run on the QEMU target.

The chosen unit testing framework is **Unity**. Unity is a lightweight and simple framework designed specifically for unit testing C code, making it well-suited for embedded projects and easy to integrate.

## 2. Directory Structure

All files related to host-based C unit testing are located within the `test/host/` directory. The Unity framework itself is (or should be) located in `test/frameworks/unity/`.

*   `test/frameworks/unity/`: Contains Unity's source files (`unity.c`, `unity.h`, `unity_internals.h`). These are currently representative versions of the official files, providing standard macros and functionality.
*   `test/host/`: This directory contains:
    *   `Makefile`: For building and running host-based tests using `gcc`.
    *   `test_*.c`: Files containing test case functions for a specific C module (e.g., `test_string_utils.c`).
    *   `test_*_runner.c`: Files containing the `main()` function for a test suite, which runs the test cases from the corresponding `test_*.c` file (e.g., `test_string_utils_runner.c`).

## 3. Writing Unit Tests

### Including Headers

Your test case file (e.g., `test_my_module.c`) should include:
```c
#include "unity.h" // For Unity assertion macros
#include "path/to/my_module.h" // Header for the C module you are testing
// Other necessary standard C headers (e.g., string.h, stdint.h)
```
The include path for `my_module.h` is typically relative to the `src/` directory (e.g., `utils/string_utils.h`), as `test/host/Makefile` adds `../../src` to the include paths.

### Test Case Functions

Test case functions are standard C functions with a `void` return type and no arguments:
```c
void test_my_feature_description(void) {
    // Your test logic and assertions here
}
```

### Unity Assertions

Unity provides a rich set of assertion macros. Here are some common ones:

*   `TEST_ASSERT_EQUAL_INT(expected, actual);`
*   `TEST_ASSERT_EQUAL_UINT(expected, actual);`
*   `TEST_ASSERT_EQUAL_HEX8(expected, actual);` (and 16, 32)
*   `TEST_ASSERT_EQUAL_STRING(expected, actual);`
*   `TEST_ASSERT_EQUAL_MEMORY(expected_ptr, actual_ptr, num_bytes);`
*   `TEST_ASSERT_NULL(pointer);`
*   `TEST_ASSERT_NOT_NULL(pointer);`
*   `TEST_ASSERT_TRUE(condition);`
*   `TEST_ASSERT_FALSE(condition);
*   `TEST_FAIL_MESSAGE("Failure reason");`
*   `TEST_IGNORE_MESSAGE("Reason for ignoring this test");` (causes test to be skipped)

These macros (and many more) are available when using the standard Unity framework.

### `setUp()` and `tearDown()`

You can define optional `setUp(void)` and `tearDown(void)` functions in your test case file (e.g., `test_my_module.c`).
*   `setUp()`: Executed before each test case in that file. Useful for common initialization.
*   `tearDown()`: Executed after each test case in that file. Useful for common cleanup.

If not needed, you can omit them, but if your test runner's `RUN_TEST` macro expects them (like the one in the placeholder Unity files might), provide empty definitions:
```c
void setUp(void) { /* No setup needed */ }
void tearDown(void) { /* No teardown needed */ }
```

### Test Runner File

For each module or group of related tests, you need a "runner" C file (e.g., `test_my_module_runner.c`). This file contains the `main()` function that executes your tests.

```c
#include "unity.h"

// Forward declarations of all your test functions from test_my_module.c
void test_my_feature_description(void);
void test_another_feature(void);
// ... more test functions

// setUp() and tearDown() should be defined in your test_my_module.c file if needed.
// Unity's RUN_TEST macro will call them. If they are not needed, you can
// define empty ones in test_my_module.c or rely on Unity's weak-symbol defaults
// if your Unity version provides them (the representative version does).

int main(void) {
    UNITY_BEGIN(); // Call first

    // Use the RUN_TEST macro from unity.h for each test case
    RUN_TEST(test_my_feature_description);
    RUN_TEST(test_another_feature);
    // ... more RUN_TEST calls

    return UNITY_END(); // Call last; returns 0 on pass, non-zero on fail
}
```

## 4. Adding a New Test Suite

To add tests for a new C module (e.g., `src/new_utils/helper.c`):

1.  **Create Test Case File:**
    Create `test/host/test_helper.c`. Write your test functions using Unity assertions, and include `unity.h` and `new_utils/helper.h`. Define `setUp()` and `tearDown()` if needed.

2.  **Create Test Runner File:**
    Create `test/host/test_helper_runner.c`. Include `unity.h`, forward-declare test functions from `test_helper.c`, and implement `main()` with `UNITY_BEGIN()`, `RUN_TEST(...)` calls, and `UNITY_END()`.

3.  **Update `test/host/Makefile`:**
    *   Add the base name `helper` to the `TEST_SUITES` list:
        ```makefile
        TEST_SUITES = string_utils helper
        ```
    *   Define the source files under test for this new suite. This variable **must** be named `SRC_<suite_basename>`:
        ```makefile
        SRC_helper = ../../src/new_utils/helper.c ../../src/new_utils/another_dependency.c # Add all .c files needed
        ```

## 5. Building and Running Tests

Open your terminal:

*   **Navigate to the test directory:**
    ```bash
    cd test/host
    ```
*   **Build all test suites:**
    ```bash
    make
    ```
    (or `make all`)
    This will create executables like `test_string_utils.out`, `test_helper.out`.
*   **Run all test suites:**
    ```bash
    make run_tests
    ```
    This will execute each test program and print a summary. If any test fails, it will print details and the `make run_tests` command will exit with a non-zero status code (useful for CI).
*   **Run a specific test suite executable:**
    ```bash
    ./test_string_utils.out
    ```
*   **Clean build artifacts:**
    ```bash
    make clean
    ```
You can also run these commands from the project root using `make -C test/host <target>`.

## 6. Guidelines & Best Practices

*   **Focus:** Each test case should ideally test one specific piece of functionality or behavior.
*   **Independence:** Tests should be independent of each other. The order of execution should not matter.
*   **Naming:** Use descriptive names for test functions (e.g., `test_functionName_condition_expectedBehavior`).
*   **Edge Cases:** Test boundary conditions, null inputs, error conditions, etc.
*   **Dependencies & Mocking:**
    *   For host-based tests, C modules under test should ideally have minimal direct dependencies on hardware or MicroPython runtime features that are unavailable on the host.
    *   If a module depends on another simple utility module, you can compile both into the test executable by listing them in the `SRC_<suite_name>` variable in the Makefile.
    *   For complex dependencies (hardware registers, RTOS functions, complex MicroPython APIs):
        *   **Stubs:** Provide simple, dummy implementations of these functions that return fixed values suitable for the test. These stubs can be compiled as part of the test.
        *   **Mocking (Advanced):** For more advanced control over dependencies (e.g., verifying calls, setting return values per call), a mocking framework like CMock (which integrates with Unity via Ceedling) would be needed. This is considered a future enhancement if required. For now, focus on testing modules that can be reasonably isolated or tested with simple stubs.

This setup provides a solid foundation for C unit testing on the host. As the project grows, further enhancements like mocking or on-target testing can be considered.

## 7. Mocking Dependencies with CMock

For more effective unit testing, it's often necessary to isolate the unit under test from its dependencies. This project uses **CMock** to generate mock interfaces for C header files, allowing you to control the behavior of dependencies during tests. CMock works seamlessly with the Unity testing framework.

### Prerequisites for Using CMock

*   **Ruby and CMock Gem:** CMock is a Ruby-based tool. To generate mocks locally, you need:
    1.  A working Ruby installation (e.g., version 2.7 or newer).
    2.  The CMock gem installed: `gem install cmock`
    *   The CI environment (GitHub Actions) is automatically configured to install Ruby and CMock.

### How CMock is Integrated

1.  **Mock Generation via Makefile:**
    *   The `test/host/Makefile` is configured to automatically generate mocks.
    *   You specify which headers to mock in the `HEADERS_TO_MOCK` list within this Makefile:
        ```makefile
        # test/host/Makefile
        HEADERS_TO_MOCK = \
            src/peripherals/sensor_reader.h \
            src/another_module/interface.h # Add other headers here
        ```
    *   When you run `make` (or `make all`, `make run_tests`) in the `test/host/` directory, the Makefile will invoke `cmock` for each listed header if the mock files are missing or the original header has changed.
    *   Generated mocks (e.g., `mock_sensor_reader.c` and `mock_sensor_reader.h`) are placed in `test/host/build/mocks/`. This directory is automatically included in the compiler's include path for tests.

2.  **Linking Mocks:**
    *   For each test suite (e.g., defined by `test_foo_runner.c`), you need to specify which generated mock C files it depends on. This is done by defining a variable `MOCKS_FOR_foo` in `test/host/Makefile`:
        ```makefile
        # test/host/Makefile
        # For a test suite 'data_processor' (leading to test_data_processor.out)
        MOCKS_FOR_data_processor = $(MOCKS_OUTPUT_DIR)/mock_sensor_reader.c
        # If a suite needs multiple mocks:
        # MOCKS_FOR_another_suite = $(MOCKS_OUTPUT_DIR)/mock_dep1.c $(MOCKS_OUTPUT_DIR)/mock_dep2.c
        ```
    *   The Makefile then links only these specified mock C files when building the test executable for that suite.

### Writing Unit Tests with CMock

Here's the typical pattern for using generated mocks in your test file (e.g., `test_data_processor.c` testing `data_processor.c` which uses `sensor_reader.h`):

1.  **Include Headers:**
    ```c
    #include "unity.h"
    #include "mock_sensor_reader.h"      // Include the generated mock header
    #include "processing/data_processor.h" // The module under test
    ```

2.  **`setUp()` and `tearDown()`:**
    *   Initialize the mock for the specific dependency in `setUp()`.
    *   Verify all mock expectations and clean up the mock in `tearDown()`.
    ```c
    void setUp(void) {
        mock_sensor_reader_Init();
    }

    void tearDown(void) {
        mock_sensor_reader_Verify();
        mock_sensor_reader_Destroy();
    }
    ```

3.  **Setting Expectations in Test Cases:**
    Before calling the function under test, set expectations for any functions from the mocked interface that you anticipate will be called.

    *   **Expect a call and return a value:**
        ```c
        // Expect sensor_read_temperature_degrees_c() to be called once, and make it return 250.
        sensor_read_temperature_degrees_c_ExpectAndReturn(250);
        ```
    *   **Expect a call (don't care about arguments, return a value):**
        ```c
        sensor_self_test_ExpectAnyArgsAndReturn(true);
        ```
    *   **Expect a call and modify an output parameter (pointer argument):**
        ```c
        uint8_t expected_result_code = 0x00;
        // Expect sensor_self_test to be called. When it is, the value of expected_result_code (0x00)
        // will be copied to the argument passed as 'result_code'.
        sensor_self_test_ExpectAnyArgsAndReturn(true); // Or _Expect with specific args
        sensor_self_test_ReturnThruPtr_result_code(&expected_result_code);
        ```
    *   **Ignoring calls:**
        ```c
        // If sensor_init might be called but you don't care about its return for this test
        sensor_init_IgnoreAndReturn(true);
        ```
    *   **Callbacks:** CMock supports setting up callbacks for more complex argument validation or behavior.
        ```c
        // Advanced: define a callback function
        // uint8_t my_self_test_callback(uint8_t* ptr, int num_calls) {
        //     *ptr = 0xAA; // Modify the output param
        //     return true; // Return value for sensor_self_test
        // }
        // sensor_self_test_Stub(my_self_test_callback); // Call the stub instead of original
        // Or: sensor_self_test_ExpectAnyArgs();
        //     sensor_self_test_AddCallback(my_self_test_callback_wrapper);
        ```

4.  **Call the Function Under Test:**
    ```c
    sensor_system_status_t status = initialize_sensor_system(); // This calls mocked functions
    ```

5.  **Assert Results:**
    Use standard Unity assertions to verify the behavior of your function under test, based on the controlled behavior of its mocked dependencies.
    ```c
    TEST_ASSERT_EQUAL_INT(SENSOR_STATUS_OK, status);
    ```

CMock generates many useful expectation functions based on your header file. Refer to the CMock documentation and the generated `mock_*.h` file for the full API available for your mocked module. Common patterns include `_ExpectAndReturn`, `_IgnoreAndReturn`, `_ExpectAnyArgsAndReturn`, `_ReturnThruPtr_<arg_name>`, `_Stub`, `_AddCallback`.
