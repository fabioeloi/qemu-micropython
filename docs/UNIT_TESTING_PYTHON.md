# Python Unit Testing Guide

## 1. Overview

This guide describes how to write, build, and run unit tests for Python scripts and modules within this project. Python unit testing is essential for verifying the correctness of helper scripts, tools, and any host-side Python logic.

The standard Python built-in **`unittest`** module is used as the testing framework.

## 2. Directory Structure

All Python unit tests should be located within the `test/python/` directory at the root of the project.

*   **`test/python/`**: The root directory for Python tests.
*   **Subdirectories:** You can create subdirectories within `test/python/` to mirror the structure of the Python code you are testing. For example, tests for scripts in the main `scripts/` directory could go into `test/python/scripts/`.
    *   Example: `test/python/scripts/test_run_qemu_c_tests_parser.py` (tests parts of `scripts/run_qemu_c_tests.py`).
*   **Test Files:** Test files must be named following the pattern `test_*.py` for `unittest` discovery to find them automatically (e.g., `test_my_module.py`).

## 3. Writing Python Unit Tests

### Basic Structure

A typical Python test file using `unittest` looks like this:

```python
import unittest
# Attempt to import the module or functions you want to test
# This might require sys.path adjustments if running the test file directly,
# but `python -m unittest discover` from the project root often handles imports correctly
# if your project has a proper structure or __init__.py files in directories.
# Example: from scripts.my_script_module import my_function
# For testing standalone scripts, you might need to import it carefully or redefine parts.

class TestMyScriptFunctionality(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Code to run once before all tests in this class
        pass

    @classmethod
    def tearDownClass(cls):
        # Code to run once after all tests in this class
        pass

    def setUp(self):
        # Code to run before each individual test method
        self.my_object = SomeClassToTest() # Example
        pass

    def tearDown(self):
        # Code to run after each individual test method
        pass

    def test_function_A_with_valid_input(self):
        # result = my_module.function_A("valid_input")
        # self.assertEqual(result, "expected_output")
        self.assertTrue(True) # Placeholder

    def test_function_A_handles_edge_case(self):
        # with self.assertRaises(ValueError):
        #    my_module.function_A("invalid_input_causing_value_error")
        pass

    # More test methods, each starting with test_
    # def test_another_feature(self):
    #    ...

if __name__ == '__main__':
    # Allows running this test file directly: python path/to/test_my_script.py
    unittest.main(verbosity=2)
```

### Key `unittest.TestCase` Assertions

Here are some commonly used assertion methods available in `unittest.TestCase`:

*   `assertEqual(a, b, msg=None)`: Tests that `a` and `b` are equal.
*   `assertNotEqual(a, b, msg=None)`: Tests that `a` and `b` are not equal.
*   `assertTrue(x, msg=None)`: Tests that `x` is true.
*   `assertFalse(x, msg=None)`: Tests that `x` is false.
*   `assertIsNone(x, msg=None)`: Tests that `x` is `None`.
*   `assertIsNotNone(x, msg=None)`: Tests that `x` is not `None`.
*   `assertIn(member, container, msg=None)`: Tests that `member` is in `container`.
*   `assertNotIn(member, container, msg=None)`: Tests that `member` is not in `container`.
*   `assertIsInstance(obj, cls, msg=None)`: Tests that `obj` is an instance of `cls`.
*   `assertNotIsInstance(obj, cls, msg=None)`: Tests that `obj` is not an instance of `cls`.
*   `assertRaises(expected_exception, callable, *args, **kwargs)`: Tests that `callable(*args, **kwargs)` raises `expected_exception`.
*   `assertRaisesRegex(expected_exception, expected_regex, callable, *args, **kwargs)`: Similar to `assertRaises` but also checks if the exception message matches `expected_regex`.
*   Using `assertRaises` as a context manager:
    ```python
    with self.assertRaises(ValueError) as cm:
        function_that_raises_value_error("bad_input")
    # self.assertEqual(str(cm.exception), "Expected error message") # Optionally check message
    ```

Refer to the [official `unittest` documentation](https://docs.python.org/3/library/unittest.html) for a full list of assertions and features.

## 4. Running Python Unit Tests

There are several ways to run the Python unit tests:

### A. Using the Root Makefile (Recommended for CI and ease of use)

From the project's root directory:
```bash
make test_python
```
This command executes `python3 -m unittest discover -s test/python -p "test_*.py" -v`, which automatically finds all test files matching the pattern `test_*.py` within the `test/python` directory and its subdirectories, and runs them verbosely.

### B. Directly with the `unittest` Module

From the project's root directory:

*   **Run all tests in `test/python`:**
    ```bash
    python3 -m unittest discover -s test/python -p "test_*.py" -v
    ```
*   **Run a specific test file:**
    (e.g., `test/python/scripts/test_my_example.py`)
    ```bash
    python3 -m unittest test.python.scripts.test_my_example -v
    ```
*   **Run a specific test class within a file:**
    (e.g., `TestMyClass` in `test.python.scripts.test_my_example`)
    ```bash
    python3 -m unittest test.python.scripts.test_my_example.TestMyClass -v
    ```
*   **Run a specific test method within a test class:**
    (e.g., `test_specific_method` in `TestMyClass`)
    ```bash
    python3 -m unittest test.python.scripts.test_my_example.TestMyClass.test_specific_method -v
    ```

### C. Running a Test File Directly

If a test file has an `if __name__ == '__main__': unittest.main()` block, you can run it directly:
```bash
python3 test/python/scripts/test_my_example.py
```

## 5. Mocking Dependencies

For unit testing, it's crucial to isolate the code under test from its external dependencies (e.g., file system operations, network requests, subprocess calls, or modules like `gdb` when testing GDB scripts). Python's `unittest.mock` module provides powerful tools for this, primarily `Mock` and `patch`.

*   **`Mock` objects:** Can replace real objects, allowing you to define their behavior (return values, side effects) and make assertions about how they were used.
*   **`patch` (as a decorator or context manager):** Temporarily replaces objects within a specific scope (e.g., a function or module) with `Mock` objects.

**Conceptual Example (testing a function that uses `os.path.exists`):**
```python
import unittest
from unittest.mock import patch
# Assume my_module.py has:
# import os
# def check_file(filepath):
#     if os.path.exists(filepath):
#         return f"File {filepath} exists."
#     return f"File {filepath} does not exist."

# In your test_my_module.py:
# from my_module import check_file

class TestCheckFile(unittest.TestCase):
    @patch('my_module.os.path.exists') # Target the 'exists' where it's looked up
    def test_check_file_when_exists(self, mock_exists):
        mock_exists.return_value = True # Configure the mock
        # self.assertEqual(check_file("dummy.txt"), "File dummy.txt exists.")
        mock_exists.assert_called_once_with("dummy.txt")

    @patch('my_module.os.path.exists')
    def test_check_file_when_not_exists(self, mock_exists):
        mock_exists.return_value = False
        # self.assertEqual(check_file("dummy.txt"), "File dummy.txt does not exist.")
        mock_exists.assert_called_once_with("dummy.txt")
```
Refer to the [official `unittest.mock` documentation](https://docs.python.org/3/library/unittest.mock.html) for detailed usage.

## 6. CI Integration

Python unit tests are automatically executed as part of the GitHub Actions CI workflow (defined in `.github/workflows/ci.yml`). The CI uses the `make test_python` command. If any Python unit test fails, the CI run will be marked as failed.

This setup provides a robust way to ensure the quality and correctness of Python code within the project.

## 7. Special Considerations for Testing GDB Python Scripts

Unit testing Python scripts that are designed to run within GDB (e.g., `scripts/micropython_gdb.py`) requires special handling due to their dependency on the `gdb` Python module, which is only available inside an active GDB session. To unit test the Python logic of such scripts externally (e.g., via `make test_python`), you must **mock the `gdb` module**.

### Key Strategies for Mocking `gdb`

1.  **Mocking the `gdb` Module Import:**
    *   Use `unittest.mock.patch` to replace the `gdb` module that your script imports with a `MagicMock` object. The target for patching is where the `gdb` module is looked up by your script under test. For example, if your script `scripts/my_gdb_script.py` contains `import gdb`, you would typically patch it in your test as `@patch('scripts.my_gdb_script.gdb')`.

    ```python
    from unittest.mock import patch, MagicMock
    # Assuming 'scripts.my_gdb_script' is the module under test (sut)
    # import scripts.my_gdb_script as sut

    # @patch('scripts.my_gdb_script.gdb') # Correct patching target
    # def test_my_function_using_gdb_api(self, mock_gdb_module):
    #     # Configure mock_gdb_module attributes and methods
    #     mock_gdb_module.parameter.return_value = "on"
    #     mock_gdb_module.error = type('MockGdbError', (Exception,), {}) # Mock gdb.error
    #
    #     # result = sut.my_function_that_uses_gdb_parameter()
    #     # self.assertTrue(result)
    #     mock_gdb_module.parameter.assert_called_once_with("some_param")
    ```

2.  **Mocking `gdb.Value` Objects:**
    *   Functions processing `gdb.Value` objects require `MagicMock` instances that simulate `gdb.Value` behavior. This includes mocking:
        *   Attribute access (e.g., `my_gdb_value.address`, `my_gdb_value.type.code`).
        *   Method calls (e.g., `my_gdb_value.dereference()`, `my_gdb_value.cast()`, `my_gdb_value.string()`).
        *   Special Python methods if used (e.g., `__add__` for pointer arithmetic, `__getitem__` for field access like `my_gdb_value['field']`, `__int__` for casting to integer).
    *   This can be complex, requiring careful setup of the mock `gdb.Value` to match the expected structure and behavior for each test case.

3.  **Focus on Python Logic:**
    *   The primary aim is to test the Python logic within your GDB script (argument parsing, string manipulation, conditional flows, class behavior), not GDB's own functionality.
    *   Mocking allows you to control the inputs/outputs of GDB API interactions, enabling isolated testing of your script's responses.

4.  **Importing the Script Under Test:**
    *   Ensure your GDB Python script is importable by your test file. This might involve `sys.path` adjustments in your test setup (as seen in `test/python/scripts/test_micropython_gdb.py`) or structuring your `scripts` directory as a Python package (e.g., by adding an `__init__.py`).

### Example

For detailed examples of mocking the `gdb` module and its objects, refer to the test file `test/python/scripts/test_micropython_gdb.py`. This file contains tests for utilities within `scripts/micropython_gdb.py`, such as `is_color_enabled()`, `Colors.colorize()`, the `GdbByteArrayReader` class, and the argument parsing logic of `MPCatchCommand`.

By employing these mocking techniques, you can achieve effective unit test coverage for the Python logic within your GDB extension scripts, even when they are run outside the GDB environment.
