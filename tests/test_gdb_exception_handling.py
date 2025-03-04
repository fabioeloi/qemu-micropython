#!/usr/bin/env python3
"""
Test script for verifying GDB exception handling integration.
This script automates the testing of the enhanced exception handling features.
"""

import os
import sys
import time
import subprocess
import tempfile
from typing import List, Dict, Any, Optional

class GDBTest:
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.qemu_process = None
        self.gdb_process = None
        self.test_log = []
    
    def setup(self) -> bool:
        """Set up the test environment"""
        try:
            # Start QEMU with GDB server
            qemu_cmd = [
                os.path.join(self.project_dir, "tools/qemu/build/qemu-system-arm"),
                "-machine", "olimex-stm32-h405",
                "-cpu", "cortex-m4",
                "-m", "128K",
                "-kernel", os.path.join(self.project_dir, "firmware/build/firmware.elf"),
                "-S",
                "-gdb", "tcp::1234",
                "-nographic"
            ]
            
            self.qemu_process = subprocess.Popen(
                qemu_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give QEMU time to start
            time.sleep(1)
            
            if self.qemu_process.poll() is not None:
                print("Failed to start QEMU")
                return False
            
            return True
        except Exception as e:
            print(f"Setup failed: {e}")
            return False
    
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
    
    def test_exception_catching(self) -> bool:
        """Test the mpy-catch command"""
        commands = [
            "target remote localhost:1234",
            "mpy-catch ZeroDivisionError",
            "continue",
            "mpy-except-info",
            "mpy-except-bt",
            "mpy-except-vars"
        ]
        
        output = self.run_gdb_commands(commands)
        self.test_log.extend(output)
        
        # Verify the output contains expected information
        expected_patterns = [
            "Will break on uncaught ZeroDivisionError exceptions",
            "Exception Type: ZeroDivisionError",
            "Local variables at exception point"
        ]
        
        return all(any(pattern in line for line in output) for pattern in expected_patterns)
    
    def test_nested_exceptions(self) -> bool:
        """Test handling of nested exceptions"""
        commands = [
            "target remote localhost:1234",
            "mpy-catch ValueError all",
            "continue",
            "mpy-except-info",
            "mpy-except-bt"
        ]
        
        output = self.run_gdb_commands(commands)
        self.test_log.extend(output)
        
        expected_patterns = [
            "Will break on all ValueError exceptions",
            "Exception Type: ValueError",
            "Traceback"
        ]
        
        return all(any(pattern in line for line in output) for pattern in expected_patterns)
    
    def test_exception_state(self) -> bool:
        """Test exception state inspection"""
        commands = [
            "target remote localhost:1234",
            "break test_exception_with_locals",
            "continue",
            "mpy-except-vars",
            "print x",
            "print y",
            "print items"
        ]
        
        output = self.run_gdb_commands(commands)
        self.test_log.extend(output)
        
        expected_patterns = [
            "x = 100",
            "y = \"test\"",
            "items = [1, 2, 3]"
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
    
    def save_log(self):
        """Save the test log"""
        log_path = os.path.join(self.project_dir, "tests/exception_test.log")
        with open(log_path, "w") as f:
            f.write("\n".join(self.test_log))
        print(f"Test log saved to {log_path}")

def main():
    # Get project directory
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create test instance
    tester = GDBTest(project_dir)
    
    try:
        # Setup
        print("Setting up test environment...")
        if not tester.setup():
            print("Setup failed")
            return 1
        
        # Run tests
        print("\nRunning exception handling tests...")
        
        tests = [
            ("Exception catching", tester.test_exception_catching),
            ("Nested exceptions", tester.test_nested_exceptions),
            ("Exception state", tester.test_exception_state)
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