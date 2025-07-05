# Root Makefile for the qemu-micropython project

.PHONY: all clean test_c_host test_c_target test_python help

all:
	@echo "Default target: No overall build action defined yet."
	@echo "Try 'make help' for available targets."

# --- Host-based C Unit Tests ---
# Assumes test/host/Makefile exists and handles these.
test_c_host:
	@echo "Building and running host C unit tests..."
	$(MAKE) -C test/host run_tests

clean_c_host:
	@echo "Cleaning host C unit test artifacts..."
	$(MAKE) -C test/host clean

# --- Target-based C Unit Tests (QEMU) ---
# Assumes test/target/Makefile exists and handles building.
# Running them is typically done via scripts/run_qemu_c_tests.py per suite.
build_c_target_tests:
	@echo "Building C unit test binaries for QEMU target..."
	$(MAKE) -C test/target all

# Example of how one might run a specific target test (manual step for now)
# run_string_utils_c_target_test: build_c_target_tests
#	@echo "Running string_utils C target tests in QEMU..."
#	python3 scripts/run_qemu_c_tests.py test/target/test_string_utils_qemu.bin

clean_c_target_tests:
	@echo "Cleaning target C unit test artifacts..."
	$(MAKE) -C test/target clean


# --- Python Unit Tests ---
test_python:
	@echo "Running Python unit tests..."
	@echo "Discovery root: test/python, pattern: test_*.py"
	python3 -m unittest discover -s ./test/python -p "test_*.py" -v
	@echo "Python unit tests execution finished."

# --- General Clean Target ---
clean: clean_c_host clean_c_target_tests
	@echo "Running main clean..."
	# Add other project-wide clean commands here if needed
	@echo "Main clean finished."

# --- Help Target ---
help:
	@echo "Available make targets:"
	@echo "  all                         - Default target (currently does nothing specific)."
	@echo "  test_c_host               - Build and run host-based C unit tests."
	@echo "  clean_c_host              - Clean host-based C unit test artifacts."
	@echo "  build_c_target_tests      - Build C unit test binaries for QEMU target."
	@echo "  clean_c_target_tests      - Clean QEMU target C unit test artifacts."
	# @echo "  run_string_utils_c_target_test - Example to run one specific QEMU test suite."
	@echo "  test_python               - Run Python unit tests."
	@echo "  clean                       - Run all clean targets."
	@echo "  help                        - Show this help message."
