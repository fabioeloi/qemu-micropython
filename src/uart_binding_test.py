"""
Test MicroPython bindings for custom UART driver
"""
import machine
import time
import sys

print("=" * 50)
print("MicroPython UART Bindings Test")
print("=" * 50)

try:
    # Initialize UART
    uart = machine.UART(2, 115200)
    uart.init(115200, bits=8, parity=None, stop=1)
    print("UART initialized successfully")
    
    # Test loopback mode
    print("\nTesting loopback mode...")
    uart.set_loopback(True)
    uart.write("Test message")
    time.sleep(0.1)
    data = uart.read(11)
    print(f"Sent: 'Test message', Received: '{data.decode() if data else 'None'}'")
    
    # Test error simulation
    print("\nTesting error simulation...")
    uart.set_error_simulation(0.5)
    uart.write("Error test")
    time.sleep(0.1)
    data = uart.read(10)
    print(f"With 50% errors - Sent: 'Error test', Received: '{data.decode() if data else 'None'}'")
    
    # Test noise simulation
    print("\nTesting noise simulation...")
    uart.set_error_simulation(0)
    uart.set_noise_simulation(0.1)
    uart.write("Noise test")
    time.sleep(0.1)
    data = uart.read(10)
    print(f"With 10% noise - Sent: 'Noise test', Received: '{data.decode() if data else 'None'}'")
    
    # Test recording
    print("\nTesting recording...")
    uart.set_noise_simulation(0)
    uart.start_recording("/tmp/uart_recording.bin")
    uart.write("Recording test")
    time.sleep(0.1)
    uart.stop_recording()
    print("Recording stopped, check file size:")
    try:
        import os
        size = os.stat("/tmp/uart_recording.bin")[6]
        print(f"Recording file size: {size} bytes")
    except:
        print("Could not check file size")
    
    print("\nAll tests completed")
    
except Exception as e:
    print(f"Error: {e}")
