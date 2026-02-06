# Test Structure Documentation

## Overview
This document describes the test structure for the qemu-micropython project.

## Test Directory Structure

```
tests/
├── .gitkeep                           # Keep empty test directory in git
├── gdb_integration_tests.md           # Documentation for GDB integration tests
├── test_exception_handling.py         # Exception handling tests
├── test_exception_visualization.py    # Exception visualization tests
├── test_gdb_exception_handling.py     # GDB-specific exception tests
├── test_gdb_integration.py           # Main GDB integration test suite
├── test_semihosting.py               # Semihosting functionality tests
└── unit/
    └── test_sensors.py               # Unit tests for sensor modules
```

## Test Categories

### 1. GDB Integration Tests
**Location:** `tests/test_gdb_integration.py`
**Purpose:** Tests the integration between QEMU, MicroPython, and GDB
**Key Features:**
- Basic GDB connectivity
- Breakpoint functionality
- Variable inspection
- Stack trace analysis

**Documentation:** See `tests/gdb_integration_tests.md` for detailed information

### 2. Exception Handling Tests
**Location:** 
- `tests/test_exception_handling.py` - Basic exception tests
- `tests/test_gdb_exception_handling.py` - GDB-specific exception tests
- `tests/test_exception_visualization.py` - Exception visualization tests

**Purpose:** Validate exception handling in MicroPython running on QEMU
**Key Features:**
- Exception detection and reporting
- Stack trace generation
- Exception visualization
- GDB exception breakpoints

### 3. Semihosting Tests
**Location:** `tests/test_semihosting.py`
**Purpose:** Test semihosting functionality for QEMU console I/O
**Key Features:**
- Semihosting API availability
- Console output via semihosting
- Character and string output

### 4. Unit Tests
**Location:** `tests/unit/`
**Purpose:** Unit tests for individual components
**Current Tests:**
- `test_sensors.py` - Sensor module functionality

## Running Tests

### Prerequisites
1. QEMU must be installed and accessible
2. MicroPython firmware must be built
3. GDB (arm-none-eabi-gdb) must be installed for GDB tests

### Running All Tests
```bash
python -m pytest tests/ -v
```

### Running Specific Test Categories

**GDB Integration Tests:**
```bash
python3 tests/test_gdb_integration.py
```

**Exception Handling Tests:**
```bash
python3 tests/test_exception_handling.py
python3 tests/test_gdb_exception_handling.py
python3 tests/test_exception_visualization.py
```

**Semihosting Tests:**
```bash
python3 tests/test_semihosting.py
```

**Unit Tests:**
```bash
python -m pytest tests/unit/ -v
```

## CI/CD Integration

Tests are run as part of the GitHub Actions workflow in `.github/workflows/ci.yml`.

### CI Test Execution Flow:
1. **Validate** - Linting and static analysis
2. **Build** - Firmware compilation
3. **Test** - Execute test suite
   - GDB integration tests
   - Exception handling tests
   - Unit tests

## Test Dependencies

### Python Dependencies
- pytest
- pytest-timeout (for test timeouts)
- subprocess (for QEMU/GDB interaction)

### System Dependencies
- QEMU (qemu-system-arm)
- GDB (arm-none-eabi-gdb)
- Built MicroPython firmware

## Adding New Tests

### For Unit Tests
1. Create test file in `tests/unit/`
2. Follow pytest conventions
3. Name file `test_*.py`
4. Use descriptive test function names `test_*`

### For Integration Tests
1. Create test file in `tests/`
2. Use subprocess to interact with QEMU/GDB
3. Add timeout decorators for long-running tests
4. Document test purpose and requirements

## Test Best Practices

1. **Isolation:** Each test should be independent
2. **Cleanup:** Always clean up processes (QEMU, GDB)
3. **Timeouts:** Use timeouts to prevent hanging tests
4. **Documentation:** Document complex test setups
5. **Error Messages:** Provide clear failure messages

## Known Issues and Limitations

1. **Timing Issues:** QEMU startup can be slow, affecting test timing
2. **GDB Version:** Some features require specific GDB versions
3. **Platform Specific:** Tests may behave differently on different OS

## Future Test Improvements

1. Add more unit tests for core modules
2. Implement performance tests
3. Add memory leak detection
4. Expand exception handling coverage
5. Add network/peripheral tests

## Troubleshooting

### Test Failures
- Check QEMU and GDB are properly installed
- Verify firmware is built correctly
- Check for port conflicts (GDB default port 1234)
- Review test output for specific error messages

### Timeout Issues
- Increase timeout values in test decorators
- Check system resources (CPU, memory)
- Verify QEMU is not hanging

### GDB Connection Issues
- Ensure no other process is using GDB port
- Check firewall settings
- Verify arm-none-eabi-gdb is in PATH

## References

- [MicroPython Documentation](https://docs.micropython.org/)
- [QEMU Documentation](https://www.qemu.org/docs/master/)
- [GDB Documentation](https://sourceware.org/gdb/documentation/)
- [pytest Documentation](https://docs.pytest.org/)
