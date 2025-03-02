"""
MicroPython UART Test

This script tests the custom UART driver features when running in MicroPython.
It demonstrates basic functionality as well as the enhanced features provided
by the custom driver.
"""
import time

# Conditional imports to handle both simulator and real hardware
try:
    import machine
    is_micropython = True
except ImportError:
    # Fallback for testing outside MicroPython
    is_micropython = False
    
    # Create a simulator for testing
    class UARTSimulator:
        def __init__(self, id, baudrate=115200, **kwargs):
            self.id = id
            self.baudrate = baudrate
            self.loopback = False
            self.buffer = bytearray()
            self.rx_buffer = bytearray()
            print(f"UART {id} initialized at {baudrate} baud")
            
        def init(self, baudrate, bits=8, parity=None, stop=1, **kwargs):
            self.baudrate = baudrate
            print(f"UART {self.id} configured: {baudrate} baud, {bits} bits, parity={parity}, stop={stop}")
            
        def write(self, data):
            if isinstance(data, str):
                data = data.encode('utf-8')
            self.buffer.extend(data)
            if self.loopback:
                self.rx_buffer.extend(data)
            return len(data)
            
        def read(self, nbytes=None):
            if not nbytes:
                result = bytes(self.rx_buffer)
                self.rx_buffer = bytearray()
                return result
            else:
                result = bytes(self.rx_buffer[:nbytes])
                self.rx_buffer = self.rx_buffer[nbytes:]
                return result
                
        def readinto(self, buf):
            available = len(self.rx_buffer)
            if not available:
                return 0
            copy_len = min(available, len(buf))
            for i in range(copy_len):
                buf[i] = self.rx_buffer[i]
            self.rx_buffer = self.rx_buffer[copy_len:]
            return copy_len
        
        def any(self):
            return len(self.rx_buffer)
        
        # Custom UART driver enhanced features
        def set_loopback(self, enable):
            self.loopback = enable
            print(f"Loopback mode {'enabled' if enable else 'disabled'}")
        
        def set_error_simulation(self, rate):
            print(f"Error simulation set to {rate*100}%")
        
        def set_noise_simulation(self, level):
            print(f"Noise simulation set to {level*100}%")
        
        def start_recording(self, filename):
            print(f"Recording started to file: {filename}")
        
        def stop_recording(self):
            print("Recording stopped")
        
        def get_errors(self):
            return 0
        
        def set_timing_simulation(self, enable):
            print(f"Timing simulation {'enabled' if enable else 'disabled'}")
        
        def get_status(self):
            return 0x01 if self.loopback else 0x00
            
    # Create a machine module simulator
    class MachineModule:
        def __init__(self):
            self.UART = UARTSimulator
            
    machine = MachineModule()


def test_basic_uart():
    """Test basic UART functionality"""
    print("\n=== Basic UART Test ===")
    
    # Initialize UART
    uart = machine.UART(0, 115200)
    uart.init(115200, bits=8, parity=None, stop=1)
    
    # Test data transmission in non-loopback mode
    print("Sending data without loopback...")
    message = "Hello, UART!"
    uart.write(message)
    
    # In non-loopback mode, nothing should be received
    time.sleep(0.1)
    data = uart.read()
    print(f"Data received without loopback: {data}")
    
    # Enable loopback mode
    if hasattr(uart, 'set_loopback'):
        print("\nEnabling loopback mode...")
        uart.set_loopback(True)
        
        # Send data again
        print("Sending data with loopback...")
        uart.write(message)
        
        # Now we should receive the data back
        time.sleep(0.1)
        data = uart.read()
        if isinstance(data, bytes):
            data = data.decode('utf-8', errors='replace')
        print(f"Data received with loopback: {data}")
        
        # Check if loopback worked
        if data == message:
            print("Loopback test PASSED")
        else:
            print("Loopback test FAILED")
            
        # Disable loopback
        uart.set_loopback(False)
    else:
        print("set_loopback function not available")


def test_error_simulation():
    """Test error simulation"""
    print("\n=== Error Simulation Test ===")
    
    if not hasattr(machine.UART, 'set_error_simulation'):
        print("Error simulation not supported")
        return
    
    uart = machine.UART(0, 115200)
    uart.init(115200, bits=8, parity=None, stop=1)
    uart.set_loopback(True)
    
    # Test without errors
    uart.set_error_simulation(0.0)
    message = "No errors should occur"
    print(f"Sending with 0% error rate: '{message}'")
    uart.write(message)
    time.sleep(0.1)
    received = uart.read()
    if isinstance(received, bytes):
        received = received.decode('utf-8', errors='replace')
    print(f"Received: '{received}'")
    
    # Test with errors
    uart.set_error_simulation(0.5)  # 50% error rate
    message = "This should have errors"
    print(f"Sending with 50% error rate: '{message}'")
    uart.write(message)
    time.sleep(0.1)
    received = uart.read()
    if isinstance(received, bytes):
        received = received.decode('utf-8', errors='replace')
    print(f"Received: '{received}'")
    
    # Disable error simulation
    uart.set_error_simulation(0.0)
    

def test_noise_simulation():
    """Test noise simulation"""
    print("\n=== Noise Simulation Test ===")
    
    if not hasattr(machine.UART, 'set_noise_simulation'):
        print("Noise simulation not supported")
        return
    
    uart = machine.UART(0, 115200)
    uart.init(115200, bits=8, parity=None, stop=1)
    uart.set_loopback(True)
    
    # Test without noise
    uart.set_noise_simulation(0.0)
    message = "No noise should occur"
    print(f"Sending with 0% noise level: '{message}'")
    uart.write(message)
    time.sleep(0.1)
    received = uart.read()
    if isinstance(received, bytes):
        received = received.decode('utf-8', errors='replace')
    print(f"Received: '{received}'")
    
    # Test with noise
    uart.set_noise_simulation(0.2)  # 20% noise level
    message = "This should have noise"
    print(f"Sending with 20% noise level: '{message}'")
    uart.write(message)
    time.sleep(0.1)
    received = uart.read()
    if isinstance(received, bytes):
        received = received.decode('utf-8', errors='replace')
    print(f"Received: '{received}'")
    
    # Disable noise simulation
    uart.set_noise_simulation(0.0)


def test_recording():
    """Test UART recording feature"""
    print("\n=== Recording Test ===")
    
    if not hasattr(machine.UART, 'start_recording'):
        print("Recording not supported")
        return
    
    uart = machine.UART(0, 115200)
    uart.init(115200, bits=8, parity=None, stop=1)
    uart.set_loopback(True)
    
    # Start recording
    uart.start_recording("/tmp/uart_test_recording.bin")
    
    # Send some data
    uart.write("Recording test message 1")
    time.sleep(0.1)
    uart.write("Recording test message 2")
    time.sleep(0.1)
    
    # Stop recording
    uart.stop_recording()
    print("Recording completed")


def run_all_tests():
    """Run all UART tests"""
    print("==== UART DRIVER TEST SUITE ====")
    print(f"Running in {'MicroPython' if is_micropython else 'Simulation'} mode")
    
    # Run all tests
    test_basic_uart()
    test_error_simulation()
    test_noise_simulation()
    test_recording()
    
    print("\n==== ALL TESTS COMPLETED ====")
    

if __name__ == "__main__":
    run_all_tests() 