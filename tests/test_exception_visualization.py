#!/usr/bin/env python3
"""
Test script for MicroPython exception visualization in GDB

This script creates various exception scenarios to test the enhanced
exception visualization features in the GDB integration.
"""

import os
import sys
import time
import subprocess
import tempfile
from typing import List, Dict, Any, Optional

class ExceptionVisualizationTest:
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.qemu_process = None
        self.test_log = []
    
    def setup(self) -> bool:
        """Set up the test environment"""
        try:
            # Create a test script that generates exceptions
            self.create_test_script()
            
            # Build the firmware with the test script
            self.build_firmware()
            
            # Start QEMU with GDB server
            qemu_cmd = [
                os.path.join(self.project_dir, "scripts/debug_micropython.sh"),
                "--no-gdb"  # Start QEMU but don't launch GDB
            ]
            
            self.qemu_process = subprocess.Popen(
                qemu_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give QEMU time to start
            time.sleep(2)
            
            if self.qemu_process.poll() is not None:
                print("Failed to start QEMU")
                return False
            
            return True
        except Exception as e:
            print(f"Setup failed: {e}")
            return False
    
    def create_test_script(self):
        """Create a test script that generates various exceptions"""
        test_script = """
def test_zero_division():
    """Test division by zero exception"""
    print("Testing division by zero...")
    a = 10
    b = 0
    # This will raise ZeroDivisionError
    result = a / b
    return result

def test_index_error():
    """Test index error exception"""
    print("Testing index error...")
    items = [1, 2, 3]
    # This will raise IndexError
    item = items[5]
    return item

def test_attribute_error():
    """Test attribute error exception"""
    print("Testing attribute error...")
    class TestClass:
        def __init__(self):
            self.value = 42
    
    obj = TestClass()
    # This will raise AttributeError
    return obj.nonexistent_attribute

def test_nested_exception():
    """Test nested exception handling"""
    print("Testing nested exception...")
    
    def inner_function():
        items = [1, 2, 3]
        return items[5]  # This will raise IndexError
    
    try:
        inner_function()
    except IndexError:
        # This will raise ZeroDivisionError
        return 1 / 0

def test_custom_exception():
    """Test custom exception handling"""
    print("Testing custom exception...")
    
    class CustomError(Exception):
        def __init__(self, message, code):
            self.message = message
            self.code = code
            super().__init__(f"{message} (code: {code})")
    
    # This will raise CustomError
    raise CustomError("This is a custom error", 42)

def main():
    """Main function"""
    print("Starting exception visualization tests...")
    
    try:
        test_zero_division()
    except ZeroDivisionError as e:
        print(f"Caught ZeroDivisionError: {e}")
    
    try:
        test_index_error()
    except IndexError as e:
        print(f"Caught IndexError: {e}")
    
    try:
        test_attribute_error()
    except AttributeError as e:
        print(f"Caught AttributeError: {e}")
    
    try:
        test_nested_exception()
    except ZeroDivisionError as e:
        print(f"Caught nested ZeroDivisionError: {e}")
    
    try:
        test_custom_exception()
    except Exception as e:
        print(f"Caught CustomError: {e}")
    
    print("All tests completed")
    return 42

if __name__ == "__main__":
    main()
"""
        # Write the test script to the src directory
        with open(os.path.join(self.project_dir, "src/main.py"), "w") as f:
            f.write(test_script)
    
    def build_firmware(self):
        """Build the firmware with the test script"""
        build_cmd = [
            os.path.join(self.project_dir, "scripts/build.sh")
        ]
        
        subprocess.run(
            build_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    
    def run_gdb_commands(self, commands: List[str]) -> List[str]:
        """Run a series of GDB commands and return the output"""
        try:
            # Create a temporary GDB script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.gdb', delete=False) as f:
                for cmd in commands:
                    f.write(cmd + "\n")
                f.write("quit\n")
                script_path = f.name
            
            # Run GDB with the script
            gdb_cmd = [
                "arm-none-eabi-gdb",
                "-x", os.path.join(self.project_dir, "config/gdb/gdbinit"),
                "-x", script_path,
                "--batch",
                os.path.join(self.project_dir, "firmware/build/firmware.elf")
            ]
            
            result = subprocess.run(
                gdb_cmd,
                capture_output=True,
                text=True
            )
            
            # Clean up
            os.unlink(script_path)
            
            return result.stdout.splitlines()
        except Exception as e:
            print(f"GDB command execution failed: {e}")
            return []
    
    def test_basic_visualization(self) -> bool:
        """Test the basic exception visualization"""
        commands = [
            "target remote localhost:1234",
            "mpy-catch ZeroDivisionError all",
            "continue",
            "mpy-except-visualize"
        ]
        
        output = self.run_gdb_commands(commands)
        self.test_log.extend(output)
        
        # Verify the output contains expected visualization elements
        expected_patterns = [
            "EXCEPTION VISUALIZATION",
            "Type: ZeroDivisionError",
            "TRACEBACK"
        ]
        
        return all(any(pattern in line for line in output) for pattern in expected_patterns)
    
    def test_detailed_info(self) -> bool:
        """Test the detailed exception information display"""
        commands = [
            "target remote localhost:1234",
            "mpy-catch AttributeError all",
            "continue",
            "mpy-except-info -d"  # Detailed mode
        ]
        
        output = self.run_gdb_commands(commands)
        self.test_log.extend(output)
        
        # Verify the output contains detailed information
        expected_patterns = [
            "Exception: AttributeError",
            "Traceback (most recent call last):",
            "Local Variables at Exception Point:"
        ]
        
        return all(any(pattern in line for line in output) for pattern in expected_patterns)
    
    def test_exception_history(self) -> bool:
        """Test the exception history feature"""
        # First, trigger multiple exceptions
        commands1 = [
            "target remote localhost:1234",
            "mpy-catch ZeroDivisionError all",
            "continue",
            "mpy-catch IndexError all",
            "continue"
        ]
        
        self.run_gdb_commands(commands1)
        
        # Now check the history
        commands2 = [
            "target remote localhost:1234",
            "mpy-except-history",
            "mpy-except-info -i 0",  # First exception in history
            "mpy-except-info -i 1"   # Second exception in history
        ]
        
        output = self.run_gdb_commands(commands2)
        self.test_log.extend(output)
        
        # Verify we can access exception history
        expected_patterns = [
            "Exception History:",
            "ZeroDivisionError",
            "IndexError"
        ]
        
        return all(any(pattern in line for line in output) for pattern in expected_patterns)
    
    def test_frame_navigation(self) -> bool:
        """Test the exception frame navigation"""
        commands = [
            "target remote localhost:1234",
            "mpy-catch IndexError all",
            "continue",
            "mpy-except-navigate",  # List frames
            "mpy-except-navigate 0"  # Navigate to first frame
        ]
        
        output = self.run_gdb_commands(commands)
        self.test_log.extend(output)
        
        # Verify frame navigation works
        expected_patterns = [
            "Available frames:",
            "Frame 0:"
        ]
        
        return all(any(pattern in line for line in output) for pattern in expected_patterns)
    
    def cleanup(self):
        """Clean up test resources"""
        if self.qemu_process:
            self.qemu_process.terminate()
            try:
                self.qemu_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.qemu_process.kill()
        
        # Restore original main.py if it exists
        if os.path.exists(os.path.join(self.project_dir, "src/main.py.bak")):
            os.rename(
                os.path.join(self.project_dir, "src/main.py.bak"),
                os.path.join(self.project_dir, "src/main.py")
            )
    
    def save_log(self):
        """Save the test log"""
        log_path = os.path.join(self.project_dir, "tests/exception_visualization_test.log")
        with open(log_path, "w") as f:
            f.write("\n".join(self.test_log))
        print(f"Test log saved to {log_path}")

def main():
    # Get project directory
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create test instance
    tester = ExceptionVisualizationTest(project_dir)
    
    try:
        # Setup
        print("Setting up test environment...")
        if not tester.setup():
            print("Setup failed")
            return 1
        
        # Run tests
        print("\nRunning exception visualization tests...")
        
        tests = [
            ("Basic visualization", tester.test_basic_visualization),
            ("Detailed information", tester.test_detailed_info),
            ("Exception history", tester.test_exception_history),
            ("Frame navigation", tester.test_frame_navigation)
        ]
        
        failed = False
        for name, test_func in tests:
            print(f"\nRunning test: {name}")
            try:
                result = test_func()
                status = "PASSED" if result else "FAILED"
                print(f"Test {name}: {status}")
                if not result:
                    failed = True
            except Exception as e:
                print(f"Test {name} failed with error: {e}")
                failed = True
        
        # Save test log
        tester.save_log()
        
        return 1 if failed else 0
    
    finally:
        # Cleanup
        print("\nCleaning up...")
        tester.cleanup()

if __name__ == "__main__":
    sys.exit(main()) 