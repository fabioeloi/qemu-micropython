CC = gcc
CFLAGS = -Wall -Wextra -g -std=c99
LDFLAGS = -lm

# Target binary
TARGET = custom_uart_test

# Source files
SRCS = custom_uart_driver.c custom_uart_test.c
OBJS = $(SRCS:.c=.o)

# Header files
DEPS = custom_uart_driver.h

# Default target
all: $(TARGET)

# Compile the target binary
$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Compile source files
%.o: %.c $(DEPS)
	$(CC) $(CFLAGS) -c $< -o $@

# Clean up
clean:
	rm -f $(OBJS) $(TARGET) uart_traffic.bin

# Run the test program
run: $(TARGET)
	./$(TARGET)

# Debug with gdb
debug: $(TARGET)
	gdb $(TARGET)

.PHONY: all clean run debug 