# Makefile for host-based C unit tests using Unity

.PHONY: all clean run_tests

# Compiler and common flags
CC = gcc
CFLAGS_COMMON = -std=c11 -Wall -Wextra -g
UNITY_FRAMEWORK_PATH = ../frameworks/unity
# Include path for Unity headers
CFLAGS += -I$(UNITY_FRAMEWORK_PATH)
# Include path for source files under test (assuming they are in ../../src)
CFLAGS += -I../../src
# Include path for any other project headers (e.g. from config)
# CFLAGS += -I../../config # Example if needed

# Unity framework source file
UNITY_SRC = $(UNITY_FRAMEWORK_PATH)/unity.c

# List of test suite base names (e.g., string_utils, another_module)
# For each 'foo' in TEST_SUITES, expects:
# - test_foo.c (test cases)
# - test_foo_runner.c (main for the test suite)
# - SRC_foo variable listing source files under test (e.g., ../../src/utils/foo.c)
TEST_SUITES = string_utils
# Example: TEST_SUITES += new_feature_utils

TEST_EXECUTABLES = $(foreach suite,$(TEST_SUITES),test_$(suite).out)

all: $(TEST_EXECUTABLES)

# Define sources for each suite
# These variables MUST be named SRC_<suite_name> (e.g. SRC_string_utils)
SRC_string_utils = ../../src/utils/string_utils.c
# Example: SRC_new_feature_utils = ../../src/new_feature/utils.c ../../src/new_feature/helpers.c


# Rule to build each test executable
# Takes test_SUITE_NAME.out, depends on test_SUITE_NAME.runner.c, test_SUITE_NAME.c,
# UNITY_SRC, and the sources listed in SRC_SUITE_NAME.
$(TEST_EXECUTABLES): %.out: test_%.runner.c test_%.c $(UNITY_SRC)
	@echo "Building test executable $@ from $^ and $(SRC_$(basename $(patsubst test_%,%,$@)))..."
	$(CC) $(CFLAGS) $^ $(SRC_$(basename $(patsubst test_%,%,$@))) -o $@

# Target to run all built test executables
run_tests: $(TEST_EXECUTABLES)
	@echo ""
	@echo "Running all C host unit tests..."
	@echo "=================================="
	@passed_all=true; \
	for test_exe in $(TEST_EXECUTABLES); do \
		echo ""; \
		echo "--- Running $$test_exe ---"; \
		./$$test_exe; \
		if [ $$? -ne 0 ]; then \
			echo "!!! TEST SUITE $$test_exe FAILED !!!"; \
			passed_all=false; \
		else \
			echo "--- TEST SUITE $$test_exe PASSED ---"; \
		fi; \
	done; \
	echo ""; \
	echo "=================================="; \
	if $$passed_all; then \
		echo "All C host test suites PASSED."; \
	else \
		echo "SOME C HOST TEST SUITES FAILED."; \
		exit 1; \
	fi

# Clean up build artifacts
clean:
	@echo "Cleaning host test build artifacts..."
	rm -f $(TEST_EXECUTABLES) *.o
	rm -rf *.dSYM # macOS debug symbols
	@echo "Done."
