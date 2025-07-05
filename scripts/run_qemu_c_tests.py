#!/usr/bin/env python3
import subprocess
import sys
import os
import argparse
import re
import time

# Define project paths relative to this script's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
QEMU_EXE_PATH_1 = os.path.join(PROJECT_DIR, "tools", "qemu", "build", "qemu-system-arm")
QEMU_EXE_PATH_2 = os.path.join(PROJECT_DIR, "tools", "qemu", "build", "arm-softmmu", "qemu-system-arm")

DEFAULT_QEMU_TIMEOUT = 30  # seconds

# Regex to parse test results from console output
TEST_LINE_RE = re.compile(r"^TEST\((?P<name>[a-zA-Z0-9_]+)\):(?P<status>PASS|FAIL|IGNORE)(?::(?P<message>.*))?")
SUMMARY_LINE_RE = re.compile(r"^SUMMARY:(?P<total>\d+):(?P<failures>\d+):(?P<ignored>\d+)")

def find_qemu_executable():
    if os.path.exists(QEMU_EXE_PATH_1):
        return QEMU_EXE_PATH_1
    if os.path.exists(QEMU_EXE_PATH_2):
        return QEMU_EXE_PATH_2
    qemu_in_path = subprocess.run(["which", "qemu-system-arm"], capture_output=True, text=True, check=False)
    if qemu_in_path.returncode == 0:
        return qemu_in_path.stdout.strip()
    return None

def run_single_test_firmware(firmware_path, qemu_exe, timeout_seconds):
    if not os.path.exists(firmware_path):
        print(f"Error: Test firmware not found at {firmware_path}")
        return None

    qemu_command = [
        qemu_exe,
        "-machine", "olimex-stm32-h405",
        "-cpu", "cortex-m4",
        "-m", "128K",
        "-kernel", firmware_path,
        "-serial", "stdio",
        "-monitor", "none",
        "-nographic",
        "-d", "guest_errors,unimp",
        "-semihosting-config", "enable=on,target=native,chardev=stdio", # Ensure semihosting output goes to where stdio is for capture if needed
        "-semihosting"
    ]

    print(f"Executing: {' '.join(qemu_command)}")

    passed_tests = []
    failed_tests = []
    ignored_tests = []
    # Initialize summary, ensuring all keys exist
    summary = {"total": 0, "failures": 0, "ignored": 0, "passed": 0, "error": None}

    try:
        process = subprocess.Popen(qemu_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')

        stdout = ""
        stderr = ""
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate() # Get any remaining output
            print(f"Error: QEMU execution timed out after {timeout_seconds} seconds.")
            summary["error"] = "timeout"
            # Fall through to parse whatever output was captured

        if stdout:
            print("\n--- QEMU STDOUT ---")
            print(stdout)
            for line in stdout.splitlines():
                line = line.strip()
                test_match = TEST_LINE_RE.match(line)
                if test_match:
                    name = test_match.group("name")
                    status = test_match.group("status")
                    message = test_match.group("message") if test_match.group("message") else ""
                    if status == "PASS":
                        passed_tests.append({"name": name})
                    elif status == "FAIL":
                        failed_tests.append({"name": name, "message": message})
                    elif status == "IGNORE":
                        ignored_tests.append({"name": name, "message": message})
                    continue

                summary_match = SUMMARY_LINE_RE.match(line)
                if summary_match:
                    summary["total"] = int(summary_match.group("total"))
                    summary["failures"] = int(summary_match.group("failures"))
                    summary["ignored"] = int(summary_match.group("ignored"))
                    break

        if stderr:
            # Filter out common, benign QEMU semihosting exit messages if desired
            # For now, print if it's not just the typical exit message from our qemu_exit.
            # A typical message is "semihosting_syscall: SYS_EXIT_EXTENDED (0x20) reason 0x20026"
            # or "pulled vbarrier"
            is_benign_stderr = "SYS_EXIT_EXTENDED" in stderr and "0x20026" in stderr
            if not is_benign_stderr or len(stderr.strip().splitlines()) > 2: # Show if more than typical exit info
                 print("\n--- QEMU STDERR ---")
                 print(stderr)

        # Consolidate results
        parsed_total = len(passed_tests) + len(failed_tests) + len(ignored_tests)
        if summary["total"] == 0 and parsed_total > 0 : # Summary line missing or malformed
             print("Warning: SUMMARY line not found or zero tests; deriving from parsed TEST lines.")
             summary["total"] = parsed_total
             summary["failures"] = len(failed_tests)
             summary["ignored"] = len(ignored_tests)

        summary["passed"] = len(passed_tests) # Always use parsed count for passed

        # Further sanity checks
        if summary["failures"] != len(failed_tests):
            print(f"Warning: Parsed failure count ({len(failed_tests)}) differs from summary line ({summary['failures']}). Using parsed count.")
            summary["failures"] = len(failed_tests)
        if summary["ignored"] != len(ignored_tests):
            print(f"Warning: Parsed ignore count ({len(ignored_tests)}) differs from summary line ({summary['ignored']}). Using parsed count.")
            summary["ignored"] = len(ignored_tests)
        # Ensure total matches sum, prioritizing parsed details
        expected_total = summary["passed"] + summary["failures"] + summary["ignored"]
        if summary["total"] != expected_total:
            print(f"Warning: Total tests in summary ({summary['total']}) adjusted to match sum of parsed results ({expected_total}).")
            summary["total"] = expected_total

        if process.returncode != 0 and summary["failures"] == 0 and not summary.get("error"):
            print(f"Warning: QEMU exited with code {process.returncode} but tests reported 0 failures.")
            summary["failures"] = 1 # Indicate at least one failure if QEMU itself failed unexpectedly
            if not summary.get("error"): summary["error"] = f"QEMU exit code {process.returncode}"
        elif process.returncode == 0 and summary["failures"] > 0 and not summary.get("error"):
             # This is fine, test runner controls exit code via semihosting, QEMU wrapper is 0.
             # The test runner's exit code (passed to qemu_exit) should ideally be reflected by QEMU.
             # If qemu_exit(1) leads to QEMU process returncode 1, then this is okay.
             # If QEMU always returns 0 unless it crashes, then summary['failures'] is key.
             pass


        return summary

    except FileNotFoundError:
        print(f"Error: QEMU executable '{qemu_exe}' not found.")
        summary["error"] = "qemu_not_found"
        return summary
    except Exception as e:
        print(f"An unexpected error occurred during QEMU execution: {e}")
        summary["error"] = str(e)
        return summary


def main():
    parser = argparse.ArgumentParser(description="Run C unit tests in QEMU for STM32.")
    parser.add_argument("firmware_binary", help="Path to the ARM target test firmware binary (e.g., test_suite.bin)")
    parser.add_argument("--qemu_exe", help="Path to qemu-system-arm executable. Autodetects if not provided.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_QEMU_TIMEOUT, help=f"Timeout for QEMU execution in seconds (default: {DEFAULT_QEMU_TIMEOUT})")

    args = parser.parse_args()

    qemu_to_run = args.qemu_exe if args.qemu_exe else find_qemu_executable()
    if not qemu_to_run:
        print("Error: qemu-system-arm not found. Please specify with --qemu_exe or ensure it's in PATH or project tools.")
        sys.exit(2) # Specific exit code for setup error

    print(f"Using QEMU: {qemu_to_run}")
    print(f"Testing firmware: {args.firmware_binary}")
    print(f"Timeout set to: {args.timeout} seconds")

    results = run_single_test_firmware(args.firmware_binary, qemu_to_run, args.timeout)

    if results:
        print("\n--- Test Execution Summary ---")
        print(f"Total Tests:   {results.get('total', 0)}")
        print(f"Passed:        {results.get('passed', 0)}")
        print(f"Failed:        {results.get('failures', 0)}")
        print(f"Ignored:       {results.get('ignored', 0)}")

        if results.get("error"):
            print(f"Error during execution: {results['error']}")
            sys.exit(1) # Test execution error
        elif results.get('failures', 0) > 0:
            print("Overall Status: FAIL")
            sys.exit(1) # Test failures
        else:
            print("Overall Status: PASS")
            sys.exit(0) # All tests passed
    else:
        # This case should ideally be caught by run_single_test_firmware returning a dict with an error
        print("Critical error: Automated test execution failed to produce any results.")
        sys.exit(2) # Script or setup error

if __name__ == "__main__":
    main()
