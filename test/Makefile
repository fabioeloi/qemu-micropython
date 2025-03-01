# Makefile for simple STM32F4 QEMU test

# Toolchain
CC = arm-none-eabi-gcc
OBJCOPY = arm-none-eabi-objcopy
SIZE = arm-none-eabi-size

# Flags
CFLAGS = -mcpu=cortex-m4 -mthumb -O0 -g3 -Wall -Wextra
LDFLAGS = -Wl,--gc-sections -nostartfiles -T stm32f4.ld

# Source files
SRCS = simple_test.c startup.c

# Output files
TARGET = simple_test
ELF = $(TARGET).elf
BIN = $(TARGET).bin

# Default target
all: $(BIN)

# Compile
$(ELF): $(SRCS) stm32f4.ld
	$(CC) $(CFLAGS) $(LDFLAGS) $(SRCS) -o $@
	$(SIZE) $@

# Create binary
$(BIN): $(ELF)
	$(OBJCOPY) -O binary $< $@

# Clean
clean:
	rm -f $(ELF) $(BIN)

# Run in QEMU
run: $(BIN)
	qemu-system-arm -machine olimex-stm32-h405 -cpu cortex-m4 -m 128K \
	-kernel $(BIN) -serial stdio -monitor none -nographic \
	-semihosting-config enable=on,target=native -semihosting

.PHONY: all clean run 