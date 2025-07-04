# tests/semihosting/test_console_pipe.py
#
# How to Run This Test:
# 1. Ensure `usemihosting` module (with console I/O functions) is compiled into your MicroPython firmware.
# 2. Start QEMU with semihosting enabled and its serial console redirected to a TCP port.
#    Example QEMU command:
#    qemu-system-arm -M ... -kernel ... -serial tcp::4444,server,nowait -semihosting ...
#    (Replace "..." with your specific QEMU machine, kernel, and semihosting options)
#    The port `4444` is an example; choose any available port.
#
# 3. On your host machine, run the `tools/semihosting_console_pipe.py` script,
#    connecting it to the TCP port QEMU is using for its serial output.
#    Example host command:
#    python tools/semihosting_console_pipe.py --qemu-port 4444
#    (Ensure the port matches QEMU's serial port)
#
# 4. Upload this test script (`test_console_pipe.py`) to your MicroPython environment in QEMU
#    (e.g., using mpremote or by including it in the firmware).
#
# 5. Run this script from the MicroPython REPL:
#    >>> import test_console_pipe
#    >>> test_console_pipe.run_all_console_pipe_tests()

try:
    import usemihosting
except ImportError:
    print("SKIP: usemihosting module not available.")
    # In a real test runner, this might raise a specific skip exception.
    raise SystemExit("usemihosting module not found, skipping tests.")

import time # For delays if needed

# --- Helper Function ---
def run_test(test_func):
    test_name = str(test_func).split(' ')[1] # Extract function name
    print(f"\n--- Running Test: {test_name} ---")
    try:
        test_func()
        print(f"--- Test {test_name}: PASS ---")
        return True
    except Exception as e:
        print(f"--- Test {test_name}: FAIL ---")
        print(f"    Exception: {type(e).__name__}: {e}")
        # import sys
        # sys.print_exception(e) # Not available in all minimal MicroPython ports
        return False

# --- Test Cases ---

def test_basic_echo():
    print("Testing basic echo with a simple string...")
    test_string = b"Hello via Semihosting Console"

    print(f"Sending: {test_string!r}")
    usemihosting.framed_console_send(test_string)

    print("Receiving...")
    received_data = usemihosting.framed_console_recv()
    print(f"Received: {received_data!r}")

    assert received_data == test_string, f"Basic echo failed. Expected {test_string!r}, got {received_data!r}"
    print("Basic echo data matches.")

def test_empty_payload():
    print("Testing echo with an empty payload...")
    test_payload = b""

    print(f"Sending empty payload: {test_payload!r}")
    usemihosting.framed_console_send(test_payload)

    print("Receiving...")
    received_data = usemihosting.framed_console_recv()
    print(f"Received: {received_data!r}")

    assert received_data == test_payload, f"Empty payload echo failed. Expected {test_payload!r}, got {received_data!r}"
    print("Empty payload echo data matches.")

def test_larger_payload():
    print("Testing echo with a larger payload (approx 280 bytes)...")
    # Create a patterned payload
    pattern = b"FrameTest1234567890!@#$%^&*()" # 28 bytes
    test_payload = pattern * 10 # 280 bytes

    print(f"Sending {len(test_payload)} bytes...")
    # print(f"Payload preview (first 30 bytes): {test_payload[:30]!r}")
    usemihosting.framed_console_send(test_payload)

    print("Receiving...")
    received_data = usemihosting.framed_console_recv()
    # print(f"Received {len(received_data)} bytes. Preview (first 30 bytes): {received_data[:30]!r}")

    assert len(received_data) == len(test_payload), \
        f"Larger payload length mismatch. Expected {len(test_payload)}, got {len(received_data)}"
    assert received_data == test_payload, \
        f"Larger payload data mismatch."
    print(f"Larger payload ({len(received_data)} bytes) echo data matches.")

def test_multiple_consecutive_sends():
    print("Testing multiple consecutive sends and receives...")
    messages = [
        b"Message One",
        b"MsgTwo",
        b"Third times the charm",
        b"", # Empty message in sequence
        b"Last Message in Sequence"
    ]

    received_messages = []

    for i, msg_to_send in enumerate(messages):
        print(f"Sending message {i+1}/{len(messages)}: {msg_to_send!r}")
        usemihosting.framed_console_send(msg_to_send)

        # Optional: small delay if timing issues are suspected, though pipe should handle it.
        # time.sleep_ms(50)

        print(f"Receiving message {i+1}/{len(messages)}...")
        received_msg = usemihosting.framed_console_recv()
        print(f"Received: {received_msg!r}")

        assert received_msg == msg_to_send, \
            f"Consecutive send/recv mismatch for message {i+1}. Expected {msg_to_send!r}, got {received_msg!r}"
        received_messages.append(received_msg)

    assert len(received_messages) == len(messages), "Not all messages were received in sequence."
    print("All consecutive messages sent and received successfully and match.")

# --- Main Test Runner ---
def run_all_console_pipe_tests():
    print("======================================================")
    print("=== Running usemihosting Console Pipe I/O Tests ===")
    print("======================================================")
    print("Ensure QEMU is running with '-serial tcp::PORT,server,nowait'")
    print("and 'tools/semihosting_console_pipe.py --qemu-port PORT' is running on the host.")
    print("------------------------------------------------------")

    # Check if semihosting is generally available first
    if not usemihosting.is_semihosting_available():
        print("CRITICAL: usemihosting.is_semihosting_available() returned False.")
        print("Cannot proceed with console pipe tests.")
        print("======================================================")
        return False

    tests_passed = 0
    tests_failed = 0

    test_suite = [
        test_basic_echo,
        test_empty_payload,
        test_larger_payload,
        test_multiple_consecutive_sends,
    ]

    for test_case in test_suite:
        if run_test(test_case):
            tests_passed += 1
        else:
            tests_failed += 1

    print("\n--- Console Pipe Test Suite Summary ---")
    print(f"Total tests run: {len(test_suite)}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    print("========================================")

    if tests_failed > 0:
        print("\nSOME CONSOLE PIPE TESTS FAILED.")
        return False
    return True

if __name__ == "__main__":
    # This allows running the test suite directly if the file is executed
    # (e.g., `mpremote run test_console_pipe.py` if supported by the port)
    # or by importing and calling run_all_console_pipe_tests() from REPL.
    run_all_console_pipe_tests()
```
