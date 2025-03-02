"""
QEMU-MicroPython Custom UART Demo

This script demonstrates the enhanced features of the custom UART driver
when running in the QEMU environment.
"""
import machine
import time
import os

# Print information about the environment
print("=" * 50)
print("Custom UART Driver Demo")
print("=" * 50)

try:
    # Initialize UART with enhanced features
    # On STM32F4, UART2 is typically on pins A2/A3
    uart = machine.UART(2, 115200)
    uart.init(115200, bits=8, parity=None, stop=1)
    print("UART initialized successfully")

    # Demonstrate basic loopback mode
    print("\n[Test 1] Basic Loopback Mode")
    print("--------------------------")
    try:
        # Enable loopback mode (custom method in QEMU environment)
        uart.set_loopback(True)
        print("Loopback mode enabled")
        
        # Send data and read it back immediately
        test_message = "Hello QEMU UART!"
        uart.write(test_message)
        time.sleep(0.1)  # Small delay to ensure data is processed
        
        # Read back the data
        response = uart.read(len(test_message))
        if response:
            print(f"Sent:     {test_message}")
            print(f"Received: {response.decode('utf-8')}")
            print("Loopback test PASSED" if response.decode('utf-8') == test_message else "Loopback test FAILED")
        else:
            print("No data received in loopback mode")
        
        # Disable loopback
        uart.set_loopback(False)
    except Exception as e:
        print(f"Loopback test error: {e}")

    # Demonstrate error simulation
    print("\n[Test 2] Error Simulation")
    print("----------------------")
    try:
        # Enable error simulation (5% error rate)
        uart.set_error_simulation(0.05)
        print("Error simulation enabled (5% error rate)")
        
        # Send a larger message that will likely encounter errors
        test_message = "A" * 100  # Send 100 'A' characters
        uart.write(test_message)
        time.sleep(0.2)
        
        # Check error status
        errors = uart.get_errors()
        print(f"Detected errors: {errors}")
        
        # Disable error simulation
        uart.set_error_simulation(0)
    except Exception as e:
        print(f"Error simulation test error: {e}")

    # Demonstrate data recording
    print("\n[Test 3] Data Recording")
    print("--------------------")
    try:
        # Start recording UART traffic
        uart.start_recording("/tmp/uart_traffic.bin")
        print("Recording started")
        
        # Generate some traffic
        for i in range(5):
            message = f"Test message {i+1}"
            uart.write(message)
            time.sleep(0.1)
        
        # Stop recording
        uart.stop_recording()
        print("Recording stopped")
        
        # Check if the file exists and its size
        try:
            size = os.stat("/tmp/uart_traffic.bin")[6]
            print(f"Recorded {size} bytes of UART traffic")
        except:
            print("Could not verify recording file")
    except Exception as e:
        print(f"Recording test error: {e}")

    print("\n[Test 4] Noise Simulation")
    print("----------------------")
    try:
        # Enable both loopback and noise simulation
        uart.set_loopback(True)
        uart.set_noise_simulation(0.1)
        print("Noise simulation enabled (10% noise level)")
        
        # Send a message that will be affected by noise
        test_message = "This message will be corrupted by noise"
        uart.write(test_message)
        time.sleep(0.1)
        
        # Read back the noisy data
        response = uart.read(len(test_message))
        if response:
            print(f"Original: {test_message}")
            print(f"Received: {response.decode('utf-8', errors='replace')}")
            
            # Count character differences
            differences = sum(1 for a, b in zip(test_message, response.decode('utf-8', errors='replace')) if a != b)
            print(f"Characters corrupted by noise: {differences}")
        else:
            print("No data received")
        
        # Disable noise simulation and loopback
        uart.set_noise_simulation(0)
        uart.set_loopback(False)
    except Exception as e:
        print(f"Noise simulation test error: {e}")

except Exception as e:
    print(f"Error: {e}")

print("\nDemo completed") 