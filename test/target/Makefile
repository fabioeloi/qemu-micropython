# Makefile for On-Target (QEMU) C Unit Tests

.PHONY: all clean

# Toolchain (ARM cross-compiler)
PREFIX = arm-none-eabi-
CC = $(PREFIX)gcc
LD = $(PREFIX)gcc
OBJCOPY = $(PREFIX)objcopy
SIZE = $(PREFIX)size

# Project Paths
ROOT_DIR = ../..
SRC_DIR = $(ROOT_DIR)/src
UNITY_FRAMEWORK_PATH = ../frameworks/unity
TARGET_TEST_DIR = . # Current directory (test/target)
HOST_TEST_DIR = ../host # Location of test case files like test_string_utils.c

# Common Flags
# CFLAGS: For Cortex-M4, Thumb mode, debugging, warnings.
# Ensure include paths for Unity, project source, and project config.
# -Wno-old-style-declaration needed for placeholder unity's main/RUN_TEST.
CFLAGS = -mcpu=cortex-m4 -mthumb -O0 -g3 -Wall -Wextra -Wno-old-style-declaration
CFLAGS += -I$(UNITY_FRAMEWORK_PATH)
CFLAGS += -I$(SRC_DIR) # To find "utils/string_utils.h" etc.
# CFLAGS += -I$(ROOT_DIR)/config # If any global configs are needed by src files

# LDFLAGS: Linker flags.
LDFLAGS = -Wl,--gc-sections -nostartfiles -T$(TARGET_TEST_DIR)/stm32f4_qemu.ld
LDFLAGS += --specs=nano.specs --specs=rdimon.specs # rdimon for semihosting with newlib-nano

# Unity framework source
UNITY_SRC = $(UNITY_FRAMEWORK_PATH)/unity.c

# Startup code for bare-metal execution on target
STARTUP_SRC = $(TARGET_TEST_DIR)/startup_qemu_tests.c

# List of test suite base names (e.g., string_utils)
TEST_SUITES = string_utils
# Example: TEST_SUITES += new_feature

# Generate .elf and .bin targets for each suite
TEST_ELFS = $(foreach suite,$(TEST_SUITES),test_$(suite)_qemu.elf)
TEST_BINS = $(foreach suite,$(TEST_SUITES),test_$(suite)_qemu.bin)

all: $(TEST_BINS)

# Define sources under test for each suite
# These variables MUST be named SRC_<suite_name> (e.g. SRC_string_utils)
SRC_string_utils = $(SRC_DIR)/utils/string_utils.c
# Example: SRC_new_feature = $(SRC_DIR)/new_feature/utils.c $(SRC_DIR)/new_feature/helpers.c


# Rule to build each test executable (.elf and .bin)
# test_SUITE_qemu.elf depends on:
# - test_SUITE_runner.c (specific to this suite, expected in TARGET_TEST_DIR or HOST_TEST_DIR)
# - test_SUITE.c (the actual tests, expected in HOST_TEST_DIR)
# - $(UNITY_SRC)
# - $(STARTUP_SRC)
# - $(SRC_SUITE) (the module(s) being tested)

# For simplicity, assume runner and test case files are co-located or paths are adjusted.
# Using HOST_TEST_DIR for both runner and test cases for now, as runner was adapted.
define COMPILE_TEST_SUITE_TARGET
test_$(1)_qemu.elf: $(HOST_TEST_DIR)/test_$(1)_runner.c $(HOST_TEST_DIR)/test_$(1).c $(UNITY_SRC) $(STARTUP_SRC) $($(SRC_$(1))) $(TARGET_TEST_DIR)/stm32f4_qemu.ld
	@echo "Building Target Test ELF: $$@"
	$(CC) $(CFLAGS) $(LDFLAGS) \
		$(HOST_TEST_DIR)/test_$(1)_runner.c \
		$(HOST_TEST_DIR)/test_$(1).c \
		$(UNITY_SRC) \
		$(STARTUP_SRC) \
		$($(SRC_$(1))) \
		-o $$@
	$(SIZE) $$@

test_$(1)_qemu.bin: test_$(1)_qemu.elf
	@echo "Creating Target Test BIN: $$@"
	$(OBJCOPY) -O binary $$< $$@

ALL_COMPILED_TARGETS += test_$(1)_qemu.elf test_$(1)_qemu.bin
endef

# Instantiate the rule for each test suite
$(foreach suite,$(TEST_SUITES),$(eval $(call COMPILE_TEST_SUITE_TARGET,$(suite))))

clean:
	@echo "Cleaning target test build artifacts..."
	rm -f $(ALL_COMPILED_TARGETS) $(TEST_ELFS) $(TEST_BINS) # Ensure all variables are used
	@echo "Done."

# Note: This Makefile assumes:
# 1. test_SUITE_runner.c and test_SUITE.c (test cases) are in test/host/.
#    This reuses the host test files for target compilation. The runner was adapted.
# 2. startup_qemu_tests.c and stm32f4_qemu.ld are in test/target/.
# 3. `qemu_exit` is implemented (e.g., in unity.c or the runner) for semihosting exit.
