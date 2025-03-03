#!/usr/bin/env python3
"""
Integration test script for GDB debugging of MicroPython firmware.
Tests basic GDB functionality like connecting, setting breakpoints, and examining memory.
"""

import os
import sys
import time
import signal
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import logging
import fcntl
import select
import json
from datetime import datetime

# Configure logging
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('gdb_test.log')
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    name: str
    expected: str
    actual: str
    passed: bool
    notes: str = ""
    duration: float = 0.0

class TestFailure(Exception):
    """Custom exception for test failures"""
    pass

class QEMUProcess:
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.process: Optional[subprocess.Popen] = None
        self.gdb_port = 1234
        self.log_file = os.path.join(project_dir, "qemu_test.log")
        self.stdout_thread: Optional[threading.Thread] = None
        self.stderr_thread: Optional[threading.Thread] = None
        self.running = False

    def _log_output(self, pipe, log_prefix: str):
        """Log output from QEMU process"""
        while self.running:
            try:
                line = pipe.readline()
                if not line:
                    break
                # Handle both string and bytes output
                if isinstance(line, bytes):
                    line = line.decode('utf-8', errors='replace')
                logger.debug(f"{log_prefix}: {line.strip()}")
            except Exception as e:
                logger.error(f"Error reading QEMU output: {e}")
                break

    def start(self) -> bool:
        """Start QEMU with GDB server enabled"""
        try:
            cmd = [
                "qemu-system-arm",
                "-machine", "netduino2",
                "-cpu", "cortex-m3",
                "-m", "128K",
                "-nographic",
                "-kernel", os.path.join(self.project_dir, "firmware/build/firmware.elf"),
                "-s", "-S",  # Start GDB server and wait for connection
                "-d", "guest_errors,unimp,exec,in_asm",
                "-D", self.log_file,
                "-semihosting-config", "enable=on,target=native",
                "-semihosting"
            ]
            
            logger.info(f"Starting QEMU: {' '.join(cmd)}")
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True
            )

            # Start output logging threads
            self.running = True
            self.stdout_thread = threading.Thread(
                target=self._log_output,
                args=(self.process.stdout, "QEMU-OUT")
            )
            self.stderr_thread = threading.Thread(
                target=self._log_output,
                args=(self.process.stderr, "QEMU-ERR")
            )
            self.stdout_thread.start()
            self.stderr_thread.start()

            logger.info("QEMU process started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start QEMU: {e}")
            return False

    def stop(self):
        """Stop QEMU process"""
        if self.process:
            self.running = False
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            
            # Wait for logging threads
            if self.stdout_thread:
                self.stdout_thread.join()
            if self.stderr_thread:
                self.stderr_thread.join()
            
            self.process = None
            logger.info("QEMU process stopped")

class GDBIntegrationTester:
    def __init__(self):
        self.project_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.firmware_path = self.project_dir / "firmware/build/firmware.elf"
        self.results: List[TestResult] = []
        self.qemu: Optional[QEMUProcess] = None
        self.test_start_time = datetime.now()
        
        # Create test results directory
        self.results_dir = self.project_dir / "test_results" / self.test_start_time.strftime("%Y%m%d_%H%M%S")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure file logging
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration"""
        log_file = self.results_dir / "test_run.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)

    def run_gdb_commands(self, commands: List[str], expected_output: Optional[List[str]] = None, 
                        timeout: int = 30) -> Tuple[bool, str]:
        """Run GDB commands and check output"""
        try:
            # Create a temporary GDB command file
            gdb_script = self.results_dir / "gdb_commands.txt"
            with open(gdb_script, 'w') as f:
                f.write("set pagination off\n")
                f.write("set confirm off\n")
                f.write("set debug remote 1\n")
                f.write(f"file {self.firmware_path}\n")
                f.write("target remote :1234\n")
                for cmd in commands:
                    f.write(f"{cmd}\n")
                f.write("quit\n")

            # Run GDB with the command file
            gdb_cmd = ['arm-none-eabi-gdb', '-x', str(gdb_script)]
            logger.info(f"Running GDB with command: {' '.join(gdb_cmd)}")
            
            gdb_output = subprocess.run(
                gdb_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Log GDB output
            logger.debug(f"GDB stdout:\n{gdb_output.stdout}")
            if gdb_output.stderr:
                logger.debug(f"GDB stderr:\n{gdb_output.stderr}")
            
            # Save GDB output to file
            output_file = self.results_dir / f"gdb_output_{len(self.results)}.txt"
            with open(output_file, 'w') as f:
                f.write(f"Command: {' '.join(gdb_cmd)}\n")
                f.write(f"Stdout:\n{gdb_output.stdout}\n")
                f.write(f"Stderr:\n{gdb_output.stderr}\n")
            
            if expected_output:
                for expected in expected_output:
                    if expected not in gdb_output.stdout:
                        logger.error(f"Expected output not found: {expected}")
                        logger.error(f"Actual output: {gdb_output.stdout}")
                        return False, gdb_output.stdout
            return True, gdb_output.stdout
        except subprocess.TimeoutExpired:
            logger.error(f"GDB command timed out after {timeout} seconds")
            return False, f"Timeout after {timeout}s"
        except Exception as e:
            logger.error(f"Error running GDB commands: {e}")
            return False, str(e)

    def run_test(self, name: str, commands: List[str], expected_output: Optional[List[str]] = None,
                timeout: int = 60) -> TestResult:
        """Run a single test with timing and logging"""
        logger.info(f"\nRunning test: {name}")
        start_time = time.time()
        
        try:
            # Add initialization commands
            init_commands = [
                "set confirm off",
                "set pagination off",
                "set print pretty on",
                "set print array on",
                "set print array-indexes on",
                "set python print-stack full"
            ]
            commands = init_commands + commands
            
            success, output = self.run_gdb_commands(commands, expected_output, timeout)
            duration = time.time() - start_time
            
            result = TestResult(
                name=name,
                expected=str(expected_output),
                actual=output,
                passed=success,
                duration=duration
            )
            
            logger.info(f"Test {name}: {'✅ PASS' if success else '❌ FAIL'} ({duration:.2f}s)")
            if not success:
                logger.error(f"Test failed with output:\n{output}")
            
            self.results.append(result)
            return result
            
        except Exception as e:
            logger.error(f"Test {name} failed with error: {e}")
            duration = time.time() - start_time
            result = TestResult(
                name=name,
                expected=str(expected_output),
                actual=str(e),
                passed=False,
                notes=f"Error: {e}",
                duration=duration
            )
            self.results.append(result)
            return result

    def test_basic_connection(self) -> TestResult:
        """Test basic GDB connection"""
        return self.run_test(
            name="Basic Connection",
            commands=[
                "monitor system_reset",
                "info registers",
                "print/x $pc"
            ],
            expected_output=["r0", "r1", "r2", "pc"]
        )

    def test_breakpoint(self) -> TestResult:
        """Test setting and hitting a breakpoint"""
        return self.run_test(
            name="Breakpoint Test",
            commands=[
                "monitor system_reset",
                "break SystemInit",
                "info break",
                "continue",
                "info registers"
            ],
            expected_output=["Breakpoint 1", "SystemInit"]
        )

    def test_examine_memory(self) -> TestResult:
        """Test examining memory contents"""
        return self.run_test(
            name="Examine Memory",
            commands=[
                "monitor system_reset",
                "break SystemInit",
                "continue",
                "x/4wx $sp",
                "info registers"
            ],
            expected_output=["0x2001", "SystemInit"]  # Match part of stack address
        )

    def test_python_state(self) -> TestResult:
        """Test MicroPython state inspection"""
        return self.run_test(
            name="Python State",
            commands=[
                "monitor system_reset",
                # Set breakpoint at Reset_Handler
                "break Reset_Handler",
                "continue",
                # Show debug info
                "bt",
                "info registers",
                "info break",
                # Try to read some memory
                "x/16wx 0x08000000",  # Flash memory start
                "x/16wx 0x20000000"   # RAM start
            ],
            expected_output=[
                "Reset_Handler",                    # Check if we hit the breakpoint
                "0x2001fff8",                      # Stack pointer value
                "SystemCoreClock",                 # Check if we can see system variables
                "mp_state_ctx"                     # Check if we can see MicroPython state
            ]
        )

    def save_results(self):
        """Save test results to JSON file"""
        results_file = self.results_dir / "test_results.json"
        results_data = {
            "timestamp": self.test_start_time.isoformat(),
            "total_tests": len(self.results),
            "passed_tests": sum(1 for r in self.results if r.passed),
            "total_duration": sum(r.duration for r in self.results),
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "duration": r.duration,
                    "expected": r.expected,
                    "actual": r.actual,
                    "notes": r.notes
                }
                for r in self.results
            ]
        }
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        logger.info(f"\nTest results saved to {results_file}")

    def print_summary(self):
        """Print test results summary"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        total_duration = sum(r.duration for r in self.results)
        
        logger.info("\nTest Summary:")
        logger.info("=============")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed Tests: {passed_tests}")
        logger.info(f"Failed Tests: {total_tests - passed_tests}")
        logger.info(f"Total Duration: {total_duration:.2f}s")
        logger.info("\nDetailed Results:")
        
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            logger.info(f"{result.name}: {status} ({result.duration:.2f}s)")
            if not result.passed:
                logger.info(f"  Expected: {result.expected}")
                logger.info(f"  Actual: {result.actual}")
                if result.notes:
                    logger.info(f"  Notes: {result.notes}")

    def setup_test_environment(self) -> bool:
        """Setup the test environment"""
        logger.info("Setting up test environment...")
        
        # Check firmware file
        if not self.firmware_path.exists():
            logger.error(f"Firmware not found at {self.firmware_path}")
            return False
        
        # Kill any existing QEMU processes
        subprocess.run(['pkill', 'qemu-system-arm'], stderr=subprocess.DEVNULL)
        time.sleep(1)
        
        # Start QEMU
        self.qemu = QEMUProcess(str(self.project_dir))
        if not self.qemu.start():
            return False
        
        # Wait for GDB server to be ready
        time.sleep(2)
        logger.info("Test environment ready")
        return True

    def cleanup(self):
        """Cleanup test environment"""
        logger.info("\nCleaning up test environment...")
        if self.qemu:
            self.qemu.stop()
        subprocess.run(['pkill', 'qemu-system-arm'], stderr=subprocess.DEVNULL)
        logger.info("Cleanup complete")

    def run_all_tests(self) -> bool:
        """Run all GDB integration tests"""
        try:
            if not self.setup_test_environment():
                logger.error("Failed to setup test environment")
                return False

            # Run all tests
            self.test_basic_connection()
            self.test_breakpoint()
            self.test_examine_memory()
            self.test_python_state()

            # Save and print results
            self.save_results()
            self.print_summary()

            # Return overall success
            return all(result.passed for result in self.results)

        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return False
        finally:
            self.cleanup()

def main():
    tester = GDBIntegrationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 