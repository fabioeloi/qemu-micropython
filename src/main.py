"""
MicroPython QEMU Demo
Simple test script focused on using UART directly
"""

import time
import machine
import sys

# Setup UART (STM32 usually has UART2 on pins A2/A3)
try:
    uart = machine.UART(2, 115200)  # UART2
    uart.init(115200, bits=8, parity=None, stop=1)
    uart_ok = True
    print("UART initialized successfully")
except Exception as e:
    uart_ok = False
    print("UART initialization failed:", e)

def uart_print(msg):
    """Print to both UART and standard output"""
    print(msg)  # Standard output
    if uart_ok:
        uart.write(msg + '\r\n')  # UART output

# Print startup message
uart_print("MicroPython QEMU Demo starting...")
uart_print("Python: " + sys.version)

# Main application loop
for i in range(10):
    uart_print("Counter: {}".format(i))
    
    # Attempt to toggle an LED (may not work in QEMU)
    try:
        led_pin = machine.Pin('A0', machine.Pin.OUT)
        led_pin.value(i % 2)  # Toggle between 0 and 1
        uart_print("LED toggled")
    except Exception as e:
        uart_print("LED control failed: " + str(e))
    
    # Sleep for a moment
    time.sleep(1)

uart_print("Demo complete!")